import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import os

@dataclass
class BacktestResult:
    """Resultado de um backtest completo"""
    backtest_id: str
    timestamp: str
    combination_id: Optional[str]
    combination_name: Optional[str]
    strategies: List[str]
    timeframe: str
    asset: str
    start_date: str
    end_date: str
    confluence_mode: str
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    initial_capital: float
    final_capital: float
    roi: float
    total_signals: int
    manus_ai_enabled: bool
    semantic_kernel_enabled: bool

@dataclass
class StrategyContribution:
    """Contribuição individual de uma estratégia"""
    backtest_id: str
    strategy_key: str
    strategy_name: str
    total_signals: int
    signals_after_volume_filter: int
    winning_signals: int
    losing_signals: int
    win_rate: float
    weight: float

@dataclass
class WeightRecommendation:
    """Recomendação de ajuste de peso"""
    strategy_key: str
    strategy_name: str
    current_weight: float
    recommended_weight: float
    reason: str
    confidence: float

class PerformanceHistoryRepository:
    """Repositório SQLite para histórico de performance"""
    
    def __init__(self, db_path: str = "data/performance_history.db"):
        self.db_path = db_path
        self._ensure_data_dir()
        self._initialize_database()
    
    def _ensure_data_dir(self):
        """Garante que diretório data/ existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _initialize_database(self):
        """Inicializa schema do banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de backtests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtests (
                backtest_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                combination_id TEXT,
                combination_name TEXT,
                strategies TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                asset TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                confluence_mode TEXT NOT NULL,
                win_rate REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                losing_trades INTEGER NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                roi REAL NOT NULL,
                total_signals INTEGER NOT NULL,
                manus_ai_enabled INTEGER NOT NULL,
                semantic_kernel_enabled INTEGER NOT NULL
            )
        """)
        
        # Tabela de estatísticas por estratégia
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                strategy_key TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                total_signals INTEGER NOT NULL,
                signals_after_volume_filter INTEGER NOT NULL,
                winning_signals INTEGER NOT NULL,
                losing_signals INTEGER NOT NULL,
                win_rate REAL NOT NULL,
                weight REAL NOT NULL,
                FOREIGN KEY (backtest_id) REFERENCES backtests (backtest_id)
            )
        """)
        
        # Índices para queries rápidas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backtests_timestamp ON backtests(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backtests_combination ON backtests(combination_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backtests_timeframe ON backtests(timeframe)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategy_stats_backtest ON strategy_stats(backtest_id)")
        
        conn.commit()
        conn.close()
    
    def save_backtest_result(self, result: BacktestResult, strategy_contributions: List[StrategyContribution]):
        """Salva resultado de backtest com contribuições das estratégias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Salvar backtest
            cursor.execute("""
                INSERT INTO backtests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.backtest_id,
                result.timestamp,
                result.combination_id,
                result.combination_name,
                json.dumps(result.strategies),
                result.timeframe,
                result.asset,
                result.start_date,
                result.end_date,
                result.confluence_mode,
                result.win_rate,
                result.total_trades,
                result.winning_trades,
                result.losing_trades,
                result.initial_capital,
                result.final_capital,
                result.roi,
                result.total_signals,
                1 if result.manus_ai_enabled else 0,
                1 if result.semantic_kernel_enabled else 0
            ))
            
            # Salvar contribuições das estratégias
            for contrib in strategy_contributions:
                cursor.execute("""
                    INSERT INTO strategy_stats 
                    (backtest_id, strategy_key, strategy_name, total_signals, 
                     signals_after_volume_filter, winning_signals, losing_signals, win_rate, weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contrib.backtest_id,
                    contrib.strategy_key,
                    contrib.strategy_name,
                    contrib.total_signals,
                    contrib.signals_after_volume_filter,
                    contrib.winning_signals,
                    contrib.losing_signals,
                    contrib.win_rate,
                    contrib.weight
                ))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_all_backtests(self, limit: Optional[int] = None) -> List[Dict]:
        """Busca todos os backtests ordenados por data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM backtests ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        results = []
        for row in cursor.fetchall():
            results.append({
                'backtest_id': row[0],
                'timestamp': row[1],
                'combination_id': row[2],
                'combination_name': row[3],
                'strategies': json.loads(row[4]),
                'timeframe': row[5],
                'asset': row[6],
                'start_date': row[7],
                'end_date': row[8],
                'confluence_mode': row[9],
                'win_rate': row[10],
                'total_trades': row[11],
                'winning_trades': row[12],
                'losing_trades': row[13],
                'initial_capital': row[14],
                'final_capital': row[15],
                'roi': row[16],
                'total_signals': row[17],
                'manus_ai_enabled': bool(row[18]),
                'semantic_kernel_enabled': bool(row[19])
            })
        
        conn.close()
        return results
    
    def get_combination_history(self, combination_id: str, timeframe: str, days: Optional[int] = None) -> List[Dict]:
        """Busca histórico de uma combinação específica"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM backtests 
            WHERE combination_id = ? AND timeframe = ?
        """
        params = [combination_id, timeframe]
        
        if days:
            query += " AND timestamp >= datetime('now', '-' || ? || ' days')"
            params.append(str(days))
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            results.append({
                'backtest_id': row[0],
                'timestamp': row[1],
                'combination_id': row[2],
                'combination_name': row[3],
                'strategies': json.loads(row[4]),
                'timeframe': row[5],
                'asset': row[6],
                'start_date': row[7],
                'end_date': row[8],
                'confluence_mode': row[9],
                'win_rate': row[10],
                'total_trades': row[11],
                'winning_trades': row[12],
                'losing_trades': row[13],
                'initial_capital': row[14],
                'final_capital': row[15],
                'roi': row[16],
                'total_signals': row[17],
                'manus_ai_enabled': bool(row[18]),
                'semantic_kernel_enabled': bool(row[19])
            })
        
        conn.close()
        return results
    
    def get_strategy_contribution_history(self, backtest_id: str) -> List[Dict]:
        """Busca contribuições das estratégias de um backtest"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT strategy_key, strategy_name, total_signals, signals_after_volume_filter,
                   winning_signals, losing_signals, win_rate, weight
            FROM strategy_stats
            WHERE backtest_id = ?
        """, (backtest_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'strategy_key': row[0],
                'strategy_name': row[1],
                'total_signals': row[2],
                'signals_after_volume_filter': row[3],
                'winning_signals': row[4],
                'losing_signals': row[5],
                'win_rate': row[6],
                'weight': row[7]
            })
        
        conn.close()
        return results
    
    def get_all_combinations_summary(self) -> Dict[str, Dict]:
        """Retorna resumo de todas as combinações já testadas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                combination_id,
                combination_name,
                timeframe,
                COUNT(*) as test_count,
                AVG(win_rate) as avg_win_rate,
                SUM(total_trades) as total_trades,
                AVG(roi) as avg_roi
            FROM backtests
            WHERE combination_id IS NOT NULL
            GROUP BY combination_id, timeframe
        """)
        
        summary = {}
        for row in cursor.fetchall():
            key = f"{row[0]}_{row[2]}"
            summary[key] = {
                'combination_id': row[0],
                'combination_name': row[1],
                'timeframe': row[2],
                'test_count': row[3],
                'avg_win_rate': row[4],
                'total_trades': row[5],
                'avg_roi': row[6]
            }
        
        conn.close()
        return summary
