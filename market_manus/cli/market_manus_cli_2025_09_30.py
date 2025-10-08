#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Manus - CLI Integrado COMPLETO
-------------------------------------
- Mantém o fluxo completo de menus (1..9) como você já tinha.
- Usa dados REAIS da Bybit quando credenciais válidas estão no .env.
- Não depende de injeção do main.py (construtor sem kwargs).
- Integra Strategy Lab + Confluence Lab com o provider real.
"""

from __future__ import annotations
import os
import sys
import json
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# ------------------------------------------------------------------------------
# .env
# ------------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ------------------------------------------------------------------------------
# Imports do projeto
# ------------------------------------------------------------------------------
# Provider real
try:
    from market_manus.data_providers.bybit_real_data_provider_fixed import BybitRealDataProvider
except Exception:
    BybitRealDataProvider = None

# Strategy Manager integrado
try:
    from market_manus.strategies.strategy_manager_integrated import StrategyManagerIntegrated
except Exception:
    StrategyManagerIntegrated = None

# Confluence
try:
    from market_manus.confluence_mode.confluence_mode_module import ConfluenceModeModule
except Exception:
    ConfluenceModeModule = None

# Strategy Lab
try:
    from market_manus.strategy_lab.strategy_lab_professional import StrategyLabProfessional
except Exception:
    StrategyLabProfessional = None

# Capital Manager (persistência/sumário)
try:
    from market_manus.core.capital_manager import CapitalManager
except Exception:
    CapitalManager = None

# ------------------------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------------------------
ASSET_PRESETS = [
    ("BTCUSDT", "Bitcoin"),
    ("ETHUSDT", "Ethereum"),
    ("BNBUSDT", "Binance Coin"),
    ("SOLUSDT", "Solana"),
    ("XRPUSDT", "XRP"),
    ("ADAUSDT", "Cardano"),
    ("DOTUSDT", "Polkadot"),
    ("AVAXUSDT", "Avalanche"),
    ("LTCUSDT", "Litecoin"),
    ("MATICUSDT", "Polygon"),
]

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

def fmt_money(v: float) -> str:
    try:
        return f"${v:,.2f}"
    except Exception:
        return str(v)

def _safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return "0"

def _print_error(e: Exception):
    print("❌ Erro:", e)
    tb = traceback.format_exc()
    print(tb)

# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
class MarketManusCompleteCLI:
    """
    CLI principal. Construtor sem kwargs (main.py cria sem injeção).
    Auto-inicializa Provider/Managers usando .env e arquivos do projeto.
    """

    def __init__(self):
        self.version = "3.2.0 - INTEGRAÇÃO COMPLETA (REAL DATA)"
        self.started_at = datetime.now()

        # Estado/Contexto
        self.real_mode: bool = False
        self.data_provider = None
        self.strategy_manager = None
        self.confluence = None
        self.strategy_lab = None
        self.capital_manager = None

        self.selected_asset: Optional[str] = None
        self.selected_timeframe: Optional[str] = None

        # Capital “visão rápida” (fallback visual)
        self.capital = 10_000.00
        self.pnl = 0.0
        self.trades = 0
        self.win_rate = 0.0

        # Boot na ordem que respeita dependências
        self._boot_capital_manager()
        self._boot_data_provider()
        self._boot_strategy_manager()
        self._boot_confluence()
        self._boot_strategy_lab()

    # --------------------------------------------------------------------------
    # BOOT / DEPENDÊNCIAS
    # --------------------------------------------------------------------------
    def _boot_capital_manager(self):
        try:
            if CapitalManager:
                # Se seu CapitalManager aceitar parâmetros, injete aqui.
                self.capital_manager = CapitalManager()
        except Exception as e:
            print(f"⚠️ CapitalManager indisponível: {e}")
            self.capital_manager = None

    def _boot_data_provider(self):
        try:
            if BybitRealDataProvider is None:
                print("⚠️ BybitRealDataProvider não disponível — modo simulado.")
                self.real_mode = False
                return

            api_key = os.getenv("BYBIT_API_KEY")
            api_secret = os.getenv("BYBIT_API_SECRET")
            testnet_env = os.getenv("BYBIT_TESTNET", "true").strip().lower()
            testnet = testnet_env not in ("false", "0", "no", "off")

            self.data_provider = BybitRealDataProvider(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet
            )

            print("[DEBUG] Inicializando Bybit Data Provider")
            print(f"[DEBUG] Testnet: {testnet}")
            if hasattr(self.data_provider, "base_url"):
                print(f"[DEBUG] Base URL: {self.data_provider.base_url}")
            if api_key:
                print(f"[DEBUG] API Key: {api_key[:10]}...")

            print("🔌 Testando conexão com Bybit API...")
            ok = False
            if hasattr(self.data_provider, "test_connection"):
                ok = self.data_provider.test_connection()
            elif hasattr(self.data_provider, "get_current_price"):
                ok = self.data_provider.get_current_price("BTCUSDT") is not None

            self.real_mode = bool(ok)
            if self.real_mode:
                print("✅ Conexão com Bybit API estabelecida")
            else:
                print("⚠️ Sem conexão real — modo simulado")

        except Exception as e:
            print(f"⚠️ Falha ao iniciar Provider real: {e}")
            self.data_provider = None
            self.real_mode = False

    def _boot_strategy_manager(self):
        try:
            if StrategyManagerIntegrated:
                try:
                    self.strategy_manager = StrategyManagerIntegrated(
                        data_provider=self.data_provider,
                        capital_manager=self.capital_manager
                    )
                except TypeError:
                    # compat
                    self.strategy_manager = StrategyManagerIntegrated()
            else:
                self.strategy_manager = None
        except Exception as e:
            print(f"⚠️ StrategyManager indisponível: {e}")
            self.strategy_manager = None

    def _boot_confluence(self):
        try:
            if ConfluenceModeModule:
                try:
                    self.confluence = ConfluenceModeModule(
                        data_provider=self.data_provider,
                        capital_manager=self.capital_manager,
                        strategy_manager=self.strategy_manager
                    )
                except TypeError:
                    # compat
                    self.confluence = ConfluenceModeModule()
            else:
                self.confluence = None
        except Exception as e:
            print(f"⚠️ Confluence indisponível: {e}")
            self.confluence = None

    def _boot_strategy_lab(self):
        try:
            if StrategyLabProfessional:
                try:
                    self.strategy_lab = StrategyLabProfessional(
                        data_provider=self.data_provider,
                        capital_manager=self.capital_manager,
                        strategy_manager=self.strategy_manager
                    )
                except TypeError:
                    self.strategy_lab = StrategyLabProfessional()
            else:
                self.strategy_lab = None
        except Exception as e:
            print(f"⚠️ StrategyLab indisponível: {e}")
            self.strategy_lab = None

    # --------------------------------------------------------------------------
    # UI / Banner
    # --------------------------------------------------------------------------
    def _print_header(self):
        print("\n" + "=" * 80)
        print("🚀 MARKET MANUS - SISTEMA DE TRADING PROFISSIONAL")
        print("=" * 80)
        print(f"📦 Versão: {self.version}")
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
        print("🟢 Dados REAIS da Bybit ✓" if self.real_mode else "⚠️ Modo simulado - configure credenciais para dados reais")
        print("✅ Capital management com persistência")
        print("✅ Sistema de confluência avançado")
        print("=" * 80)

    def _print_quick_dashboard(self):
        print("\n💰 DASHBOARD RÁPIDO")
        print("----------------------------------------")
        capital = self._get_capital_amount()
        print(f"💵 Capital: {fmt_money(capital)}")
        sign = "+" if self.pnl >= 0 else "-"
        print(f"🟢 P&L: {sign}{fmt_money(abs(self.pnl))} (+0.00%)")
        print(f"📊 Trades: {self.trades} | Win Rate: {self.win_rate:.1f}%")

    def _menu(self):
        print("\n🎯 MENU PRINCIPAL")
        print("==============================")
        print("   1️⃣  Capital Dashboard (Visão detalhada do capital)")
        print("   2️⃣  Strategy Lab Professional (Análise individual)")
        print("   3️⃣  Confluence Lab (Combinar múltiplas estratégias)")
        print("   4️⃣  Simulate Trades (Simular operações)")
        print("   5️⃣  Export Reports (Exportar relatórios)")
        print("   6️⃣  Connectivity Status (Testar API)")
        print("   7️⃣  Strategy Explorer (Explorar estratégias)")
        print("   8️⃣  Performance Analysis (Análise de performance)")
        print("   9️⃣  Advanced Settings (Configurações avançadas)")
        print("   0️⃣  Sair")

    # --------------------------------------------------------------------------
    # Capital / Helpers
    # --------------------------------------------------------------------------
    def _get_capital_amount(self) -> float:
        try:
            if self.capital_manager and hasattr(self.capital_manager, "get_total_capital"):
                return float(self.capital_manager.get_total_capital())
        except Exception:
            pass
        return float(self.capital)

    # --------------------------------------------------------------------------
    # Menus (1..9)
    # --------------------------------------------------------------------------
    def _handle_capital_dashboard(self):
        print("\n💰 CAPITAL DASHBOARD")
        print("=" * 40)
        if self.capital_manager and hasattr(self.capital_manager, "get_summary"):
            try:
                summary = self.capital_manager.get_summary()
                for k, v in summary.items():
                    print(f"{k}: {v}")
            except Exception as e:
                _print_error(e)
        else:
            print(f"Capital atual: {fmt_money(self._get_capital_amount())}")
            print("P&L: +0.00% (demo)")
        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _prompt_asset_timeframe(self):
        if not self.selected_asset:
            print("\n📊 ASSET SELECTION - SELEÇÃO DE CRIPTOATIVO")
            print("=" * 60)
            for i, (sym, name) in enumerate(ASSET_PRESETS, 1):
                print(f"{i:>2}  {sym:<8} {name}")
            choice = _safe_input("\nEscolha o número do ativo: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(ASSET_PRESETS):
                    self.selected_asset = ASSET_PRESETS[idx][0]
            except Exception:
                pass

        if not self.selected_timeframe:
            print("\n⏰ TIMEFRAMES DISPONÍVEIS:")
            for i, tf in enumerate(TIMEFRAMES, 1):
                print(f"{i}. {tf}")
            choice = _safe_input("\nEscolha o timeframe (número): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(TIMEFRAMES):
                    self.selected_timeframe = TIMEFRAMES[idx]
            except Exception:
                pass

    def _handle_strategy_lab(self):
        print("\n🔬 STRATEGY LAB PROFESSIONAL")
        print("=" * 60)
        self._prompt_asset_timeframe()
        if not self.selected_asset or not self.selected_timeframe:
            print("❌ Selecione ativo/timeframe primeiro.")
            _ = _safe_input("\nENTER...")
            return

        if not self.strategy_lab:
            print("❌ StrategyLab não disponível no ambiente.")
            _ = _safe_input("\nENTER...")
            return

        # Período
        print("\n📅 PERÍODOS:")
        print("1. Últimas 24 horas")
        print("2. Últimos 7 dias")
        print("3. Últimos 30 dias")
        print("4. Últimos 90 dias")
        choice = _safe_input("\nEscolha: ").strip()
        now = datetime.utcnow()
        lookups = {"1": 1, "2": 7, "3": 30, "4": 90}
        days = lookups.get(choice, 1)
        start = now - timedelta(days=days)
        end = now

        # Executa o backtest via Strategy Lab (tentando métodos conhecidos)
        try:
            result = None
            if hasattr(self.strategy_lab, "backtest_asset"):
                # assinatura: backtest_asset(symbol, timeframe, start, end)
                result = self.strategy_lab.backtest_asset(self.selected_asset, self.selected_timeframe, start, end)
            elif hasattr(self.strategy_lab, "run_historical_test"):
                result = self.strategy_lab.run_historical_test(
                    asset=self.selected_asset, timeframe=self.selected_timeframe,
                    start=start, end=end
                )
            elif hasattr(self.strategy_lab, "run"):
                result = self.strategy_lab.run()  # fallback
            else:
                # fallback mínimo: consultar klines do provider
                kl = self._fetch_klines(self.selected_asset, self.selected_timeframe, start, end)
                result = {
                    "candles": len(kl) if kl else 0,
                    "note": "StrategyLab não expôs APIs conhecidas; exibindo só dados."
                }

            print("\n📊 RESULTADOS DO STRATEGY LAB")
            print("=" * 60)
            if isinstance(result, dict):
                for k, v in result.items():
                    print(f"{k}: {v}")
            else:
                print(result)
        except Exception as e:
            _print_error(e)

        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _fetch_klines(self, symbol: str, timeframe: str, start: datetime, end: datetime):
        if not self.data_provider:
            return None
        try:
            if hasattr(self.data_provider, "get_klines"):
                return self.data_provider.get_klines(symbol, timeframe, start, end, limit=1000)
        except Exception as e:
            _print_error(e)
        return None

    def _handle_confluence_lab(self):
        print("\n🔬 CONFLUENCE LAB - SISTEMA DE CONFLUÊNCIA")
        print("=" * 60)
        self._prompt_asset_timeframe()
        if not self.selected_asset or not self.selected_timeframe:
            print("❌ Selecione ativo/timeframe primeiro.")
            _ = _safe_input("\nENTER...")
            return

        if not self.confluence:
            print("❌ Confluence não disponível no ambiente.")
            _ = _safe_input("\nENTER...")
            return

        # Modo
        print("\n🎯 MODO DE CONFLUÊNCIA")
        print("1. ALL")
        print("2. ANY")
        print("3. MAJORITY")
        print("4. WEIGHTED")
        mode_map = {"1": "ALL", "2": "ANY", "3": "MAJORITY", "4": "WEIGHTED"}
        mode_choice = _safe_input("\nEscolha o modo: ").strip()
        mode = mode_map.get(mode_choice, "MAJORITY")

        # Período
        print("\n📅 PERÍODOS:")
        print("1. Últimas 24 horas")
        print("2. Últimos 7 dias")
        print("3. Últimos 30 dias")
        print("4. Últimos 90 dias")
        choice = _safe_input("\nEscolha: ").strip()
        now = datetime.utcnow()
        days = {"1": 1, "2": 7, "3": 30, "4": 90}.get(choice, 1)
        start = now - timedelta(days=days)
        end = now

        # Execução (tentando APIs conhecidas do Confluence)
        try:
            result = None
            if hasattr(self.confluence, "historical_test"):
                result = self.confluence.historical_test(
                    asset=self.selected_asset, timeframe=self.selected_timeframe,
                    mode=mode, start=start, end=end
                )
            elif hasattr(self.confluence, "run_historical_backtest"):
                result = self.confluence.run_historical_backtest(
                    asset=self.selected_asset, timeframe=self.selected_timeframe,
                    mode=mode, start=start, end=end
                )
            elif hasattr(self.confluence, "run"):
                result = self.confluence.run()
            else:
                # fallback: apenas pega candles
                kl = self._fetch_klines(self.selected_asset, self.selected_timeframe, start, end)
                result = {
                    "candles": len(kl) if kl else 0,
                    "note": "Confluence não expôs APIs conhecidas; exibindo só dados."
                }

            print("\n📊 RESULTADOS DO CONFLUENCE LAB")
            print("=" * 60)
            if isinstance(result, dict):
                for k, v in result.items():
                    print(f"{k}: {v}")
            else:
                print(result)
        except Exception as e:
            _print_error(e)

        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _handle_simulate_trades(self):
        print("\n🧪 SIMULAÇÃO DE TRADES (DEMO)")
        print("=" * 60)
        self._prompt_asset_timeframe()
        if not self.selected_asset or not self.selected_timeframe:
            print("❌ Selecione ativo/timeframe primeiro.")
            _ = _safe_input("\nENTER...")
            return

        # Exemplo mínimo: pega último preço e simula buy&hold curto
        try:
            price = None
            if self.data_provider and hasattr(self.data_provider, "get_current_price"):
                price = self.data_provider.get_current_price(self.selected_asset)
            print(f"Preço atual ({self.selected_asset}): {price}")
            print("→ (DEMO) Entraria comprado e sairia quando +0.2%")
        except Exception as e:
            _print_error(e)

        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _handle_export_reports(self):
        print("\n🧾 EXPORT REPORTS")
        print("=" * 60)
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "asset": self.selected_asset,
            "timeframe": self.selected_timeframe,
            "real_mode": self.real_mode,
        }
        out = reports_dir / f"export_{int(time.time())}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Exportado: {out}")
        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _handle_connectivity(self):
        print("\n🔌 CONNECTIVITY STATUS")
        print("=" * 60)
        if not self.data_provider:
            print("❌ Data Provider não inicializado")
            _ = _safe_input("\nENTER...")
            return
        try:
            ok = False
            if hasattr(self.data_provider, "test_connection"):
                ok = self.data_provider.test_connection()
            elif hasattr(self.data_provider, "get_current_price"):
                ok = self.data_provider.get_current_price("BTCUSDT") is not None
            self.real_mode = bool(ok)
            if self.real_mode:
                print("✅ Conectado à Bybit API (modo REAL)")
                price = self.data_provider.get_current_price("ETHUSDT") or self.data_provider.get_current_price("BTCUSDT")
                if price is not None:
                    print(f"   • Preço exemplo: {price}")
            else:
                print("⚠️ Sem conexão real — operando em modo simulado")
        except Exception as e:
            _print_error(e)
        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _handle_strategy_explorer(self):
        print("\n🧭 STRATEGY EXPLORER")
        print("=" * 60)
        if not self.strategy_manager:
            print("❌ Strategy Manager não disponível")
            _ = _safe_input("\nENTER...")
            return
        try:
            if hasattr(self.strategy_manager, "get_available_strategies"):
                strategies = self.strategy_manager.get_available_strategies()
                if not strategies:
                    print("⚠️ Nenhuma estratégia registrada.")
                else:
                    for i, st in enumerate(strategies, 1):
                        print(f"{i}. {st}")
            else:
                print("⚠️ Strategy Manager não expõe get_available_strategies()")
        except Exception as e:
            _print_error(e)
        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _handle_performance_analysis(self):
        print("\n📈 PERFORMANCE ANALYSIS (DEMO)")
        print("=" * 60)
        # Caso seu Performance Agent exista, você pode integrá-lo aqui.
        print("→ Integração com performance_agent pode ser plugada aqui.")
        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    def _handle_advanced_settings(self):
        print("\n⚙️ ADVANCED SETTINGS")
        print("=" * 60)
        print("1) Selecionar Ativo")
        print("2) Selecionar Timeframe")
        print("3) Definir Capital Inicial")
        print("0) Voltar")
        choice = _safe_input("\nEscolha: ").strip()
        if choice == "1":
            self.selected_asset = None  # força seleção
            self._prompt_asset_timeframe()
        elif choice == "2":
            self.selected_timeframe = None
            self._prompt_asset_timeframe()
        elif choice == "3":
            val = _safe_input("Novo capital inicial (apenas número): ").strip()
            try:
                f = float(val)
                self.capital = f
                if self.capital_manager and hasattr(self.capital_manager, "set_total_capital"):
                    self.capital_manager.set_total_capital(f)
                print(f"✅ Capital atualizado para {fmt_money(f)}")
            except Exception:
                print("❌ Valor inválido.")

        _ = _safe_input("\n📖 Pressione ENTER para continuar...")

    # --------------------------------------------------------------------------
    # Loop principal
    # --------------------------------------------------------------------------
    def run(self):
        print("🚀 Inicializando Market Manus CLI Integrado...")
        print("✅ Market Manus CLI Integrado inicializado com sucesso!\n")

        while True:
            self._print_header()
            self._print_quick_dashboard()
            self._menu()

            choice = _safe_input("\n🔢 Escolha uma opção: ").strip()

            if choice == "0":
                print("\n👋 Encerrando Market Manus...")
                break
            elif choice == "1":
                self._handle_capital_dashboard()
            elif choice == "2":
                self._handle_strategy_lab()
            elif choice == "3":
                self._handle_confluence_lab()
            elif choice == "4":
                self._handle_simulate_trades()
            elif choice == "5":
                self._handle_export_reports()
            elif choice == "6":
                self._handle_connectivity()
            elif choice == "7":
                self._handle_strategy_explorer()
            elif choice == "8":
                self._handle_performance_analysis()
            elif choice == "9":
                self._handle_advanced_settings()
            else:
                print("❌ Opção inválida!")
                time.sleep(0.8)
