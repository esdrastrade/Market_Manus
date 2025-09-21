#!/usr/bin/env python3
"""
Strategy Lab - Assets Selection Module
Módulo para seleção e configuração de ativos para o Strategy Lab
"""

import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class AssetManager:
    """Gerenciador de ativos para o Strategy Lab"""
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.base_url = "https://api-demo.bybit.com" if testnet else "https://api.bybit.com"
        
        # Lista padrão de 10 criptoativos com alta liquidez
        self.default_assets = [
            {"symbol": "BTCUSDT", "name": "Bitcoin", "emoji": "🪙", "min_notional": 5.0},
            {"symbol": "ETHUSDT", "name": "Ethereum", "emoji": "💎", "min_notional": 5.0},
            {"symbol": "BNBUSDT", "name": "Binance Coin", "emoji": "🟡", "min_notional": 1.0},
            {"symbol": "SOLUSDT", "name": "Solana", "emoji": "⚡", "min_notional": 1.0},
            {"symbol": "XRPUSDT", "name": "XRP", "emoji": "💧", "min_notional": 1.0},
            {"symbol": "ADAUSDT", "name": "Cardano", "emoji": "🔵", "min_notional": 1.0},
            {"symbol": "DOTUSDT", "name": "Polkadot", "emoji": "🔴", "min_notional": 1.0},
            {"symbol": "AVAXUSDT", "name": "Avalanche", "emoji": "🔺", "min_notional": 1.0},
            {"symbol": "LTCUSDT", "name": "Litecoin", "emoji": "🥈", "min_notional": 1.0},
            {"symbol": "MATICUSDT", "name": "Polygon", "emoji": "🟣", "min_notional": 1.0}
        ]
        
        self.selected_assets = []
        self.asset_prices = {}
        
    def get_asset_price(self, symbol: str) -> Optional[Dict]:
        """Obter preço atual de um ativo"""
        try:
            response = requests.get(
                f"{self.base_url}/v5/market/tickers",
                params={'category': 'spot', 'symbol': symbol},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0 and data['result']['list']:
                    ticker = data['result']['list'][0]
                    return {
                        'symbol': symbol,
                        'price': float(ticker['lastPrice']),
                        'change_24h': float(ticker['price24hPcnt']) * 100,
                        'volume_24h': float(ticker['volume24h']),
                        'high_24h': float(ticker['highPrice24h']),
                        'low_24h': float(ticker['lowPrice24h'])
                    }
        except Exception as e:
            print(f"❌ Erro ao obter preço de {symbol}: {e}")
        
        return None
    
    def update_all_prices(self) -> Dict[str, Dict]:
        """Atualizar preços de todos os ativos padrão"""
        print("🔄 Atualizando preços dos ativos...")
        
        for asset in self.default_assets:
            symbol = asset['symbol']
            price_data = self.get_asset_price(symbol)
            if price_data:
                self.asset_prices[symbol] = price_data
        
        return self.asset_prices
    
    def display_asset_selection(self) -> None:
        """Exibir interface de seleção de ativos"""
        print("\n" + "="*60)
        print("📊 STRATEGY LAB - SELEÇÃO DE ATIVOS")
        print("="*60)
        
        # Atualizar preços
        self.update_all_prices()
        
        print(f"{'Nº':<3} {'Emoji':<5} {'Symbol':<10} {'Nome':<15} {'Preço':<12} {'24h':<8}")
        print("-" * 60)
        
        for i, asset in enumerate(self.default_assets, 1):
            symbol = asset['symbol']
            emoji = asset['emoji']
            name = asset['name']
            
            if symbol in self.asset_prices:
                price_data = self.asset_prices[symbol]
                price = f"${price_data['price']:,.4f}"
                change = price_data['change_24h']
                change_str = f"{change:+.2f}%"
                change_color = "🟢" if change >= 0 else "🔴"
            else:
                price = "N/A"
                change_str = "N/A"
                change_color = "⚪"
            
            print(f"{i:<3} {emoji:<5} {symbol:<10} {name:<15} {price:<12} {change_color}{change_str}")
        
        print("-" * 60)
        print("💡 Opções:")
        print("   • Digite números separados por vírgula (ex: 1,2,5)")
        print("   • Digite 'all' para selecionar todos")
        print("   • Digite 'top5' para os 5 principais")
        print("   • Digite '0' para voltar")
    
    def parse_selection(self, selection: str) -> List[str]:
        """Processar seleção do usuário"""
        selection = selection.strip().lower()
        
        if selection == '0':
            return []
        elif selection == 'all':
            return [asset['symbol'] for asset in self.default_assets]
        elif selection == 'top5':
            return [asset['symbol'] for asset in self.default_assets[:5]]
        else:
            try:
                indices = [int(x.strip()) for x in selection.split(',')]
                symbols = []
                for idx in indices:
                    if 1 <= idx <= len(self.default_assets):
                        symbols.append(self.default_assets[idx-1]['symbol'])
                    else:
                        print(f"⚠️  Índice {idx} inválido (deve ser 1-{len(self.default_assets)})")
                return symbols
            except ValueError:
                print("❌ Formato inválido. Use números separados por vírgula.")
                return []
    
    def select_assets_interactive(self) -> List[str]:
        """Interface interativa para seleção de ativos"""
        while True:
            self.display_asset_selection()
            
            selection = input(f"\n🔢 Sua seleção: ").strip()
            
            if selection == '0':
                return []
            
            selected_symbols = self.parse_selection(selection)
            
            if selected_symbols:
                print(f"\n✅ Ativos selecionados:")
                for symbol in selected_symbols:
                    asset_info = next((a for a in self.default_assets if a['symbol'] == symbol), None)
                    if asset_info and symbol in self.asset_prices:
                        price_data = self.asset_prices[symbol]
                        emoji = asset_info['emoji']
                        name = asset_info['name']
                        price = price_data['price']
                        change = price_data['change_24h']
                        change_emoji = "🟢" if change >= 0 else "🔴"
                        print(f"   {emoji} {symbol} - {name}: ${price:,.4f} {change_emoji}({change:+.2f}%)")
                
                confirm = input(f"\n✅ Confirmar seleção? (s/N): ").strip().lower()
                if confirm in ['s', 'sim', 'y', 'yes']:
                    self.selected_assets = selected_symbols
                    return selected_symbols
            else:
                print("❌ Nenhum ativo válido selecionado.")
    
    def get_asset_info(self, symbol: str) -> Optional[Dict]:
        """Obter informações completas de um ativo"""
        asset_info = next((a for a in self.default_assets if a['symbol'] == symbol), None)
        if asset_info and symbol in self.asset_prices:
            return {
                **asset_info,
                **self.asset_prices[symbol]
            }
        return None
    
    def validate_assets_liquidity(self, symbols: List[str], min_volume_24h: float = 1000000) -> Dict:
        """Validar liquidez dos ativos selecionados"""
        results = {}
        
        for symbol in symbols:
            if symbol in self.asset_prices:
                price_data = self.asset_prices[symbol]
                volume_usdt = price_data['volume_24h'] * price_data['price']
                
                results[symbol] = {
                    'valid': volume_usdt >= min_volume_24h,
                    'volume_24h_usdt': volume_usdt,
                    'liquidity_score': min(volume_usdt / min_volume_24h, 10.0)  # Score 0-10
                }
            else:
                results[symbol] = {
                    'valid': False,
                    'volume_24h_usdt': 0,
                    'liquidity_score': 0
                }
        
        return results
    
    def save_selection(self, filename: str = "selected_assets.json") -> bool:
        """Salvar seleção de ativos em arquivo"""
        try:
            config_dir = "config"
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            filepath = os.path.join(config_dir, filename)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'selected_symbols': self.selected_assets,
                'asset_data': {symbol: self.get_asset_info(symbol) for symbol in self.selected_assets}
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Seleção salva em: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar seleção: {e}")
            return False
    
    def load_selection(self, filename: str = "selected_assets.json") -> bool:
        """Carregar seleção de ativos de arquivo"""
        try:
            filepath = os.path.join("config", filename)
            
            if not os.path.exists(filepath):
                print(f"⚠️  Arquivo não encontrado: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.selected_assets = data.get('selected_symbols', [])
            print(f"📂 Seleção carregada: {', '.join(self.selected_assets)}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar seleção: {e}")
            return False

def test_asset_manager():
    """Função de teste do AssetManager"""
    print("🧪 TESTANDO ASSET MANAGER")
    print("="*40)
    
    # Inicializar manager
    manager = AssetManager(testnet=True)
    
    # Testar seleção interativa
    selected = manager.select_assets_interactive()
    
    if selected:
        print(f"\n🎯 Resultado final: {len(selected)} ativos selecionados")
        
        # Validar liquidez
        liquidity = manager.validate_assets_liquidity(selected)
        print(f"\n💧 VALIDAÇÃO DE LIQUIDEZ:")
        for symbol, data in liquidity.items():
            status = "✅" if data['valid'] else "❌"
            volume = data['volume_24h_usdt']
            score = data['liquidity_score']
            print(f"   {status} {symbol}: ${volume:,.0f} (Score: {score:.1f}/10)")
        
        # Salvar seleção
        manager.save_selection()
    else:
        print("❌ Nenhum ativo selecionado")

if __name__ == "__main__":
    test_asset_manager()
