#!/usr/bin/env python3
"""
Orchestrator Agent para Sistema de Scalping Automatizado
Responsável por coordenar todos os agentes e gerenciar o sistema como um todo
Autor: Manus AI
Data: 17 de Julho de 2025
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import threading
import queue

# Adicionar diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, SuggestionType, AlertSeverity

class OrchestratorAgent(BaseAgent):
    """
    Agente Orquestrador
    
    Responsabilidades:
    - Coordenação de todos os agentes do sistema
    - Monitoramento de saúde dos agentes
    - Gerenciamento de dependências entre agentes
    - Controle de fluxo de execução
    - Consolidação de métricas do sistema
    - Detecção e recuperação de falhas
    - Balanceamento de carga entre agentes
    
    Frequência: Contínuo (master process)
    """
    
    def __init__(self):
        super().__init__("OrchestratorAgent")
        
        # Configuração dos agentes
        self.agents_config = self.load_agents_config()
        
        # Estado dos agentes
        self.agents_status = {}
        
        # Fila de tarefas
        self.task_queue = queue.Queue()
        
        # Métricas consolidadas
        self.system_metrics = {}
        
        # Histórico de execuções
        self.execution_history = []
        
        # Threads de monitoramento
        self.monitoring_threads = {}
        
        # Sistema ativo
        self.system_active = True
        
        self.logger.info("OrchestratorAgent inicializado")
    
    def load_agents_config(self) -> Dict:
        """Carrega configuração dos agentes"""
        try:
            config_file = "config/agents_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        
        # Configuração padrão
        return {
            "agents": {
                "market_analysis": {
                    "module": "agents.market_analysis_agent",
                    "class": "MarketAnalysisAgent",
                    "schedule": "*/5 * * * *",  # A cada 5 minutos
                    "priority": 1,
                    "dependencies": [],
                    "timeout": 300,  # 5 minutos
                    "retry_count": 3,
                    "enabled": True
                },
                "risk_management": {
                    "module": "agents.risk_management_agent",
                    "class": "RiskManagementAgent",
                    "schedule": "*/1 * * * *",  # A cada 1 minuto
                    "priority": 2,
                    "dependencies": ["market_analysis"],
                    "timeout": 180,  # 3 minutos
                    "retry_count": 3,
                    "enabled": True
                },
                "notification": {
                    "module": "agents.notification_agent",
                    "class": "NotificationAgent",
                    "schedule": "event_driven",  # Baseado em eventos
                    "priority": 3,
                    "dependencies": [],
                    "timeout": 120,  # 2 minutos
                    "retry_count": 2,
                    "enabled": True
                },
                "performance": {
                    "module": "agents.performance_agent",
                    "class": "PerformanceAgent",
                    "schedule": "0 */6 * * *",  # A cada 6 horas
                    "priority": 4,
                    "dependencies": ["market_analysis", "risk_management"],
                    "timeout": 600,  # 10 minutos
                    "retry_count": 2,
                    "enabled": True
                },
                "backtesting": {
                    "module": "agents.backtesting_agent",
                    "class": "BacktestingAgent",
                    "schedule": "0 2 * * *",  # Diário às 2:00
                    "priority": 5,
                    "dependencies": [],
                    "timeout": 1800,  # 30 minutos
                    "retry_count": 1,
                    "enabled": True
                }
            },
            "system": {
                "max_concurrent_agents": 3,
                "health_check_interval": 60,  # 1 minuto
                "restart_failed_agents": True,
                "emergency_shutdown_threshold": 3,  # Falhas consecutivas
                "log_retention_days": 30
            }
        }
    
    def initialize_agents_status(self):
        """Inicializa status de todos os agentes"""
        try:
            for agent_name, config in self.agents_config["agents"].items():
                self.agents_status[agent_name] = {
                    "status": "stopped",
                    "last_run": None,
                    "last_success": None,
                    "last_error": None,
                    "consecutive_failures": 0,
                    "total_runs": 0,
                    "total_successes": 0,
                    "total_failures": 0,
                    "avg_execution_time": 0,
                    "current_pid": None,
                    "config": config
                }
            
            self.logger.info(f"Status inicializado para {len(self.agents_status)} agentes")
            
        except Exception as e:
            self.handle_error(e, "initialize_agents_status")
    
    def check_agent_dependencies(self, agent_name: str) -> bool:
        """
        Verifica se as dependências de um agente foram satisfeitas
        
        Args:
            agent_name: Nome do agente
            
        Returns:
            bool: True se dependências satisfeitas
        """
        try:
            config = self.agents_config["agents"][agent_name]
            dependencies = config.get("dependencies", [])
            
            if not dependencies:
                return True
            
            # Verificar se todas as dependências executaram com sucesso recentemente
            for dep_agent in dependencies:
                if dep_agent not in self.agents_status:
                    return False
                
                dep_status = self.agents_status[dep_agent]
                
                # Verificar se executou com sucesso nas últimas 2 horas
                if dep_status["last_success"]:
                    last_success = datetime.fromisoformat(dep_status["last_success"])
                    if datetime.now() - last_success > timedelta(hours=2):
                        return False
                else:
                    return False
            
            return True
            
        except Exception as e:
            self.handle_error(e, "check_agent_dependencies")
            return False
    
    def execute_agent(self, agent_name: str) -> Dict:
        """
        Executa um agente específico
        
        Args:
            agent_name: Nome do agente
            
        Returns:
            Dict: Resultado da execução
        """
        try:
            config = self.agents_config["agents"][agent_name]
            
            if not config.get("enabled", True):
                return {"status": "disabled", "message": "Agente desabilitado"}
            
            # Verificar dependências
            if not self.check_agent_dependencies(agent_name):
                return {"status": "dependencies_not_met", "message": "Dependências não satisfeitas"}
            
            # Atualizar status
            self.agents_status[agent_name]["status"] = "running"
            self.agents_status[agent_name]["last_run"] = datetime.now().isoformat()
            
            start_time = time.time()
            
            # Executar agente
            module_path = config["module"]
            script_path = module_path.replace(".", "/") + ".py"
            
            self.logger.info(f"Executando agente: {agent_name}")
            
            # Executar como subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                capture_output=True,
                text=True,
                timeout=config.get("timeout", 300)
            )
            
            execution_time = time.time() - start_time
            
            # Processar resultado
            if result.returncode == 0:
                # Sucesso
                self.agents_status[agent_name]["status"] = "completed"
                self.agents_status[agent_name]["last_success"] = datetime.now().isoformat()
                self.agents_status[agent_name]["consecutive_failures"] = 0
                self.agents_status[agent_name]["total_successes"] += 1
                
                execution_result = {
                    "status": "success",
                    "execution_time": execution_time,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
                self.logger.info(f"Agente {agent_name} executado com sucesso ({execution_time:.1f}s)")
                
            else:
                # Falha
                self.agents_status[agent_name]["status"] = "failed"
                self.agents_status[agent_name]["last_error"] = datetime.now().isoformat()
                self.agents_status[agent_name]["consecutive_failures"] += 1
                self.agents_status[agent_name]["total_failures"] += 1
                
                execution_result = {
                    "status": "failed",
                    "execution_time": execution_time,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": f"Processo terminou com código {result.returncode}"
                }
                
                self.logger.error(f"Agente {agent_name} falhou: {result.stderr}")
            
            # Atualizar estatísticas
            self.agents_status[agent_name]["total_runs"] += 1
            
            # Calcular tempo médio de execução
            current_avg = self.agents_status[agent_name]["avg_execution_time"]
            total_runs = self.agents_status[agent_name]["total_runs"]
            new_avg = ((current_avg * (total_runs - 1)) + execution_time) / total_runs
            self.agents_status[agent_name]["avg_execution_time"] = new_avg
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            self.agents_status[agent_name]["status"] = "timeout"
            self.agents_status[agent_name]["consecutive_failures"] += 1
            self.agents_status[agent_name]["total_failures"] += 1
            
            error_msg = f"Agente {agent_name} excedeu timeout de {config.get('timeout', 300)}s"
            self.logger.error(error_msg)
            
            return {"status": "timeout", "error": error_msg}
            
        except Exception as e:
            self.agents_status[agent_name]["status"] = "error"
            self.agents_status[agent_name]["consecutive_failures"] += 1
            self.agents_status[agent_name]["total_failures"] += 1
            
            error_msg = f"Erro ao executar agente {agent_name}: {str(e)}"
            self.handle_error(e, "execute_agent")
            
            return {"status": "error", "error": error_msg}
    
    def should_execute_agent(self, agent_name: str) -> bool:
        """
        Determina se um agente deve ser executado baseado em seu schedule
        
        Args:
            agent_name: Nome do agente
            
        Returns:
            bool: True se deve executar
        """
        try:
            config = self.agents_config["agents"][agent_name]
            schedule = config.get("schedule", "")
            
            if schedule == "event_driven":
                # Verificar se há eventos pendentes para este agente
                return self.has_pending_events(agent_name)
            
            # Para schedules baseados em cron, simplificar para demonstração
            now = datetime.now()
            last_run = self.agents_status[agent_name]["last_run"]
            
            if not last_run:
                return True  # Primeira execução
            
            last_run_dt = datetime.fromisoformat(last_run)
            
            # Lógica simplificada baseada no schedule
            if "*/5" in schedule:  # A cada 5 minutos
                return (now - last_run_dt).total_seconds() >= 300
            elif "*/1" in schedule:  # A cada 1 minuto
                return (now - last_run_dt).total_seconds() >= 60
            elif "*/6" in schedule:  # A cada 6 horas
                return (now - last_run_dt).total_seconds() >= 21600
            elif "0 2" in schedule:  # Diário às 2:00
                return (now.hour == 2 and now.minute < 5 and 
                       (now - last_run_dt).total_seconds() >= 82800)  # 23 horas
            
            return False
            
        except Exception as e:
            self.handle_error(e, "should_execute_agent")
            return False
    
    def has_pending_events(self, agent_name: str) -> bool:
        """
        Verifica se há eventos pendentes para um agente
        
        Args:
            agent_name: Nome do agente
            
        Returns:
            bool: True se há eventos pendentes
        """
        try:
            if agent_name == "notification":
                # Verificar alertas não processados
                alerts_dir = Path("data/alerts")
                if alerts_dir.exists():
                    for alert_file in alerts_dir.glob("*.json"):
                        try:
                            with open(alert_file, 'r', encoding='utf-8') as f:
                                alert = json.load(f)
                                if not alert.get("processed", False):
                                    return True
                        except:
                            continue
                
                # Verificar sinais novos
                signals_dir = Path("data/signals")
                if signals_dir.exists():
                    cutoff_time = datetime.now() - timedelta(minutes=10)
                    for signal_file in signals_dir.glob("*.json"):
                        try:
                            file_time = datetime.fromtimestamp(signal_file.stat().st_mtime)
                            if file_time >= cutoff_time:
                                with open(signal_file, 'r', encoding='utf-8') as f:
                                    signal = json.load(f)
                                    if not signal.get("notified", False):
                                        return True
                        except:
                            continue
            
            return False
            
        except Exception as e:
            self.handle_error(e, "has_pending_events")
            return False
    
    def get_next_agent_to_execute(self) -> Optional[str]:
        """
        Determina o próximo agente a ser executado baseado em prioridade e schedule
        
        Returns:
            Optional[str]: Nome do agente ou None
        """
        try:
            candidates = []
            
            for agent_name, config in self.agents_config["agents"].items():
                if (config.get("enabled", True) and 
                    self.agents_status[agent_name]["status"] not in ["running"] and
                    self.should_execute_agent(agent_name)):
                    
                    candidates.append({
                        "name": agent_name,
                        "priority": config.get("priority", 999),
                        "consecutive_failures": self.agents_status[agent_name]["consecutive_failures"]
                    })
            
            if not candidates:
                return None
            
            # Filtrar agentes com muitas falhas consecutivas
            max_failures = self.agents_config["system"]["emergency_shutdown_threshold"]
            candidates = [c for c in candidates if c["consecutive_failures"] < max_failures]
            
            if not candidates:
                return None
            
            # Ordenar por prioridade (menor número = maior prioridade)
            candidates.sort(key=lambda x: x["priority"])
            
            return candidates[0]["name"]
            
        except Exception as e:
            self.handle_error(e, "get_next_agent_to_execute")
            return None
    
    def consolidate_system_metrics(self) -> Dict:
        """
        Consolida métricas de todos os agentes
        
        Returns:
            Dict: Métricas consolidadas do sistema
        """
        try:
            # Carregar métricas de cada agente
            agents_metrics = {}
            
            for agent_name in self.agents_config["agents"].keys():
                metrics_file = f"data/metrics/{agent_name}_current.json"
                if os.path.exists(metrics_file):
                    try:
                        with open(metrics_file, 'r', encoding='utf-8') as f:
                            agents_metrics[agent_name] = json.load(f)
                    except:
                        continue
            
            # Consolidar métricas do sistema
            system_metrics = {
                "agents_status": self.agents_status,
                "agents_metrics": agents_metrics,
                "system_health": self.calculate_system_health(),
                "active_agents": len([a for a in self.agents_status.values() if a["status"] == "running"]),
                "total_agents": len(self.agents_status),
                "system_uptime": self.calculate_system_uptime(),
                "consolidation_timestamp": datetime.now().isoformat()
            }
            
            return system_metrics
            
        except Exception as e:
            self.handle_error(e, "consolidate_system_metrics")
            return {}
    
    def calculate_system_health(self) -> Dict:
        """
        Calcula saúde geral do sistema
        
        Returns:
            Dict: Métricas de saúde do sistema
        """
        try:
            total_agents = len(self.agents_status)
            if total_agents == 0:
                return {"status": "unknown", "score": 0}
            
            # Contar agentes por status
            status_counts = {}
            for agent_status in self.agents_status.values():
                status = agent_status["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Calcular score de saúde
            health_score = 0
            
            # Agentes funcionando bem
            healthy_statuses = ["completed", "running"]
            healthy_count = sum(status_counts.get(status, 0) for status in healthy_statuses)
            health_score += (healthy_count / total_agents) * 60
            
            # Penalizar falhas
            failed_count = status_counts.get("failed", 0) + status_counts.get("error", 0) + status_counts.get("timeout", 0)
            health_score -= (failed_count / total_agents) * 30
            
            # Bonificar por baixas falhas consecutivas
            avg_consecutive_failures = sum(a["consecutive_failures"] for a in self.agents_status.values()) / total_agents
            if avg_consecutive_failures < 1:
                health_score += 20
            elif avg_consecutive_failures < 2:
                health_score += 10
            
            # Bonificar por alta taxa de sucesso
            total_runs = sum(a["total_runs"] for a in self.agents_status.values())
            total_successes = sum(a["total_successes"] for a in self.agents_status.values())
            
            if total_runs > 0:
                success_rate = total_successes / total_runs
                health_score += success_rate * 20
            
            # Normalizar score
            health_score = max(0, min(100, health_score))
            
            # Determinar status
            if health_score >= 80:
                status = "excellent"
            elif health_score >= 60:
                status = "good"
            elif health_score >= 40:
                status = "fair"
            else:
                status = "poor"
            
            return {
                "status": status,
                "score": round(health_score, 1),
                "status_counts": status_counts,
                "healthy_agents": healthy_count,
                "failed_agents": failed_count,
                "avg_consecutive_failures": round(avg_consecutive_failures, 1),
                "success_rate": round(total_successes / total_runs if total_runs > 0 else 0, 3)
            }
            
        except Exception as e:
            self.handle_error(e, "calculate_system_health")
            return {"status": "error", "score": 0}
    
    def calculate_system_uptime(self) -> Dict:
        """
        Calcula uptime do sistema
        
        Returns:
            Dict: Informações de uptime
        """
        try:
            # Para demonstração, simular uptime baseado no histórico
            if not self.execution_history:
                return {"uptime_hours": 0, "start_time": datetime.now().isoformat()}
            
            first_execution = min(self.execution_history, key=lambda x: x["timestamp"])
            start_time = datetime.fromisoformat(first_execution["timestamp"])
            uptime_seconds = (datetime.now() - start_time).total_seconds()
            uptime_hours = uptime_seconds / 3600
            
            return {
                "uptime_hours": round(uptime_hours, 2),
                "uptime_days": round(uptime_hours / 24, 2),
                "start_time": start_time.isoformat(),
                "total_executions": len(self.execution_history)
            }
            
        except Exception as e:
            self.handle_error(e, "calculate_system_uptime")
            return {"uptime_hours": 0}
    
    def handle_agent_failure(self, agent_name: str, failure_info: Dict):
        """
        Trata falha de um agente
        
        Args:
            agent_name: Nome do agente que falhou
            failure_info: Informações sobre a falha
        """
        try:
            consecutive_failures = self.agents_status[agent_name]["consecutive_failures"]
            max_failures = self.agents_config["system"]["emergency_shutdown_threshold"]
            
            self.logger.warning(f"Agente {agent_name} falhou ({consecutive_failures}/{max_failures})")
            
            # Salvar alerta de falha
            alert = {
                "type": "agent_failure",
                "severity": AlertSeverity.HIGH,
                "agent_name": agent_name,
                "consecutive_failures": consecutive_failures,
                "failure_info": failure_info,
                "timestamp": datetime.now().isoformat(),
                "action_required": "Investigar causa da falha e corrigir"
            }
            
            self.save_alert(alert)
            
            # Se muitas falhas consecutivas, desabilitar agente temporariamente
            if consecutive_failures >= max_failures:
                self.logger.critical(f"Agente {agent_name} desabilitado após {consecutive_failures} falhas consecutivas")
                
                # Salvar alerta crítico
                critical_alert = {
                    "type": "agent_disabled",
                    "severity": AlertSeverity.CRITICAL,
                    "agent_name": agent_name,
                    "reason": f"Muitas falhas consecutivas ({consecutive_failures})",
                    "timestamp": datetime.now().isoformat(),
                    "action_required": "Revisar logs e corrigir problema antes de reativar"
                }
                
                self.save_alert(critical_alert)
            
        except Exception as e:
            self.handle_error(e, "handle_agent_failure")
    
    def analyze_performance(self) -> Dict:
        """
        Analisa performance do sistema orquestrador
        
        Returns:
            Dict: Métricas de performance
        """
        try:
            # Consolidar métricas do sistema
            system_metrics = self.consolidate_system_metrics()
            
            # Estatísticas de execução
            recent_executions = self.execution_history[-100:]  # Últimas 100 execuções
            
            if recent_executions:
                success_count = len([e for e in recent_executions if e["result"]["status"] == "success"])
                success_rate = success_count / len(recent_executions)
                
                avg_execution_time = sum(e["result"].get("execution_time", 0) for e in recent_executions) / len(recent_executions)
            else:
                success_rate = 0
                avg_execution_time = 0
            
            performance = {
                "system_metrics": system_metrics,
                "orchestrator_stats": {
                    "total_executions": len(self.execution_history),
                    "recent_success_rate": round(success_rate, 3),
                    "avg_execution_time": round(avg_execution_time, 2),
                    "active_monitoring_threads": len(self.monitoring_threads),
                    "task_queue_size": self.task_queue.qsize()
                },
                "system_health": system_metrics.get("system_health", {}),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return performance
            
        except Exception as e:
            self.handle_error(e, "analyze_performance")
            return {"status": "error", "message": str(e)}
    
    def suggest_improvements(self) -> List[Dict]:
        """
        Sugere melhorias no sistema de orquestração
        
        Returns:
            List[Dict]: Lista de sugestões
        """
        try:
            suggestions = []
            performance = self.analyze_performance()
            
            system_health = performance.get("system_health", {})
            health_score = system_health.get("score", 0)
            
            # Sugestão 1: Melhorar saúde do sistema se baixa
            if health_score < 60:
                failed_agents = system_health.get("failed_agents", 0)
                
                suggestions.append({
                    "type": SuggestionType.SYSTEM_MAINTENANCE,
                    "priority": "critical",
                    "current_metrics": system_health,
                    "suggested_changes": {
                        "file": "config/agents_config.json",
                        "line_range": [1, 100],
                        "parameter": "system.restart_failed_agents",
                        "current_value": True,
                        "suggested_value": True,
                        "reason": f"Saúde do sistema baixa ({health_score:.1f}/100) com {failed_agents} agentes falhando",
                        "expected_improvement": "Reinicialização automática de agentes falhando"
                    }
                })
            
            # Sugestão 2: Ajustar timeouts se muitos timeouts
            orchestrator_stats = performance.get("orchestrator_stats", {})
            avg_execution_time = orchestrator_stats.get("avg_execution_time", 0)
            
            if avg_execution_time > 200:  # Mais de 3 minutos em média
                suggestions.append({
                    "type": SuggestionType.PARAMETER_ADJUSTMENT,
                    "priority": "medium",
                    "current_metrics": {"avg_execution_time": avg_execution_time},
                    "suggested_changes": {
                        "file": "config/agents_config.json",
                        "line_range": [10, 50],
                        "parameter": "agents.*.timeout",
                        "current_value": 300,
                        "suggested_value": 450,
                        "reason": f"Tempo médio de execução alto ({avg_execution_time:.1f}s) - aumentar timeouts",
                        "expected_improvement": "Reduzir falhas por timeout"
                    }
                })
            
            # Sugestão 3: Otimizar concorrência
            max_concurrent = self.agents_config["system"]["max_concurrent_agents"]
            if health_score > 80 and max_concurrent < 5:
                suggestions.append({
                    "type": SuggestionType.PERFORMANCE_OPTIMIZATION,
                    "priority": "low",
                    "current_metrics": {"health_score": health_score},
                    "suggested_changes": {
                        "file": "config/agents_config.json",
                        "line_range": [80, 85],
                        "parameter": "system.max_concurrent_agents",
                        "current_value": max_concurrent,
                        "suggested_value": max_concurrent + 1,
                        "reason": f"Sistema saudável ({health_score:.1f}/100) - aumentar concorrência",
                        "expected_improvement": "Melhorar throughput do sistema"
                    }
                })
            
            return suggestions
            
        except Exception as e:
            self.handle_error(e, "suggest_improvements")
            return []
    
    def run_orchestration_cycle(self):
        """Executa um ciclo de orquestração"""
        try:
            # Verificar próximo agente a executar
            next_agent = self.get_next_agent_to_execute()
            
            if next_agent:
                self.logger.debug(f"Executando agente: {next_agent}")
                
                # Executar agente
                result = self.execute_agent(next_agent)
                
                # Registrar execução
                execution_record = {
                    "timestamp": datetime.now().isoformat(),
                    "agent": next_agent,
                    "result": result
                }
                
                self.execution_history.append(execution_record)
                
                # Manter histórico limitado
                if len(self.execution_history) > 1000:
                    self.execution_history = self.execution_history[-1000:]
                
                # Tratar falhas se necessário
                if result["status"] in ["failed", "error", "timeout"]:
                    self.handle_agent_failure(next_agent, result)
            
            # Consolidar métricas periodicamente
            if len(self.execution_history) % 10 == 0:  # A cada 10 execuções
                self.system_metrics = self.consolidate_system_metrics()
                self.save_metrics(self.system_metrics)
            
        except Exception as e:
            self.handle_error(e, "run_orchestration_cycle")
    
    def run(self):
        """
        Executa loop principal do orquestrador
        """
        self.logger.info("Iniciando orquestrador do sistema")
        
        try:
            # Inicializar status dos agentes
            self.initialize_agents_status()
            
            # Loop principal
            cycle_count = 0
            while self.system_active:
                cycle_count += 1
                
                # Executar ciclo de orquestração
                self.run_orchestration_cycle()
                
                # Análise de performance periódica
                if cycle_count % 60 == 0:  # A cada 60 ciclos
                    performance = self.analyze_performance()
                    self.save_metrics(performance)
                    
                    suggestions = self.suggest_improvements()
                    for suggestion in suggestions:
                        self.save_suggestion(suggestion)
                    
                    # Log de status
                    health = performance.get("system_health", {})
                    self.logger.info(
                        f"Sistema - Saúde: {health.get('status', 'unknown')} "
                        f"({health.get('score', 0):.1f}/100), "
                        f"Agentes ativos: {health.get('healthy_agents', 0)}/{health.get('healthy_agents', 0) + health.get('failed_agents', 0)}"
                    )
                
                # Pausa entre ciclos
                time.sleep(30)  # 30 segundos entre ciclos
                
        except KeyboardInterrupt:
            self.logger.info("Orquestrador interrompido pelo usuário")
            self.system_active = False
        except Exception as e:
            self.handle_error(e, "run")
            raise

def main():
    """Função principal para execução standalone"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo de teste - executar apenas alguns ciclos
        orchestrator = OrchestratorAgent()
        print("Executando teste do OrchestratorAgent...")
        
        orchestrator.initialize_agents_status()
        
        # Executar alguns ciclos de teste
        for i in range(3):
            print(f"Ciclo de teste {i+1}/3")
            orchestrator.run_orchestration_cycle()
            time.sleep(2)
        
        print("Teste concluído com sucesso!")
    else:
        # Execução normal - loop contínuo
        orchestrator = OrchestratorAgent()
        orchestrator.run_with_error_handling()

if __name__ == "__main__":
    main()

