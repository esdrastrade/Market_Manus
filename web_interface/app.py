"""
Market Manus - Interface Web
Flask application para visualização e controle do sistema de trading
"""
import os
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import asyncio
from threading import Thread
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from market_manus.data_providers.binance_data_provider import BinanceDataProvider
from market_manus.core.capital_manager import CapitalManager
from market_manus.confluence_mode.confluence_mode_module import ConfluenceModeModule
from market_manus.confluence_mode.recommended_combinations import RecommendedCombinations
from market_manus.performance.history_repository import PerformanceHistoryRepository
from market_manus.performance.analytics_service import PerformanceAnalyticsService
from market_manus.sentiment.sentiment_service import gather_sentiment
from market_manus.explanations.strategy_explanations import StrategyExplanations

app = Flask(__name__)
app.config['SECRET_KEY'] = 'market-manus-secret-key-2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

data_provider = None
capital_manager = None
confluence_module = None
performance_repo = None
performance_analytics = None
sentiment_cache = {}
SENTIMENT_CACHE_TTL_SECONDS = 300

def initialize_system():
    """Inicializa os módulos do sistema"""
    global data_provider, capital_manager, confluence_module, performance_repo, performance_analytics
    
    print("🔄 Inicializando sistema Market Manus...")
    
    # Carregar credenciais
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    
    if not api_key or not api_secret:
        print("⚠️  Binance API não configurada - modo demonstração")
        api_key = "demo"
        api_secret = "demo"
    
    data_provider = BinanceDataProvider(
        api_key=api_key,
        api_secret=api_secret,
        testnet=False
    )
    capital_manager = CapitalManager(initial_capital=10000.0)
    
    performance_repo = PerformanceHistoryRepository()
    performance_analytics = PerformanceAnalyticsService(performance_repo)
    
    confluence_module = ConfluenceModeModule(
        data_provider=data_provider,
        capital_manager=capital_manager
    )
    
    print("✅ Sistema inicializado com sucesso!")

@app.route('/')
def index():
    """Dashboard principal"""
    return render_template('dashboard.html')

@app.route('/strategies')
def strategies():
    """Página Strategy Lab"""
    return render_template('strategies.html')

@app.route('/confluence')
def confluence():
    """Página Confluence Lab"""
    return render_template('confluence.html')

@app.route('/backtest')
def backtest():
    """Página de Backtest"""
    return render_template('backtest.html')

@app.route('/performance')
def performance():
    """Página de Performance"""
    return render_template('performance.html')

@app.route('/settings')
def settings():
    """Página de Settings (Capital Dashboard)"""
    return render_template('settings.html')

@app.route('/connectivity')
def connectivity():
    """Página de Connectivity Status"""
    return render_template('connectivity.html')

@app.route('/sentiment')
def sentiment():
    """Página de Market Sentiment"""
    return render_template('sentiment.html')

@app.route('/livetest')
def livetest():
    """Página de Live Test (Tempo Real)"""
    return render_template('livetest.html')

@app.route('/explanations')
def explanations():
    """Página de explicações das estratégias (Docs)"""
    return render_template('explanations.html')

@app.route('/api/system/status')
def system_status():
    """Retorna status do sistema"""
    return jsonify({
        'status': 'online',
        'capital': capital_manager.current_capital if capital_manager else 10000,
        'strategies_count': len(confluence_module.available_strategies) if confluence_module else 0,
        'combinations_count': RecommendedCombinations.get_total_combinations(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/strategies')
def get_strategies():
    """Retorna lista de estratégias disponíveis"""
    if not confluence_module:
        return jsonify({'error': 'Sistema não inicializado'}), 500
    
    strategies = []
    for key, strategy in confluence_module.available_strategies.items():
        strategies.append({
            'key': key,
            'name': strategy['name'],
            'emoji': strategy['emoji'],
            'type': strategy.get('type', 'classic'),
            'description': strategy.get('description', '')
        })
    
    return jsonify({'strategies': strategies})

@app.route('/api/combinations')
def get_combinations():
    """Retorna combinações recomendadas"""
    all_combos = RecommendedCombinations.get_all_combinations()
    
    formatted_combos = []
    for category, combos in all_combos.items():
        for combo in combos:
            formatted_combos.append({
                'id': combo['id'],
                'name': combo['name'],
                'category': category,
                'target_win_rate': combo['target_win_rate'],
                'mode': combo['mode'],
                'strategies': combo['strategies'],
                'best_timeframes': combo['best_timeframes'],
                'description': combo['description'],
                'why_it_works': combo['why_it_works']
            })
    
    return jsonify({'combinations': formatted_combos})

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Executa backtest com configurações fornecidas"""
    try:
        data = request.json
        # Helper para emitir progresso em tempo-real
        def emit_progress(percent: int, message: str, extra: dict = None):
            payload = {'percent': int(percent), 'message': message}
            if extra:
                payload.update(extra)
            try:
                socketio.emit('backtest_progress', payload, broadcast=True)
            except Exception:
                pass
        
        # Extrair parâmetros
        asset = data.get('asset', 'BTCUSDT')
        timeframe = data.get('timeframe', '15')
        strategies = data.get('strategies', [])
        confluence_mode = data.get('mode', 'weighted')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        initial_capital = float(data.get('capital', 10000))
        manus_ai_enabled = data.get('manus_ai', False)
        sk_enabled = data.get('semantic_kernel', False)

        # Normalização de timeframe e datas para evitar 0 candles
        # Aceitar formatos da UI (1m, 5m, 15m, 1h, 4h, 1d) e do engine (1,5,15,60,240,D)
        tf_map_ui_to_engine = {
            '1m': '1', '5m': '5', '15m': '15', '30m': '30', '1h': '60', '4h': '240', '1d': 'D'
        }
        # timeframe pode já vir como número/engine; manter se não houver mapeamento
        tf_engine = tf_map_ui_to_engine.get(str(timeframe).lower(), str(timeframe))

        from datetime import datetime, timedelta
        def normalize_dates(s, e):
            try:
                s_dt = datetime.strptime(s, '%Y-%m-%d') if s else None
            except Exception:
                s_dt = None
            try:
                e_dt = datetime.strptime(e, '%Y-%m-%d') if e else None
            except Exception:
                e_dt = None
            # End date padrão: hoje
            if not e_dt:
                e_dt = datetime.now()
            # Se start ausente/igual/maior que end, usar janela padrão de 30 dias
            if not s_dt or s_dt >= e_dt:
                s_dt = e_dt - timedelta(days=30)
            return s_dt.strftime('%Y-%m-%d'), e_dt.strftime('%Y-%m-%d')

        norm_start_date, norm_end_date = normalize_dates(start_date, end_date)
        
        # Validar parâmetros
        if not strategies or len(strategies) == 0:
            return jsonify({
                'status': 'error',
                'message': 'Selecione pelo menos uma estratégia'
            }), 400
        
        # Importar módulos necessários
        from market_manus.confluence_mode.confluence_mode_module import ConfluenceModeModule
        from datetime import datetime
        import uuid
        import os
        
        # Determinar exchange a usar
        exchange = data.get('exchange', 'binance')
        emit_progress(5, 'Iniciando backtest', {
            'exchange': exchange,
            'asset': asset,
            'timeframe': tf_engine,
            'strategies': strategies,
            'mode': confluence_mode
        })
        
        # Criar data provider baseado na exchange selecionada
        if exchange == 'bybit':
            from market_manus.data_providers.bybit_real_data_provider import BybitRealDataProvider
            
            api_key = os.getenv('BYBIT_API_KEY', '')
            api_secret = os.getenv('BYBIT_API_SECRET', '')
            
            if not api_key or not api_secret:
                return jsonify({
                    'status': 'error',
                    'message': 'Chaves API do Bybit não configuradas. Configure BYBIT_API_KEY e BYBIT_API_SECRET.'
                }), 500
            
            data_provider = BybitRealDataProvider(api_key=api_key, api_secret=api_secret)
            emit_progress(10, 'Conectado à Bybit e preparando provider')
        else:  # binance (default)
            from market_manus.data_providers.binance_data_provider import BinanceDataProvider
            
            api_key = os.getenv('BINANCE_API_KEY', '')
            api_secret = os.getenv('BINANCE_API_SECRET', '')
            
            if not api_key or not api_secret:
                return jsonify({
                    'status': 'error',
                    'message': 'Chaves API do Binance não configuradas. Configure BINANCE_API_KEY e BINANCE_API_SECRET.'
                }), 500
            
            data_provider = BinanceDataProvider(api_key=api_key, api_secret=api_secret)
            emit_progress(10, 'Conectado à Binance e preparando provider')
        
        # Criar módulo de confluência
        confluence_module = ConfluenceModeModule(
            data_provider=data_provider,
            capital_manager=None
        )
        
        # Configurar parâmetros
        confluence_module.selected_asset = asset
        confluence_module.selected_timeframe = tf_engine
        confluence_module.selected_strategies = strategies
        confluence_module.selected_confluence_mode = confluence_mode
        confluence_module.custom_start_date = norm_start_date
        confluence_module.custom_end_date = norm_end_date
        confluence_module.manus_ai_enabled = manus_ai_enabled
        confluence_module.sk_advisor_enabled = sk_enabled
        
        # Executar backtest programaticamente
        print(f"\n🧪 Executando backtest via Web API...")
        print(f"   Asset: {asset}, Timeframe: {tf_engine}")
        print(f"   Strategies: {len(strategies)}, Mode: {confluence_mode}")
        
        # Buscar dados históricos
        emit_progress(15, 'Carregando dados históricos', {
            'start_date': norm_start_date,
            'end_date': norm_end_date
        })
        klines, metrics = confluence_module._fetch_historical_klines(
            symbol=asset,
            interval=tf_engine,
            start_date=norm_start_date,
            end_date=norm_end_date
        )
        
        if not klines or len(klines) < 50:
            return jsonify({
                'status': 'error',
                'message': f'Dados insuficientes: {len(klines) if klines else 0} candles recebidos'
            }), 400
        
        emit_progress(25, f'Dados carregados: {len(klines)} candles')
        # Converter dados OHLCV
        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        volumes_raw = [float(k[5]) if len(k) > 5 else 0.0 for k in klines]
        
        import pandas as pd
        volumes = pd.Series(volumes_raw)
        
        emit_progress(35, 'Pré-processando OHLCV e volume')
        # Executar estratégias
        strategy_signals = {}
        for idx, strategy_key in enumerate(strategies, start=1):
            if strategy_key in confluence_module.available_strategies:
                strategy = confluence_module.available_strategies[strategy_key]
                emit_progress(35 + int(25 * (idx / max(1, len(strategies)))), f'Calculando sinais: {strategy["name"]}')
                signal_indices = confluence_module._execute_strategy_on_data(
                    strategy_key, closes, highs, lows, opens
                )
                strategy_signals[strategy_key] = {
                    "name": strategy['name'],
                    "signal_indices": signal_indices,
                    "weight": strategy.get('weight', 1.0)
                }
        
        # Aplicar filtro de volume
        if volumes.sum() > 0:
            confluence_module.volume_pipeline.reset_stats()
            filtered_strategy_signals = confluence_module.volume_pipeline.apply_to_strategy_signals(
                strategy_signals, volumes
            )
        else:
            filtered_strategy_signals = strategy_signals
        emit_progress(65, 'Aplicando filtro de volume e limpeza de sinais')
        
        # Calcular confluência
        confluence_signals = confluence_module._calculate_confluence_signals(filtered_strategy_signals)
        emit_progress(75, f'Confluência calculada — {len(confluence_signals)} sinais totais')
        
        # Simular trades
        final_capital, total_trades, winning_trades = confluence_module._simulate_trades_from_signals(
            confluence_signals, closes, initial_capital, highs, lows
        )
        emit_progress(90, f'Simulando trades — {total_trades} executados')
        
        losing_trades = total_trades - winning_trades
        pnl = final_capital - initial_capital
        roi = (pnl / initial_capital) * 100
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Contar sinais por direção
        buy_signals = sum(1 for _, direction in confluence_signals if direction == "BUY")
        sell_signals = sum(1 for _, direction in confluence_signals if direction == "SELL")
        
        # Salvar no repositório de performance
        from market_manus.performance.history_repository import (
            PerformanceHistoryRepository, BacktestResult, StrategyContribution
        )
        
        repo = PerformanceHistoryRepository()
        backtest_id = str(uuid.uuid4())[:8]
        
        # Preparar resultado
        backtest_result = BacktestResult(
            backtest_id=backtest_id,
            timestamp=datetime.now().isoformat(),
            combination_id=data.get('combination_id'),
            combination_name=data.get('combination_name'),
            strategies=strategies,
            timeframe=tf_engine,
            asset=asset,
            start_date=norm_start_date or "auto",
            end_date=norm_end_date or "auto",
            confluence_mode=confluence_mode,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            initial_capital=initial_capital,
            final_capital=final_capital,
            roi=roi,
            total_signals=len(confluence_signals),
            manus_ai_enabled=manus_ai_enabled,
            semantic_kernel_enabled=sk_enabled
        )
        
        # Preparar contribuições das estratégias
        contributions = []
        for strategy_key, data in filtered_strategy_signals.items():
            contrib = StrategyContribution(
                backtest_id=backtest_id,
                strategy_key=strategy_key,
                strategy_name=data['name'],
                total_signals=data.get('original_count', len(data['signal_indices'])),
                signals_after_volume_filter=len(data['signal_indices']),
                winning_signals=0,  # Não temos dados granulares por estratégia
                losing_signals=0,
                win_rate=0.0,
                weight=data['weight']
            )
            contributions.append(contrib)
        
        # Salvar no repositório
        repo.save_backtest_result(backtest_result, contributions)
        emit_progress(95, 'Salvando resultado e métricas no SQLite', {'backtest_id': backtest_id})
        
        print(f"✅ Backtest concluído: {win_rate:.1f}% win rate, {roi:+.2f}% ROI")
        emit_progress(100, f'Concluído: ROI {roi:+.2f}% · Win rate {win_rate:.1f}%', {
            'final_capital': final_capital,
            'initial_capital': initial_capital,
            'win_rate': win_rate,
            'roi': roi
        })
        
        # Preparar recomendações de IA e peso
        ai_payload = {}
        weight_recommendations_data = []

        try:
            from market_manus.performance.analytics_service import PerformanceAnalyticsService
            analytics = PerformanceAnalyticsService(repo)
            current_weights = {k: v.get('weight', 1.0) for k, v in filtered_strategy_signals.items()}
            weight_recs = analytics.calculate_weight_recommendations(backtest_id, current_weights)
            weight_recommendations_data = [
                {
                    'strategy_key': rec.strategy_key,
                    'strategy_name': rec.strategy_name,
                    'current_weight': rec.current_weight,
                    'recommended_weight': rec.recommended_weight,
                    'reason': rec.reason,
                    'confidence': rec.confidence
                }
                for rec in weight_recs
            ]
        except Exception:
            weight_recommendations_data = []

        if sk_enabled:
            try:
                from market_manus.ai.semantic_kernel_advisor import SemanticKernelAdvisor
                sk = SemanticKernelAdvisor()
                if sk.is_available():
                    backtest_summary = {
                        'asset': asset,
                        'timeframe': tf_engine,
                        'start_date': norm_start_date,
                        'end_date': norm_end_date,
                        'confluence_mode': confluence_mode,
                        'win_rate': win_rate,
                        'total_trades': total_trades,
                        'roi': roi,
                        'initial_capital': initial_capital,
                        'final_capital': final_capital
                    }
                    strategy_contributions_data = [
                        {
                            'strategy_name': data.get('name'),
                            'signals_after_volume_filter': len(data['signal_indices']),
                            'win_rate': win_rate,
                            'weight': data.get('weight', 1.0),
                            'winning_signals': int(len(data['signal_indices']) * win_rate / 100),
                            'losing_signals': int(len(data['signal_indices']) * (100 - win_rate) / 100)
                        }
                        for data in filtered_strategy_signals.values()
                    ]
                    sk_text = sk.generate_recommendations(
                        backtest_summary,
                        strategy_contributions_data,
                        weight_recommendations_data
                    )
                    ai_payload['semantic_kernel'] = {'available': True, 'text': sk_text}
                else:
                    ai_payload['semantic_kernel'] = {'available': False, 'text': '❌ Semantic Kernel não disponível (OPENAI_API_KEY não configurada)'}
            except Exception as e:
                ai_payload['semantic_kernel'] = {'available': False, 'text': f'❌ Erro ao gerar recomendações SK: {str(e)}'}

        if manus_ai_enabled:
            try:
                from market_manus.ai.manus_ai_integration import ManusAIAnalyzer
                import pandas as pd, asyncio
                analyzer = ManusAIAnalyzer()
                df = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes, 'volume': volumes.tolist() if hasattr(volumes, 'tolist') else volumes_raw})
                strategies_votes = {
                    s['name']: {
                        'action': 'BUY' if buy_signals >= sell_signals else ('SELL' if sell_signals > buy_signals else 'NEUTRAL'),
                        'confidence': max(0.3, min(0.9, (win_rate/100)))
                    }
                    for s in filtered_strategy_signals.values()
                }
                ai_analysis = asyncio.run(analyzer.analyze_market_context(df, asset, strategies_votes))
                ai_payload['manus_ai'] = ai_analysis
            except Exception as e:
                ai_payload['manus_ai'] = {'ai_enabled': False, 'error': f'Erro Manus AI: {str(e)}'}

        return jsonify({
            'status': 'success',
            'backtest_id': backtest_id,
            'results': {
                'initial_capital': initial_capital,
                'final_capital': final_capital,
                'pnl': pnl,
                'roi': roi,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_signals': len(confluence_signals),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'candles_analyzed': len(closes),
                'strategies_used': len(strategies)
            },
            'strategy_details': [
                {
                    'name': data['name'],
                    'signals': len(data['signal_indices']),
                    'weight': data['weight']
                }
                for data in filtered_strategy_signals.values()
            ],
            'ai': ai_payload,
            'weight_recommendations': weight_recommendations_data
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erro no backtest: {str(e)}")
        print(error_trace)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'details': error_trace
        }), 500

@app.route('/api/performance/summary')
def get_performance_summary():
    """Retorna resumo de performance de todos os backtests"""
    try:
        from market_manus.performance.history_repository import PerformanceHistoryRepository
        repo = PerformanceHistoryRepository()
        
        all_backtests = repo.get_all_backtests(limit=100)
        
        if not all_backtests:
            return jsonify({
                'total_backtests': 0,
                'avg_win_rate': 0,
                'avg_roi': 0,
                'best_combination': None,
                'recent_backtests': []
            })
        
        # Calcular métricas gerais
        total = len(all_backtests)
        avg_win_rate = sum(b['win_rate'] for b in all_backtests) / total
        avg_roi = sum(b['roi'] for b in all_backtests) / total
        
        # Melhor combinação
        best = max(all_backtests, key=lambda x: x['win_rate'])
        
        # Formatar backtests recentes
        recent = [{
            'backtest_id': b['backtest_id'],
            'timestamp': b['timestamp'],
            'asset': b['asset'],
            'timeframe': b['timeframe'],
            'combination_name': b['combination_name'] or 'Custom',
            'total_trades': b['total_trades'],
            'win_rate': b['win_rate'],
            'roi': b['roi'],
            'manus_ai_enabled': b['manus_ai_enabled'],
            'semantic_kernel_enabled': b['semantic_kernel_enabled']
        } for b in all_backtests[:20]]
        
        return jsonify({
            'total_backtests': total,
            'avg_win_rate': avg_win_rate,
            'avg_roi': avg_roi,
            'best_combination': {
                'name': best['combination_name'] or 'Custom',
                'win_rate': best['win_rate']
            },
            'recent_backtests': recent
        })
        
    except Exception as e:
        print(f"Erro ao buscar performance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance/export/<backtest_id>')
def export_backtest_report(backtest_id):
    """Exporta relatório de backtest em JSON"""
    try:
        from market_manus.performance.history_repository import PerformanceHistoryRepository
        import json
        
        repo = PerformanceHistoryRepository()
        backtest = repo.get_backtest_by_id(backtest_id)
        strategies = repo.get_strategy_contributions(backtest_id)
        
        if not backtest:
            return jsonify({'error': 'Backtest não encontrado'}), 404
        
        report = {
            'backtest': backtest,
            'strategies': strategies,
            'exported_at': datetime.now().isoformat()
        }
        
        return jsonify(report)
        
    except Exception as e:
        print(f"Erro ao exportar relatório: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/capital/status')
def capital_status():
    """Retorna status detalhado do capital"""
    if not capital_manager:
        return jsonify({'error': 'Capital Manager não inicializado'}), 500
    
    stats = capital_manager.get_stats()
    
    return jsonify({
        'initial_capital': capital_manager.initial_capital,
        'current_capital': capital_manager.current_capital,
        'position_size': capital_manager.get_position_size(),
        'position_size_pct': capital_manager.position_size_pct * 100,
        'total_pnl': stats['total_pnl'],
        'total_trades': stats['total_trades'],
        'win_rate': stats['win_rate'],
        'max_drawdown': stats.get('max_drawdown', 0),
        'sharpe_ratio': stats.get('sharpe_ratio', 0)
    })

@app.route('/api/capital/update', methods=['POST'])
def update_capital():
    """Atualiza configurações de capital"""
    if not capital_manager:
        return jsonify({'success': False, 'error': 'Capital Manager não inicializado'}), 500
    
    data = request.get_json()
    
    try:
        if 'initial_capital' in data:
            new_capital = float(data['initial_capital'])
            if new_capital < 100:
                return jsonify({'success': False, 'error': 'Capital mínimo: $100'}), 400
            
            capital_manager.initial_capital = new_capital
            capital_manager.current_capital = new_capital
            capital_manager.peak_capital = new_capital
            capital_manager.total_pnl = 0.0
            capital_manager.total_trades = 0
            capital_manager.winning_trades = 0
            capital_manager.losing_trades = 0
            capital_manager._save_data()
        
        if 'position_size_pct' in data:
            new_pct = float(data['position_size_pct']) / 100
            if new_pct < 0.001 or new_pct > 0.1:
                return jsonify({'success': False, 'error': 'Position size: 0.1% - 10%'}), 400
            
            capital_manager.position_size_pct = new_pct
            capital_manager._save_data()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/capital/reset', methods=['POST'])
def reset_capital():
    """Reseta capital para valor inicial"""
    if not capital_manager:
        return jsonify({'success': False, 'error': 'Capital Manager não inicializado'}), 500
    
    try:
        capital_manager.reset_capital()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/connectivity/binance')
def connectivity_binance():
    """Verifica conectividade com Binance API"""
    if not data_provider:
        return jsonify({'connected': False, 'error': 'Data Provider não inicializado'})
    
    try:
        result = data_provider.test_connection()
        
        if result:
            tickers = data_provider.get_tickers(category="spot")
            pairs_count = len(tickers.get('list', [])) if tickers else 0
            
            return jsonify({
                'connected': True,
                'endpoint': data_provider.base_url,
                'api_key': f"{os.getenv('BINANCE_API_KEY', '')[:10]}..." if os.getenv('BINANCE_API_KEY') else 'Não configurado',
                'pairs_count': pairs_count
            })
        else:
            return jsonify({'connected': False, 'error': 'Falha no teste de conexão'})
    
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})

@app.route('/api/connectivity/openai')
def connectivity_openai():
    """Verifica se OpenAI API está configurada"""
    openai_key = os.getenv('OPENAI_API_KEY', '')
    
    if openai_key:
        return jsonify({'configured': True, 'api_key': f"{openai_key[:10]}..."})
    else:
        return jsonify({'configured': False, 'api_key': 'Não configurado'})

@app.route('/api/connectivity/manus')
def connectivity_manus():
    """Verifica se Manus AI API está configurada"""
    manus_key = os.getenv('MANUS_AI_API_KEY', '')
    
    if manus_key:
        return jsonify({'configured': True, 'api_key': f"{manus_key[:10]}..."})
    else:
        return jsonify({'configured': False, 'api_key': 'Não configurado'})

@app.route('/api/sentiment/<asset>')
def get_sentiment(asset):
    """Retorna análise de sentimento do mercado"""
    try:
        import random
        from datetime import datetime, timedelta
        
        # Cache simples em memória para estabilizar resultados por ativo
        force_refresh = request.args.get('force_refresh', 'false').lower() in ('1', 'true', 'yes')
        now = datetime.now()
        cached = sentiment_cache.get(asset)
        if cached and not force_refresh:
            ts = cached.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except Exception:
                    ts = now
            if ts and (now - ts) < timedelta(seconds=SENTIMENT_CACHE_TTL_SECONDS):
                return jsonify(cached['data'])
        
        # Coletar dados reais de sentimento/mercado
        result = asyncio.run(gather_sentiment(asset, "1d"))
        sources = result.get('sources', [])
        score = result.get('score')
        coingecko = next((s for s in sources if s.get('source') == 'coingecko' and not s.get('error')), None)
        change_24h = coingecko.get('chg_24h') if coingecko else None
        vol_24h = coingecko.get('vol_24h') if coingecko else None
        alt = next((s for s in sources if s.get('kind') == 'macro_sentiment' and 'score' in s), None)
        
        fear_greed_value = int(round(float(score) * 100)) if score is not None else int(round(float(alt.get('score', 50))))
        if fear_greed_value < 25:
            fear_greed_label = 'Extreme Fear'
        elif fear_greed_value < 45:
            fear_greed_label = 'Fear'
        elif fear_greed_value < 55:
            fear_greed_label = 'Neutral'
        elif fear_greed_value < 75:
            fear_greed_label = 'Greed'
        else:
            fear_greed_label = 'Extreme Greed'
        
        regimes = ['BULLISH', 'BEARISH', 'NEUTRAL', 'CORRECTION']
        regime = 'BULLISH' if (score is not None and score >= 0.7) else 'BEARISH' if (score is not None and score <= 0.3) else 'NEUTRAL'
        
        if regime == 'BULLISH':
            prognosis_title = 'Mercado em Alta'
            prognosis_desc = 'Sinais técnicos indicam tendência de alta. Volume crescente e suporte forte.'
            recommendation = 'Considere posições LONG'
        elif regime == 'BEARISH':
            prognosis_title = 'Mercado em Baixa'
            prognosis_desc = 'Pressão vendedora detectada. Rompimento de suportes importantes.'
            recommendation = 'Cautela: considere proteções'
        elif regime == 'CORRECTION':
            prognosis_title = 'Correção em Curso'
            prognosis_desc = 'Movimento de correção técnica após rally. Normal em mercados saudáveis.'
            recommendation = 'Aguardar estabilização'
        else:
            prognosis_title = 'Mercado Lateral'
            prognosis_desc = 'Consolidação entre suporte e resistência. Aguardando definição.'
            recommendation = 'Aguardar breakout'
        
        payload = {
            'asset': asset,
            'fear_greed': {'value': fear_greed_value, 'label': fear_greed_label},
            'prognosis': {
                'title': prognosis_title,
                'description': prognosis_desc,
                'regime': regime,
                'trend': 'Alta' if regime == 'BULLISH' else 'Baixa' if regime == 'BEARISH' else 'Lateral',
                'volatility': f'{abs(change_24h):.1f}%' if isinstance(change_24h, (int, float)) else '--',
                'recommendation': recommendation
            },
            'market_data': {
                'volume_24h': vol_24h if vol_24h is not None else '--',
                'market_cap': '--',
                'volatility': f'{abs(change_24h):.1f}%' if isinstance(change_24h, (int, float)) else '--',
                'change_24h': float(change_24h) if isinstance(change_24h, (int, float)) else 0.0
            },
            'social': {
                'summary': f'Sem dados sociais/notícias recentes para {asset}.'
            }
        }
        sentiment_cache[asset] = {'timestamp': now.isoformat(), 'data': payload}
        return jsonify(payload)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/list')
def list_cache():
    """Lista arquivos em cache"""
    try:
        import os
        from pathlib import Path
        
        cache_dir = Path('data')
        if not cache_dir.exists():
            return jsonify({'cache_files': [], 'total_size': '0 B'})
        
        files = []
        total_size = 0
        
        for file in cache_dir.glob('*.parquet'):
            size = file.stat().st_size
            total_size += size
            files.append({
                'name': file.name,
                'size': f'{size / 1024:.1f} KB' if size < 1024*1024 else f'{size / (1024*1024):.1f} MB'
            })
        
        total_size_str = f'{total_size / 1024:.1f} KB' if total_size < 1024*1024 else f'{total_size / (1024*1024):.1f} MB'
        
        return jsonify({
            'cache_files': files,
            'total_size': total_size_str
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/delete', methods=['POST'])
def delete_cache():
    """Deleta arquivo de cache específico"""
    try:
        from pathlib import Path
        
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'Filename não fornecido'}), 400
        
        cache_file = Path('data') / filename
        
        if cache_file.exists() and cache_file.suffix == '.parquet':
            cache_file.unlink()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Limpa todo o cache"""
    try:
        from pathlib import Path
        import shutil
        
        cache_dir = Path('data')
        
        if cache_dir.exists():
            for file in cache_dir.glob('*.parquet'):
                file.unlink()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/combination/<int:combination_id>')
def get_combination(combination_id):
    """Retorna detalhes de uma combinação específica"""
    try:
        from market_manus.confluence_mode.recommended_combinations import RecommendedCombinations
        
        rc = RecommendedCombinations()
        all_combos_dict = rc.get_all_combinations()
        
        # Achatar todas as combinações em uma lista única
        all_combos = []
        for category, combos in all_combos_dict.items():
            for combo in combos:
                combo['category'] = category
                all_combos.append(combo)
        
        # Procurar pela combinação específica
        combo = next((c for c in all_combos if c['id'] == combination_id), None)
        
        if not combo:
            return jsonify({'error': 'Combinação não encontrada'}), 404
        
        return jsonify(combo)
    
    except Exception as e:
        import traceback
        print(f"Erro ao buscar combinação: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance/export')
def export_performance():
    """Exporta resultados em JSON ou CSV"""
    try:
        from io import StringIO
        import csv
        
        format_type = request.args.get('format', 'json')
        
        # Obter dados do banco
        summary = get_performance_summary()
        
        if format_type == 'csv':
            # Criar CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Cabeçalho
            writer.writerow(['Data', 'Ativo', 'Timeframe', 'Combinação', 'Trades', 'Win Rate (%)', 'ROI (%)', 'Manus AI', 'Semantic Kernel'])
            
            # Dados
            for b in summary.get('recent_backtests', []):
                writer.writerow([
                    b.get('timestamp', ''),
                    b.get('asset', ''),
                    b.get('timeframe', ''),
                    b.get('combination_name', ''),
                    b.get('total_trades', 0),
                    round(b.get('win_rate', 0), 2),
                    round(b.get('roi', 0), 2),
                    'Sim' if b.get('manus_ai_enabled') else 'Não',
                    'Sim' if b.get('semantic_kernel_enabled') else 'Não'
                ])
            
            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = 'attachment; filename=market_manus_performance.csv'
            return response
        
        else:  # JSON
            response = Response(
                json.dumps(summary, indent=2, ensure_ascii=False),
                mimetype='application/json'
            )
            response.headers['Content-Disposition'] = 'attachment; filename=market_manus_performance.json'
            return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================
# Strategy Explanations API
# =============================
@app.route('/api/explanations/strategies')
def list_explanations_strategies():
    """Lista metadados das estratégias com agrupamento clássico/SMC"""
    explainer = StrategyExplanations()
    result = {'classic': [], 'smc': []}
    for key, data in explainer.strategies.items():
        item = {
            'key': key,
            'name': data.get('name'),
            'emoji': data.get('emoji'),
            'type': data.get('type'),
            'description': data.get('description')
        }
        if key.startswith('smc_'):
            result['smc'].append(item)
        else:
            result['classic'].append(item)
    return jsonify(result)

@app.route('/api/explanations/strategy/<key>')
def get_explanation_for_strategy(key: str):
    """Retorna a explicação completa para uma estratégia"""
    explainer = StrategyExplanations()
    data = explainer.strategies.get(key)
    if not data:
        return jsonify({'error': f"Estratégia '{key}' não encontrada"}), 404
    return jsonify({
        'key': key,
        'name': data.get('name'),
        'emoji': data.get('emoji'),
        'type': data.get('type'),
        'description': data.get('description'),
        'logic': data.get('logic'),
        'triggers': data.get('triggers'),
        'parameters': data.get('parameters'),
        'best_for': data.get('best_for'),
        'avoid': data.get('avoid')
    })


@socketio.on('connect')
def handle_connect():
    """Cliente conectado via WebSocket"""
    print("✅ Cliente conectado via WebSocket")
    emit('status', {'message': 'Conectado ao Market Manus'})

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f"❌ Cliente desconectado")

def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """Inicia servidor web"""
    initialize_system()
    print(f"\n🌐 Iniciando interface web em http://{host}:{port}")
    print("📊 Acesse o dashboard para começar!\n")
    socketio.run(
        app, 
        host=host, 
        port=port, 
        debug=debug, 
        allow_unsafe_werkzeug=True,
        use_reloader=False,
        log_output=True
    )

if __name__ == '__main__':
    run_web_server(debug=True)
