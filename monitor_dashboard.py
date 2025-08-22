#!/usr/bin/env python3
"""
Dashboard de Monitoramento para Cloud Data Orchestrator
Interface simples para visualizar status e métricas do sistema
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_system import IntegratedSystem

class MonitorDashboard:
    """Dashboard de monitoramento do sistema"""
    
    def __init__(self):
        self.system = IntegratedSystem()
        self.refresh_interval = 5  # segundos
    
    def display_header(self):
        """Exibe cabeçalho do dashboard"""
        print("\n" + "=" * 80)
        print("🚀 CLOUD DATA ORCHESTRATOR - DASHBOARD DE MONITORAMENTO")
        print("=" * 80)
        print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔄 Atualização automática a cada {self.refresh_interval} segundos")
        print("=" * 80)
    
    def display_health_status(self):
        """Exibe status de saúde do sistema"""
        print("\n🏥 STATUS DE SAÚDE DO SISTEMA")
        print("-" * 50)
        
        try:
            health_status = self.system.run_health_check()
            overall_status = health_status['status']
            
            # Emoji baseado no status
            status_emoji = "✅" if overall_status == "healthy" else "❌" if overall_status == "error" else "⚠️"
            
            print(f"{status_emoji} Status Geral: {overall_status.upper()}")
            
            # Detalhes dos health checks
            for check_name, check_result in health_status['checks'].items():
                check_emoji = "✅" if check_result['status'] else "❌"
                print(f"  {check_emoji} {check_name}: {'Saudável' if check_result['status'] else 'Problema'}")
                
        except Exception as e:
            print(f"❌ Erro ao verificar saúde: {e}")
    
    def display_metrics_summary(self):
        """Exibe resumo das métricas"""
        print("\n📊 RESUMO DE MÉTRICAS")
        print("-" * 50)
        
        try:
            system_status = self.system.get_system_status()
            metrics = system_status['metrics']
            
            # Contar métricas por tipo
            metric_counts = {}
            for metric in metrics:
                metric_type = metric.get('type', 'unknown')
                metric_counts[metric_type] = metric_counts.get(metric_type, 0) + 1
            
            print(f"📈 Total de métricas: {len(metrics)}")
            for metric_type, count in metric_counts.items():
                print(f"  • {metric_type}: {count}")
            
            # Cache stats
            cache_stats = system_status['cache_stats']
            print(f"\n💾 CACHE:")
            print(f"  • Hits: {cache_stats['hits']}")
            print(f"  • Misses: {cache_stats['misses']}")
            print(f"  • Taxa de acerto: {cache_stats['hit_rate']}%")
            print(f"  • Tamanho atual: {cache_stats['size']}/{cache_stats['max_size']}")
            
        except Exception as e:
            print(f"❌ Erro ao obter métricas: {e}")
    
    def display_resilience_status(self):
        """Exibe status dos componentes de resiliência"""
        print("\n🛡️ STATUS DE RESILIÊNCIA")
        print("-" * 50)
        
        try:
            system_status = self.system.get_system_status()
            resilience_status = system_status['resilience_status']
            
            # Circuit breakers
            print("🔌 CIRCUIT BREAKERS:")
            for name, cb_status in resilience_status['circuit_breakers'].items():
                state_emoji = {
                    'closed': '🟢',
                    'open': '🔴',
                    'half_open': '🟡'
                }.get(cb_status['state'], '❓')
                
                print(f"  {state_emoji} {name}: {cb_status['state']}")
                print(f"    • Falhas: {cb_status['failure_count']}/{cb_status['failure_threshold']}")
                print(f"    • Sucessos: {cb_status['success_count']}")
            
            # Retry handlers
            print("\n🔄 RETRY HANDLERS:")
            for name, rh_status in resilience_status['retry_handlers'].items():
                print(f"  • {name}: {rh_status['max_attempts']} tentativas máximas")
            
        except Exception as e:
            print(f"❌ Erro ao obter status de resiliência: {e}")
    
    def display_config_summary(self):
        """Exibe resumo das configurações"""
        print("\n⚙️ CONFIGURAÇÕES DO SISTEMA")
        print("-" * 50)
        
        try:
            system_status = self.system.get_system_status()
            config_summary = system_status['config_summary']
            
            print(f"🌍 Região AWS: {config_summary['aws_region']}")
            print(f"🏗️ Ambiente: {config_summary['environment']}")
            print(f"🐛 Debug Mode: {'Ativado' if config_summary['debug_mode'] else 'Desativado'}")
            
        except Exception as e:
            print(f"❌ Erro ao obter configurações: {e}")
    
    def display_recent_activity(self):
        """Exibe atividade recente"""
        print("\n🕒 ATIVIDADE RECENTE")
        print("-" * 50)
        
        try:
            # Verificar dados em cache
            cache = self.system.cache
            recent_keys = [key for key in cache.keys() if key.startswith('data_')]
            
            if recent_keys:
                print(f"📦 Dados recentes em cache: {len(recent_keys)} tipos")
                for key in sorted(recent_keys, reverse=True)[:3]:  # Últimos 3
                    data = cache.get(key)
                    if data and isinstance(data, dict):
                        count = data.get('count', 0)
                        print(f"  • {key}: {count} registros")
            else:
                print("📭 Nenhum dado recente encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao verificar atividade: {e}")
    
    def display_actions_menu(self):
        """Exibe menu de ações disponíveis"""
        print("\n🎯 AÇÕES DISPONÍVEIS")
        print("-" * 50)
        print("1. 🔄 Executar pipeline de coleta")
        print("2. 🧹 Executar manutenção")
        print("3. 📊 Atualizar dashboard")
        print("4. 🚪 Sair")
        print("-" * 50)
    
    def execute_action(self, action: str):
        """Executa ação selecionada"""
        if action == "1":
            print("\n🔄 Executando pipeline de coleta...")
            try:
                result = self.system.run_data_collection_pipeline()
                if result['success']:
                    print(f"✅ Pipeline executado com sucesso em {result['duration']:.2f}s")
                else:
                    print(f"❌ Pipeline falhou: {result['error']}")
            except Exception as e:
                print(f"❌ Erro: {e}")
                
        elif action == "2":
            print("\n🔧 Executando manutenção...")
            try:
                result = self.system.run_maintenance()
                print("✅ Manutenção concluída")
            except Exception as e:
                print(f"❌ Erro: {e}")
                
        elif action == "3":
            print("\n📊 Atualizando dashboard...")
            return  # Sair do loop para atualizar
            
        elif action == "4":
            print("\n👋 Saindo do dashboard...")
            sys.exit(0)
            
        else:
            print("❌ Ação inválida!")
    
    def run_dashboard(self):
        """Executa o dashboard principal"""
        while True:
            try:
                # Limpar tela (Windows)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Exibir dashboard
                self.display_header()
                self.display_health_status()
                self.display_metrics_summary()
                self.display_resilience_status()
                self.display_config_summary()
                self.display_recent_activity()
                self.display_actions_menu()
                
                # Aguardar input do usuário
                try:
                    action = input("\n🎯 Escolha uma ação (1-4): ").strip()
                    self.execute_action(action)
                except KeyboardInterrupt:
                    print("\n\n👋 Dashboard interrompido pelo usuário")
                    break
                
                # Aguardar antes da próxima atualização
                if action != "3":  # Se não for atualizar, aguardar
                    print(f"\n⏳ Aguardando {self.refresh_interval} segundos...")
                    time.sleep(self.refresh_interval)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Dashboard interrompido pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro no dashboard: {e}")
                print("🔄 Tentando novamente em 5 segundos...")
                time.sleep(5)

def main():
    """Função principal"""
    print("🚀 Iniciando Dashboard de Monitoramento...")
    
    try:
        dashboard = MonitorDashboard()
        dashboard.run_dashboard()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
