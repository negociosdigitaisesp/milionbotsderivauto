#!/usr/bin/env python3
"""
Script de Inicialização dos Sistemas de Radar
Permite executar o radar analyzer original e o novo radar analyzer tunder
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime

def print_header():
    """Imprime o cabeçalho do sistema"""
    print("\n" + "=" * 70)
    print("🎯 SISTEMA DE RADAR ANALYZERS - DERIV TRADING BOTS")
    print("=" * 70)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📁 Diretório: {os.getcwd()}")
    print("=" * 70)
    print("💡 MODO AUTOMÁTICO: python start_radar_systems.py --auto")
    print("📋 MODO INTERATIVO: python start_radar_systems.py")
    print("=" * 70)

def verificar_arquivos():
    """Verifica se os arquivos necessários existem"""
    arquivos_necessarios = [
        'radar_analyzer.py',
        'radar_analyzer_tunder.py',
        '.env'
    ]
    
    print("\n🔍 Verificando arquivos necessários...")
    arquivos_faltando = []
    
    for arquivo in arquivos_necessarios:
        if os.path.exists(arquivo):
            print(f"✅ {arquivo} - OK")
        else:
            print(f"❌ {arquivo} - FALTANDO")
            arquivos_faltando.append(arquivo)
    
    if arquivos_faltando:
        print(f"\n⚠️ AVISO: {len(arquivos_faltando)} arquivo(s) faltando:")
        for arquivo in arquivos_faltando:
            print(f"   • {arquivo}")
        return False
    
    print("\n✅ Todos os arquivos necessários estão presentes")
    return True

def executar_radar_original():
    """Executa o radar analyzer original (Accumulator)"""
    print("\n🚀 Iniciando Radar Analyzer Original (Accumulator)...")
    try:
        subprocess.run([sys.executable, 'radar_analyzer.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar radar analyzer original: {e}")
    except KeyboardInterrupt:
        print("\n⏹️ Radar Analyzer Original interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado no radar analyzer original: {e}")

def executar_radar_tunder():
    """Executa o radar analyzer tunder"""
    print("\n🚀 Iniciando Radar Analyzer Tunder...")
    try:
        subprocess.run([sys.executable, 'radar_analyzer_tunder.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar radar analyzer tunder: {e}")
    except KeyboardInterrupt:
        print("\n⏹️ Radar Analyzer Tunder interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado no radar analyzer tunder: {e}")

def executar_teste_tunder():
    """Executa o teste do radar analyzer tunder"""
    print("\n🧪 Executando teste do Radar Analyzer Tunder...")
    try:
        subprocess.run([sys.executable, 'test_radar_tunder.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar teste: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado no teste: {e}")

def executar_ambos_paralelo():
    """Executa ambos os radars em paralelo usando threads"""
    print("\n🔄 Iniciando ambos os Radar Analyzers em paralelo...")
    print("⚠️ ATENÇÃO: Ambos os sistemas irão rodar simultaneamente")
    print("⚠️ Use Ctrl+C para interromper ambos os processos")
    
    # Criar threads para cada radar
    thread_original = threading.Thread(target=executar_radar_original, name="RadarOriginal")
    thread_tunder = threading.Thread(target=executar_radar_tunder, name="RadarTunder")
    
    try:
        # Iniciar ambas as threads
        thread_original.start()
        time.sleep(2)  # Pequeno delay entre inicializações
        thread_tunder.start()
        
        print("\n✅ Ambos os radars foram iniciados")
        print("📊 Monitorando execução... (Ctrl+C para parar)")
        
        # Aguardar ambas as threads
        thread_original.join()
        thread_tunder.join()
        
    except KeyboardInterrupt:
        print("\n⏹️ Interrupção solicitada pelo usuário")
        print("⏳ Aguardando finalização dos processos...")
        
        # As threads irão finalizar naturalmente com o KeyboardInterrupt
        if thread_original.is_alive():
            thread_original.join(timeout=5)
        if thread_tunder.is_alive():
            thread_tunder.join(timeout=5)
            
        print("✅ Ambos os radars foram finalizados")
    
    except Exception as e:
        print(f"❌ Erro na execução paralela: {e}")

def mostrar_menu():
    """Mostra o menu de opções"""
    print("\n📋 OPÇÕES DISPONÍVEIS:")
    print("=" * 30)
    print("1️⃣  Executar Radar Analyzer Original (Accumulator)")
    print("2️⃣  Executar Radar Analyzer Tunder")
    print("3️⃣  Executar ambos em paralelo")
    print("4️⃣  Testar Radar Analyzer Tunder")
    print("5️⃣  Verificar status dos sistemas")
    print("0️⃣  Sair")
    print("=" * 30)

def verificar_status_sistemas():
    """Verifica o status dos sistemas"""
    print("\n📊 STATUS DOS SISTEMAS")
    print("=" * 40)
    
    # Verificar se os processos estão rodando (simplificado)
    print("🔍 Verificando arquivos de configuração...")
    
    # Verificar .env
    if os.path.exists('.env'):
        print("✅ Arquivo .env encontrado")
        try:
            with open('.env', 'r') as f:
                content = f.read()
                if 'SUPABASE_URL' in content and 'SUPABASE_KEY' in content:
                    print("✅ Credenciais Supabase configuradas")
                else:
                    print("⚠️ Credenciais Supabase podem estar incompletas")
        except Exception as e:
            print(f"⚠️ Erro ao ler .env: {e}")
    else:
        print("❌ Arquivo .env não encontrado")
    
    # Verificar arquivos Python
    arquivos_radar = {
        'radar_analyzer.py': 'Radar Analyzer Original',
        'radar_analyzer_tunder.py': 'Radar Analyzer Tunder',
        'test_radar_tunder.py': 'Teste Radar Tunder'
    }
    
    print("\n🐍 Arquivos Python:")
    for arquivo, descricao in arquivos_radar.items():
        if os.path.exists(arquivo):
            size = os.path.getsize(arquivo)
            print(f"✅ {descricao}: {arquivo} ({size} bytes)")
        else:
            print(f"❌ {descricao}: {arquivo} - NÃO ENCONTRADO")
    
    print("\n💡 INFORMAÇÕES IMPORTANTES:")
    print("• Radar Original: Analisa 'scalping_accumulator_bot_logs'")
    print("• Radar Tunder: Analisa 'tunder_bot_logs'")
    print("• Ambos salvam sinais em 'radar_de_apalancamiento_signals'")
    print("• Radar Tunder usa filtros mais conservadores (1% growth rate)")

def executar_automatico():
    """Executa automaticamente ambos os radares sem menu interativo"""
    print_header()
    
    # Verificar arquivos necessários
    if not verificar_arquivos():
        print("\n❌ Não é possível continuar sem os arquivos necessários")
        return False
    
    print("\n🚀 MODO AUTOMÁTICO: Iniciando ambos os Radar Analyzers...")
    print("⚠️ ATENÇÃO: Ambos os sistemas irão rodar simultaneamente")
    print("⚠️ Use Ctrl+C para interromper ambos os processos")
    
    try:
        executar_ambos_paralelo()
        return True
    except Exception as e:
        print(f"\n❌ Erro na execução automática: {e}")
        return False

def main():
    """Função principal"""
    # Verificar se foi passado argumento para execução automática
    if len(sys.argv) > 1 and sys.argv[1] in ['--auto', '-a', '--both']:
        return executar_automatico()
    
    print_header()
    
    # Verificar arquivos necessários
    if not verificar_arquivos():
        print("\n❌ Não é possível continuar sem os arquivos necessários")
        return
    
    while True:
        mostrar_menu()
        
        try:
            opcao = input("\n👉 Escolha uma opção (0-5): ").strip()
            
            if opcao == '0':
                print("\n👋 Saindo do sistema...")
                break
            
            elif opcao == '1':
                executar_radar_original()
            
            elif opcao == '2':
                executar_radar_tunder()
            
            elif opcao == '3':
                executar_ambos_paralelo()
            
            elif opcao == '4':
                executar_teste_tunder()
            
            elif opcao == '5':
                verificar_status_sistemas()
            
            else:
                print("\n❌ Opção inválida. Tente novamente.")
        
        except KeyboardInterrupt:
            print("\n\n⏹️ Interrompido pelo usuário")
            break
        
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
        
        # Pausa antes de mostrar o menu novamente
        if opcao not in ['0']:
            input("\n⏸️ Pressione Enter para continuar...")
    
    print("\n✅ Sistema finalizado")
    print("=" * 70)

if __name__ == "__main__":
    main()