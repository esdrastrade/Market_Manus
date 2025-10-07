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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from market_manus.data_providers.binance_data_provider import BinanceDataProvider
from market_manus.capital_manager.capital_manager import CapitalManager
from market_manus.confluence_mode.confluence_mode_module import ConfluenceModeModule
from market_manus.confluence_mode.recommended_combinations import RecommendedCombinations
from market_manus.performance.history_repository import PerformanceHistoryRepository
from market_manus.performance.analytics_service import PerformanceAnalyticsService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'market-manus-secret-key-2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

data_provider = None
capital_manager = None
confluence_module = None
performance_repo = None
performance_analytics = None

def initialize_system():
    """Inicializa os módulos do sistema"""
    global data_provider, capital_manager, confluence_module, performance_repo, performance_analytics
    
    print("🔄 Inicializando sistema Market Manus...")
    
    data_provider = BinanceDataProvider()
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
    data = request.json
    
    # TODO: Implementar execução de backtest assíncrono
    
    return jsonify({
        'status': 'queued',
        'message': 'Backtest adicionado à fila de execução'
    })

@socketio.on('connect')
def handle_connect():
    """Cliente conectado via WebSocket"""
    print(f"✅ Cliente conectado: {request.sid}")
    emit('status', {'message': 'Conectado ao Market Manus'})

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f"❌ Cliente desconectado: {request.sid}")

def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """Inicia servidor web"""
    initialize_system()
    print(f"\n🌐 Iniciando interface web em http://{host}:{port}")
    print("📊 Acesse o dashboard para começar!\n")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_web_server(debug=True)
