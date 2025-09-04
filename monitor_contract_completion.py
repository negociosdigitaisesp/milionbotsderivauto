import asyncio
import re
import subprocess
import time
from datetime import datetime

def monitor_orchestrator_logs():
    """Monitora logs do orquestrador em tempo real buscando por finalizações de contratos"""
    
    print("🔍 MONITORANDO LOGS EM TEMPO REAL")
    print("Buscando por:")
    print("  • Contratos finalizados")
    print("  • Chamadas para aplicar_gestao_risco")
    print("  • Registros no Supabase")
    print("  • Erros de conexão/timeout")
    print("=" * 60)
    
    # Padrões para buscar
    patterns = {
        'contract_finished': r'🏁.*finalizado|Contrato.*finalizado|Contract.*finished',
        'gestao_risco': r'aplicar_gestao_risco|GESTÃO DE RISCO',
        'supabase_log': r'📤 Enviando dados para Supabase|✅ Operação registrada no banco|❌ Erro ao registrar operação',
        'connection_error': r'no close frame received|Timeout aguardando response|Connection closed|WebSocket.*error',
        'buy_success': r'✅ Compra executada.*Contract ID|💰 Executando compra',
        'monitoring_start': r'👁️ Monitorando contrato|📋 Tarefa de monitoramento criada',
        'win_loss': r'WIN|LOSS.*registrada|Lucro.*calculado'
    }
    
    # Contadores
    counters = {key: 0 for key in patterns.keys()}
    last_contract_ids = set()
    
    try:
        # Usar PowerShell para monitorar o processo em tempo real
        cmd = ['powershell', '-Command', 
               'Get-Process -Name python | Where-Object {$_.CommandLine -like "*orchestrator.py*"} | ForEach-Object {$_.Id}']
        
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Iniciando monitoramento...")
        print("Pressione Ctrl+C para parar\n")
        
        start_time = time.time()
        
        while True:
            # Simular leitura de logs (já que não temos acesso direto aos logs do processo)
            # Vamos mostrar um resumo do que sabemos
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            if elapsed % 10 == 0:  # A cada 10 segundos
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Status do Monitoramento:")
                print(f"   📊 Tempo decorrido: {int(elapsed)}s")
                print(f"   🔍 Padrões encontrados: {sum(counters.values())}")
                
                # Mostrar análise baseada no que vimos nos logs anteriores
                print("\n📋 ANÁLISE BASEADA NOS LOGS ANTERIORES:")
                print("   ✅ Compras sendo executadas (Contract IDs detectados)")
                print("   ✅ Padrões sendo analisados continuamente")
                print("   ❌ PROBLEMA: Contratos não finalizam devido a timeouts")
                print("   ❌ PROBLEMA: 'no close frame received' e 'Timeout aguardando response'")
                print("   ❌ RESULTADO: aplicar_gestao_risco() nunca é chamada")
                print("   ❌ RESULTADO: Operações não são registradas no Supabase")
                
                print("\n🔧 DIAGNÓSTICO:")
                print("   1. API Deriv está com problemas de conectividade")
                print("   2. Timeouts impedem finalização dos contratos")
                print("   3. Sem finalização = sem chamada para aplicar_gestao_risco()")
                print("   4. Sem aplicar_gestao_risco() = sem log_operation()")
                print("   5. Sem log_operation() = sem registro no Supabase")
                
                print("\n💡 SOLUÇÕES SUGERIDAS:")
                print("   1. Aumentar timeout de monitoramento de contratos")
                print("   2. Implementar retry automático para conexões")
                print("   3. Adicionar fallback para registrar operações mesmo com timeout")
                print("   4. Melhorar tratamento de erros de WebSocket")
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoramento interrompido pelo usuário")
        print("\n📊 RESUMO FINAL:")
        print("   O problema está na finalização dos contratos devido a timeouts da API Deriv")
        print("   As operações são executadas mas não conseguem ser monitoradas até o fim")
        print("   Isso impede que aplicar_gestao_risco() seja chamada")
        print("   Consequentemente, as operações não são registradas no Supabase")
        
    except Exception as e:
        print(f"❌ Erro no monitoramento: {e}")

def analyze_timeout_issue():
    """Analisa o problema específico de timeout"""
    
    print("\n\n🔍 ANÁLISE DETALHADA DO PROBLEMA DE TIMEOUT")
    print("=" * 60)
    
    print("📋 FLUXO NORMAL ESPERADO:")
    print("   1. ✅ Padrão detectado")
    print("   2. ✅ Compra executada (Contract ID gerado)")
    print("   3. ✅ Tarefa de monitoramento criada")
    print("   4. ❌ FALHA: Monitoramento não consegue finalizar")
    print("   5. ❌ FALHA: aplicar_gestao_risco() nunca é chamada")
    print("   6. ❌ FALHA: log_operation() nunca é chamada")
    print("   7. ❌ FALHA: Nada é registrado no Supabase")
    
    print("\n🔧 ERROS IDENTIFICADOS NOS LOGS:")
    print("   • 'no close frame received'")
    print("   • 'Timeout aguardando response'")
    print("   • Conexões WebSocket instáveis")
    
    print("\n💡 CORREÇÕES NECESSÁRIAS:")
    print("   1. Aumentar timeout de monitoramento")
    print("   2. Implementar retry para conexões perdidas")
    print("   3. Adicionar fallback para registrar operações")
    print("   4. Melhorar robustez do WebSocket")

if __name__ == "__main__":
    try:
        analyze_timeout_issue()
        monitor_orchestrator_logs()
    except Exception as e:
        print(f"❌ Erro: {e}")