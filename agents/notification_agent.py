#!/usr/bin/env python3
"""
Notification Agent para Sistema de Scalping Automatizado
Responsável por alertas, notificações e relatórios de comunicação
Autor: Manus AI
Data: 17 de Julho de 2025
"""

import json
import os
import sys
import time
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Adicionar diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, SuggestionType, AlertSeverity

class NotificationAgent(BaseAgent):
    """
    Agente de Notificações
    
    Responsabilidades:
    - Envio de notificações via Telegram, Discord e Email
    - Processamento de alertas de outros agentes
    - Geração de relatórios periódicos
    - Dashboard web em tempo real
    - Integração com sistemas de monitoramento externos
    
    Frequência: Event-driven via PowerShell
    """
    
    def __init__(self):
        super().__init__("NotificationAgent")
        
        # Configurações de notificação
        self.notification_config = self.load_notification_config()
        
        # Histórico de notificações enviadas
        self.notification_history = []
        self.max_history_size = 1000
        
        # Cache de templates de mensagem
        self.message_templates = self.load_message_templates()
        
        # Estatísticas de envio
        self.send_stats = {
            "total_sent": 0,
            "sent_by_channel": {},
            "failed_sends": 0,
            "last_send_time": None
        }
        
        self.logger.info("NotificationAgent inicializado")
    
    def load_notification_config(self) -> Dict:
        """Carrega configuração de notificações"""
        try:
            config_file = "config/notification_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        
        # Configuração padrão
        return {
            "channels": {
                "telegram": {
                    "enabled": False,
                    "bot_token_env": "TELEGRAM_BOT_TOKEN",
                    "chat_id_env": "TELEGRAM_CHAT_ID",
                    "rate_limit_seconds": 1
                },
                "discord": {
                    "enabled": False,
                    "webhook_url_env": "DISCORD_WEBHOOK_URL",
                    "rate_limit_seconds": 1
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username_env": "EMAIL_USERNAME",
                    "password_env": "EMAIL_PASSWORD",
                    "to_email_env": "EMAIL_TO",
                    "rate_limit_seconds": 60
                }
            },
            "alert_routing": {
                "critical": ["telegram", "discord", "email"],
                "high": ["telegram", "discord"],
                "medium": ["telegram"],
                "low": []
            },
            "report_schedule": {
                "daily_summary": {"enabled": True, "time": "18:00"},
                "weekly_report": {"enabled": True, "day": "sunday", "time": "09:00"},
                "monthly_report": {"enabled": True, "day": 1, "time": "09:00"}
            }
        }
    
    def load_message_templates(self) -> Dict:
        """Carrega templates de mensagens"""
        return {
            "signal_alert": {
                "title": "🎯 Novo Sinal de Trading",
                "template": """
🎯 **Novo Sinal de Trading**

📊 **Símbolo**: {symbol}
🔔 **Sinal**: {signal}
📈 **Confiança**: {confidence:.1%}
💰 **Preço**: ${price:,.2f}
⏰ **Timestamp**: {timestamp}

📋 **Estratégias**:
{strategies}

🎲 **Scores**:
• Compra: {buy_score:.2f}
• Venda: {sell_score:.2f}
• Hold: {hold_score:.2f}
                """
            },
            "risk_alert": {
                "title": "⚠️ Alerta de Risco",
                "template": """
⚠️ **Alerta de Risco - {severity}**

🚨 **Tipo**: {alert_type}
📊 **Valor Atual**: {current_value}
🎯 **Limite**: {limit}
📝 **Mensagem**: {message}

⚡ **Ação Necessária**: {action_required}
⏰ **Timestamp**: {timestamp}
                """
            },
            "performance_report": {
                "title": "📊 Relatório de Performance",
                "template": """
📊 **Relatório de Performance Diário**

💰 **Portfolio**: ${portfolio_value:,.2f}
📈 **P&L Hoje**: {daily_pnl:+.2%}
📉 **Drawdown**: {drawdown:.2%}

🎯 **Trading**:
• Win Rate: {win_rate:.1%}
• Total Trades: {total_trades}
• Profit Factor: {profit_factor:.2f}

🤖 **Sistema**:
• Agentes Ativos: {active_agents}
• Alertas: {active_alerts}
• Última Atualização: {last_update}
                """
            },
            "system_status": {
                "title": "🖥️ Status do Sistema",
                "template": """
🖥️ **Status do Sistema**

🟢 **Status Geral**: {overall_status}
🤖 **Agentes**: {active_agents}/{total_agents} ativos

📊 **Agentes Detalhados**:
{agent_details}

⚠️ **Problemas**: {issues_count}
⏰ **Última Verificação**: {last_check}
                """
            }
        }
    
    def send_telegram_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Envia mensagem via Telegram
        
        Args:
            message: Texto da mensagem
            parse_mode: Modo de parsing (Markdown/HTML)
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            config = self.notification_config["channels"]["telegram"]
            if not config["enabled"]:
                return False
            
            bot_token = os.getenv(config["bot_token_env"])
            chat_id = os.getenv(config["chat_id_env"])
            
            if not bot_token or not chat_id:
                self.logger.warning("Telegram credentials não configuradas")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.debug("Mensagem Telegram enviada com sucesso")
                return True
            else:
                self.logger.error(f"Erro ao enviar Telegram: {response.status_code}")
                return False
                
        except Exception as e:
            self.handle_error(e, "send_telegram_message")
            return False
    
    def send_discord_message(self, message: str) -> bool:
        """
        Envia mensagem via Discord webhook
        
        Args:
            message: Texto da mensagem
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            config = self.notification_config["channels"]["discord"]
            if not config["enabled"]:
                return False
            
            webhook_url = os.getenv(config["webhook_url_env"])
            
            if not webhook_url:
                self.logger.warning("Discord webhook não configurado")
                return False
            
            payload = {
                "content": message,
                "username": "Scalping Bot"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                self.logger.debug("Mensagem Discord enviada com sucesso")
                return True
            else:
                self.logger.error(f"Erro ao enviar Discord: {response.status_code}")
                return False
                
        except Exception as e:
            self.handle_error(e, "send_discord_message")
            return False
    
    def send_email(self, subject: str, message: str) -> bool:
        """
        Envia email
        
        Args:
            subject: Assunto do email
            message: Corpo da mensagem
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            config = self.notification_config["channels"]["email"]
            if not config["enabled"]:
                return False
            
            username = os.getenv(config["username_env"])
            password = os.getenv(config["password_env"])
            to_email = os.getenv(config["to_email_env"])
            
            if not all([username, password, to_email]):
                self.logger.warning("Email credentials não configuradas")
                return False
            
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Enviar email
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
            server.login(username, password)
            
            text = msg.as_string()
            server.sendmail(username, to_email, text)
            server.quit()
            
            self.logger.debug("Email enviado com sucesso")
            return True
            
        except Exception as e:
            self.handle_error(e, "send_email")
            return False
    
    def send_notification(self, title: str, message: str, channels: List[str], severity: str = "medium") -> Dict:
        """
        Envia notificação para canais especificados
        
        Args:
            title: Título da notificação
            message: Corpo da mensagem
            channels: Lista de canais para enviar
            severity: Severidade da notificação
            
        Returns:
            Dict: Resultado do envio
        """
        results = {
            "sent_channels": [],
            "failed_channels": [],
            "total_sent": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Formatar mensagem completa
            full_message = f"{title}\n\n{message}"
            
            for channel in channels:
                success = False
                
                if channel == "telegram":
                    success = self.send_telegram_message(full_message)
                elif channel == "discord":
                    success = self.send_discord_message(full_message)
                elif channel == "email":
                    success = self.send_email(title, message)
                
                if success:
                    results["sent_channels"].append(channel)
                    results["total_sent"] += 1
                    
                    # Atualizar estatísticas
                    self.send_stats["sent_by_channel"][channel] = self.send_stats["sent_by_channel"].get(channel, 0) + 1
                else:
                    results["failed_channels"].append(channel)
                    self.send_stats["failed_sends"] += 1
                
                # Rate limiting
                channel_config = self.notification_config["channels"].get(channel, {})
                rate_limit = channel_config.get("rate_limit_seconds", 1)
                time.sleep(rate_limit)
            
            # Atualizar estatísticas gerais
            self.send_stats["total_sent"] += results["total_sent"]
            self.send_stats["last_send_time"] = datetime.now().isoformat()
            
            # Salvar no histórico
            notification_record = {
                "title": title,
                "message": message,
                "channels": channels,
                "severity": severity,
                "results": results
            }
            
            self.notification_history.append(notification_record)
            
            # Manter tamanho do histórico
            if len(self.notification_history) > self.max_history_size:
                self.notification_history = self.notification_history[-self.max_history_size:]
            
            self.logger.info(f"Notificação enviada: {results['total_sent']}/{len(channels)} canais")
            
            return results
            
        except Exception as e:
            self.handle_error(e, "send_notification")
            return results
    
    def process_signal_alert(self, signal: Dict):
        """
        Processa alerta de novo sinal de trading
        
        Args:
            signal: Dados do sinal
        """
        try:
            # Verificar se deve notificar (apenas sinais BUY/SELL com alta confiança)
            if signal.get("signal") == "HOLD" or signal.get("confidence", 0) < 0.7:
                return
            
            template = self.message_templates["signal_alert"]
            
            # Formatar estratégias
            strategies_text = ""
            for individual in signal.get("individual_signals", []):
                strategies_text += f"• {individual['strategy']}: {individual['signal']} ({individual['confidence']:.1%})\n"
            
            # Formatar mensagem
            message = template["template"].format(
                symbol=signal.get("symbol", "N/A"),
                signal=signal.get("signal", "N/A"),
                confidence=signal.get("confidence", 0),
                price=signal.get("price", 0),
                timestamp=signal.get("timestamp", "N/A"),
                strategies=strategies_text.strip(),
                buy_score=signal.get("scores", {}).get("buy_score", 0),
                sell_score=signal.get("scores", {}).get("sell_score", 0),
                hold_score=signal.get("scores", {}).get("hold_score", 0)
            )
            
            # Determinar canais baseado na confiança
            if signal.get("confidence", 0) > 0.8:
                channels = self.notification_config["alert_routing"]["high"]
            else:
                channels = self.notification_config["alert_routing"]["medium"]
            
            self.send_notification(template["title"], message, channels, "medium")
            
        except Exception as e:
            self.handle_error(e, "process_signal_alert")
    
    def process_risk_alert(self, alert: Dict):
        """
        Processa alerta de risco
        
        Args:
            alert: Dados do alerta de risco
        """
        try:
            template = self.message_templates["risk_alert"]
            
            # Mapear severidade
            severity_map = {
                AlertSeverity.CRITICAL: "CRÍTICO",
                AlertSeverity.HIGH: "ALTO",
                AlertSeverity.MEDIUM: "MÉDIO",
                AlertSeverity.LOW: "BAIXO"
            }
            
            severity = alert.get("severity", AlertSeverity.MEDIUM)
            severity_text = severity_map.get(severity, "MÉDIO")
            
            # Formatar mensagem
            message = template["template"].format(
                severity=severity_text,
                alert_type=alert.get("type", "N/A"),
                current_value=alert.get("current_value", "N/A"),
                limit=alert.get("limit", "N/A"),
                message=alert.get("message", "N/A"),
                action_required=alert.get("action_required", "Monitorar situação"),
                timestamp=alert.get("timestamp", datetime.now().isoformat())
            )
            
            # Determinar canais baseado na severidade
            channels = self.notification_config["alert_routing"].get(severity, ["telegram"])
            
            self.send_notification(template["title"], message, channels, severity)
            
        except Exception as e:
            self.handle_error(e, "process_risk_alert")
    
    def generate_performance_report(self) -> str:
        """
        Gera relatório de performance
        
        Returns:
            str: Relatório formatado
        """
        try:
            # Carregar métricas atuais
            metrics_file = "data/metrics/current.json"
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
            else:
                metrics = {}
            
            # Carregar status do sistema
            system_status = self.load_system_status()
            
            template = self.message_templates["performance_report"]
            
            # Dados padrão se não disponíveis
            portfolio_value = metrics.get("portfolio_value", 10000)
            daily_pnl = metrics.get("daily_pnl", 0)
            drawdown = metrics.get("current_drawdown", 0)
            win_rate = metrics.get("simulated_win_rate", 0)
            total_trades = metrics.get("total_trades", 0)
            profit_factor = metrics.get("profit_factor", 1.0)
            
            active_agents = len([a for a in system_status.get("agents", {}).values() if a.get("status") == "running"])
            active_alerts = metrics.get("active_alerts", 0)
            
            message = template["template"].format(
                portfolio_value=portfolio_value,
                daily_pnl=daily_pnl,
                drawdown=drawdown,
                win_rate=win_rate,
                total_trades=total_trades,
                profit_factor=profit_factor,
                active_agents=active_agents,
                active_alerts=active_alerts,
                last_update=datetime.now().strftime("%H:%M:%S")
            )
            
            return message
            
        except Exception as e:
            self.handle_error(e, "generate_performance_report")
            return "Erro ao gerar relatório de performance"
    
    def generate_system_status_report(self) -> str:
        """
        Gera relatório de status do sistema
        
        Returns:
            str: Relatório formatado
        """
        try:
            system_status = self.load_system_status()
            template = self.message_templates["system_status"]
            
            # Processar detalhes dos agentes
            agent_details = ""
            agents = system_status.get("agents", {})
            active_count = 0
            
            for agent_name, agent_info in agents.items():
                status = agent_info.get("status", "unknown")
                if status == "running":
                    status_icon = "🟢"
                    active_count += 1
                elif status == "error":
                    status_icon = "🔴"
                else:
                    status_icon = "🟡"
                
                last_run = agent_info.get("last_run", "N/A")
                if last_run != "N/A":
                    try:
                        last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
                        last_run = last_run_dt.strftime("%H:%M:%S")
                    except:
                        pass
                
                agent_details += f"{status_icon} {agent_name}: {status} (última: {last_run})\n"
            
            # Contar problemas
            issues = system_status.get("issues", [])
            issues_count = len(issues)
            
            message = template["template"].format(
                overall_status=system_status.get("overall_status", "unknown").upper(),
                active_agents=active_count,
                total_agents=len(agents),
                agent_details=agent_details.strip(),
                issues_count=issues_count,
                last_check=datetime.now().strftime("%H:%M:%S")
            )
            
            return message
            
        except Exception as e:
            self.handle_error(e, "generate_system_status_report")
            return "Erro ao gerar relatório de status"
    
    def process_pending_alerts(self):
        """Processa alertas pendentes de outros agentes"""
        try:
            alerts_dir = Path("data/alerts")
            if not alerts_dir.exists():
                return
            
            # Processar arquivos de alerta
            for alert_file in alerts_dir.glob("*.json"):
                try:
                    with open(alert_file, 'r', encoding='utf-8') as f:
                        alert = json.load(f)
                    
                    # Verificar se já foi processado
                    if alert.get("processed", False):
                        continue
                    
                    # Processar baseado no tipo
                    alert_type = alert.get("type", "")
                    
                    if "risk" in alert_type or "drawdown" in alert_type or "loss" in alert_type:
                        self.process_risk_alert(alert)
                    
                    # Marcar como processado
                    alert["processed"] = True
                    alert["processed_at"] = datetime.now().isoformat()
                    
                    with open(alert_file, 'w', encoding='utf-8') as f:
                        json.dump(alert, f, indent=2)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar alerta {alert_file}: {e}")
                    continue
            
        except Exception as e:
            self.handle_error(e, "process_pending_alerts")
    
    def process_new_signals(self):
        """Processa novos sinais para notificação"""
        try:
            signals_dir = Path("data/signals")
            if not signals_dir.exists():
                return
            
            # Processar apenas sinais dos últimos 10 minutos
            cutoff_time = datetime.now() - timedelta(minutes=10)
            
            for signal_file in signals_dir.glob("*.json"):
                try:
                    # Verificar idade do arquivo
                    file_time = datetime.fromtimestamp(signal_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        continue
                    
                    with open(signal_file, 'r', encoding='utf-8') as f:
                        signal = json.load(f)
                    
                    # Verificar se já foi notificado
                    if signal.get("notified", False):
                        continue
                    
                    # Processar sinal
                    self.process_signal_alert(signal)
                    
                    # Marcar como notificado
                    signal["notified"] = True
                    signal["notified_at"] = datetime.now().isoformat()
                    
                    with open(signal_file, 'w', encoding='utf-8') as f:
                        json.dump(signal, f, indent=2)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar sinal {signal_file}: {e}")
                    continue
            
        except Exception as e:
            self.handle_error(e, "process_new_signals")
    
    def analyze_performance(self) -> Dict:
        """
        Analisa performance do sistema de notificações
        
        Returns:
            Dict: Métricas de performance
        """
        try:
            # Estatísticas de envio
            recent_notifications = self.notification_history[-100:]  # Últimas 100
            
            success_rate = 0
            if recent_notifications:
                successful = sum(1 for n in recent_notifications if n["results"]["total_sent"] > 0)
                success_rate = successful / len(recent_notifications)
            
            # Estatísticas por canal
            channel_stats = {}
            for channel in ["telegram", "discord", "email"]:
                sent_count = self.send_stats["sent_by_channel"].get(channel, 0)
                channel_stats[channel] = {
                    "sent_count": sent_count,
                    "enabled": self.notification_config["channels"][channel]["enabled"]
                }
            
            performance = {
                "total_notifications_sent": self.send_stats["total_sent"],
                "failed_sends": self.send_stats["failed_sends"],
                "success_rate": round(success_rate, 3),
                "channel_stats": channel_stats,
                "recent_notifications_count": len(recent_notifications),
                "last_send_time": self.send_stats["last_send_time"],
                "notification_history_size": len(self.notification_history),
                "last_analysis": datetime.now().isoformat()
            }
            
            return performance
            
        except Exception as e:
            self.handle_error(e, "analyze_performance")
            return {"status": "error", "message": str(e)}
    
    def suggest_improvements(self) -> List[Dict]:
        """
        Sugere melhorias no sistema de notificações
        
        Returns:
            List[Dict]: Lista de sugestões
        """
        try:
            suggestions = []
            performance = self.analyze_performance()
            
            # Sugestão 1: Ativar canais se taxa de sucesso baixa
            if performance.get("success_rate", 0) < 0.8:
                disabled_channels = [
                    ch for ch, stats in performance["channel_stats"].items()
                    if not stats["enabled"]
                ]
                
                if disabled_channels:
                    suggestions.append({
                        "type": SuggestionType.CONFIGURATION_UPDATE,
                        "priority": "medium",
                        "current_metrics": {"success_rate": performance["success_rate"]},
                        "suggested_changes": {
                            "file": "config/notification_config.json",
                            "line_range": [5, 20],
                            "parameter": f"channels.{disabled_channels[0]}.enabled",
                            "current_value": False,
                            "suggested_value": True,
                            "reason": f"Taxa de sucesso {performance['success_rate']:.1%} baixa - ativar canal adicional",
                            "expected_improvement": "Redundância e maior confiabilidade nas notificações"
                        }
                    })
            
            # Sugestão 2: Ajustar rate limiting se muitas falhas
            if performance.get("failed_sends", 0) > 10:
                suggestions.append({
                    "type": SuggestionType.PARAMETER_ADJUSTMENT,
                    "priority": "low",
                    "current_metrics": {"failed_sends": performance["failed_sends"]},
                    "suggested_changes": {
                        "file": "config/notification_config.json",
                        "line_range": [10, 15],
                        "parameter": "channels.telegram.rate_limit_seconds",
                        "current_value": 1,
                        "suggested_value": 2,
                        "reason": f"{performance['failed_sends']} envios falharam - aumentar rate limiting",
                        "expected_improvement": "Reduzir falhas por rate limiting da API"
                    }
                })
            
            return suggestions
            
        except Exception as e:
            self.handle_error(e, "suggest_improvements")
            return []
    
    def run(self):
        """
        Executa ciclo principal do agente de notificações
        """
        self.logger.info("Iniciando ciclo de notificações")
        
        try:
            # Processar alertas pendentes
            self.process_pending_alerts()
            
            # Processar novos sinais
            self.process_new_signals()
            
            # Verificar se deve enviar relatórios periódicos
            now = datetime.now()
            
            # Relatório diário (exemplo: 18:00)
            if now.hour == 18 and now.minute < 5:  # Janela de 5 minutos
                report = self.generate_performance_report()
                self.send_notification(
                    "📊 Relatório Diário",
                    report,
                    ["telegram"],
                    "low"
                )
            
            # Status do sistema a cada hora
            if now.minute < 5:  # Primeiros 5 minutos de cada hora
                status_report = self.generate_system_status_report()
                self.send_notification(
                    "🖥️ Status do Sistema",
                    status_report,
                    ["telegram"],
                    "low"
                )
            
            # Analisar performance e gerar sugestões
            performance = self.analyze_performance()
            self.save_metrics(performance)
            
            suggestions = self.suggest_improvements()
            for suggestion in suggestions:
                self.save_suggestion(suggestion)
            
            self.logger.info(
                f"Ciclo de notificações concluído - "
                f"Enviadas: {self.send_stats['total_sent']}, "
                f"Falhas: {self.send_stats['failed_sends']}"
            )
            
        except Exception as e:
            self.handle_error(e, "run")
            raise

def main():
    """Função principal para execução standalone"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo de teste
        agent = NotificationAgent()
        print("Executando teste do NotificationAgent...")
        agent.run()
        print("Teste concluído com sucesso!")
    else:
        # Execução normal
        agent = NotificationAgent()
        agent.run_with_error_handling()

if __name__ == "__main__":
    main()

