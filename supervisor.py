import subprocess
import time
import sys
import os
import subprocess
from datetime import datetime

# Configurações
script_a_rodar = "bot_trading_system.py"
tempo_de_execucao_segundos = 3600  # 1 hora
pausa_entre_reinicios_segundos = 15

# Estatísticas do supervisor
class SupervisorStats:
    def __init__(self):
        self.inicio_supervisor = datetime.now()
        self.total_ciclos = 0
        self.reinicios_programados = 0
        self.reinicios_por_falha = 0
        self.ultimo_reinicio = None
        
    def registrar_reinicio_programado(self):
        self.reinicios_programados += 1
        self.ultimo_reinicio = datetime.now()
        
    def registrar_reinicio_falha(self):
        self.reinicios_por_falha += 1
        self.ultimo_reinicio = datetime.now()
        
    def get_relatorio(self):
        tempo_ativo = datetime.now() - self.inicio_supervisor
        return {
            'tempo_ativo': str(tempo_ativo).split('.')[0],
            'total_ciclos': self.total_ciclos,
            'reinicios_programados': self.reinicios_programados,
            'reinicios_por_falha': self.reinicios_por_falha,
            'ultimo_reinicio': self.ultimo_reinicio.strftime("%H:%M:%S") if self.ultimo_reinicio else "N/A"
        }

# Instância global das estatísticas
stats = SupervisorStats()

def log_message(message):
    """Função para logging com timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_python_executable():
    """Obtém o caminho para o executável Python disponível"""
    # Lista de possíveis caminhos para o Python
    possible_paths = []
    
    if os.name == 'nt':  # Windows
        possible_paths = [
            os.path.join("venv", "Scripts", "python.exe"),
            os.path.join(".venv", "Scripts", "python.exe"),
            "python.exe",
            "python"
        ]
    else:  # Linux/Mac
        possible_paths = [
            os.path.join("venv", "bin", "python"),
            os.path.join(".venv", "bin", "python"),
            "python3",
            "python"
        ]
    
    # Tenta encontrar um executável Python válido
    for python_path in possible_paths:
        try:
            if os.path.exists(python_path):
                # Testa se o Python funciona
                result = subprocess.run([python_path, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    log_message(f"✅ Python encontrado: {python_path}")
                    log_message(f"📋 Versão: {result.stdout.strip()}")
                    return python_path
            else:
                # Para comandos do sistema (python, python3)
                if python_path in ["python", "python.exe", "python3"]:
                    try:
                        result = subprocess.run([python_path, "--version"], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            log_message(f"✅ Python do sistema encontrado: {python_path}")
                            log_message(f"📋 Versão: {result.stdout.strip()}")
                            return python_path
                    except FileNotFoundError:
                        continue
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    
    # Se chegou aqui, não encontrou Python válido
    log_message("❌ ERRO CRÍTICO: Nenhum executável Python válido encontrado!")
    log_message("💡 Opções para resolver:")
    log_message("   1. Criar ambiente virtual: python -m venv venv")
    log_message("   2. Ativar ambiente virtual existente")
    log_message("   3. Instalar Python no sistema")
    log_message("   4. Verificar se Python está no PATH")
    sys.exit(1)

def exibir_estatisticas():
    """Exibe estatísticas do supervisor"""
    relatorio = stats.get_relatorio()
    log_message("📊 ESTATÍSTICAS DO SUPERVISOR")
    log_message(f"⏰ Tempo ativo: {relatorio['tempo_ativo']}")
    log_message(f"🔄 Total de ciclos: {relatorio['total_ciclos']}")
    log_message(f"⏰ Reinícios programados: {relatorio['reinicios_programados']}")
    log_message(f"⚠️ Reinícios por falha: {relatorio['reinicios_por_falha']}")
    log_message(f"🕐 Último reinício: {relatorio['ultimo_reinicio']}")
    log_message("=" * 50)

def main():
    """Função principal do supervisor"""
    log_message("🚀 SUPERVISOR ROBUSTO INICIADO")
    log_message("=" * 50)
    log_message(f"📄 Script a executar: {script_a_rodar}")
    log_message(f"⏱️  Tempo de execução: {tempo_de_execucao_segundos} segundos ({tempo_de_execucao_segundos//60} minutos)")
    log_message(f"⏸️  Pausa entre reinícios: {pausa_entre_reinicios_segundos} segundos")
    log_message("🔧 Funcionalidades: Reinício por tempo + Detecção de falhas")
    log_message("=" * 50)
    
    # Obter o executável Python
    python_executable = get_python_executable()
    
    # Verificar se o script existe
    if not os.path.exists(script_a_rodar):
        log_message(f"❌ ERRO CRÍTICO: Script não encontrado: {script_a_rodar}")
        sys.exit(1)
    
    log_message(f"✅ Script encontrado: {script_a_rodar}")
    log_message("🔄 Iniciando loop de supervisão robusto...")
    log_message("💡 O supervisor detectará falhas automaticamente e reiniciará o sistema")
    
    ciclo = 1
    
    while True:
        try:
            stats.total_ciclos = ciclo
            log_message(f"🔄 CICLO {ciclo} - Iniciando {script_a_rodar}")
            
            # Exibir estatísticas a cada 5 ciclos
            if ciclo > 1 and ciclo % 5 == 0:
                exibir_estatisticas()
            
            # Iniciar o processo
            inicio_processo = datetime.now()
            processo = subprocess.Popen([python_executable, script_a_rodar])
            log_message(f"✅ Processo iniciado com PID: {processo.pid} às {inicio_processo.strftime('%H:%M:%S')}")
            
            # Aguardar pelo tempo especificado ou até o processo terminar
            try:
                # Esta é a chave: wait() com timeout detecta ambas as situações
                processo.wait(timeout=tempo_de_execucao_segundos)
                # Se chegou aqui, o processo dos bots parou inesperadamente
                tempo_execucao = datetime.now() - inicio_processo
                log_message("⚠️ O script dos bots parou inesperadamente. Reiniciando...")
                log_message(f"🔍 Código de saída do processo: {processo.returncode}")
                log_message(f"⏱️ Tempo de execução antes da falha: {str(tempo_execucao).split('.')[0]}")
                stats.registrar_reinicio_falha()
                
            except subprocess.TimeoutExpired:
                # Reinício programado - processo ainda estava rodando após 1 hora
                log_message(f"⏰ Tempo limite atingido ({tempo_de_execucao_segundos}s) - Reinício programado")
                log_message("🔄 Encerrando processo para reinício programado...")
                stats.registrar_reinicio_programado()
                
                # Encerrar o processo graciosamente
                processo.terminate()
                try:
                    processo.wait(timeout=10)
                    log_message("✅ Processo encerrado graciosamente")
                except subprocess.TimeoutExpired:
                    log_message("⚠️ Forçando encerramento do processo...")
                    processo.kill()
                    processo.wait()
                    log_message("✅ Processo encerrado forçadamente")
            
        # Pausa entre reinícios (essencial para evitar reinícios frenéticos)
        if pausa_entre_reinicios_segundos > 0:
            log_message(f"⏸️ Aguardando {pausa_entre_reinicios_segundos} segundos antes do próximo ciclo...")
            time.sleep(pausa_entre_reinicios_segundos)
        
        ciclo += 1
            
        except KeyboardInterrupt:
            log_message("🛑 INTERRUPÇÃO MANUAL DETECTADA (Ctrl+C)")
            if 'processo' in locals() and processo.poll() is None:
                log_message("🔄 Encerrando processo do bot...")
                processo.terminate()
                try:
                    processo.wait(timeout=10)
                    log_message("✅ Processo do bot encerrado graciosamente")
                except subprocess.TimeoutExpired:
                    log_message("⚠️ Forçando encerramento do processo do bot...")
                    processo.kill()
                    processo.wait()
                    log_message("✅ Processo do bot encerrado forçadamente")
            
            log_message("👋 SUPERVISOR ENCERRADO")
            log_message("📊 ESTATÍSTICAS FINAIS:")
            exibir_estatisticas()
            break
            
        except Exception as e:
            log_message(f"❌ ERRO INESPERADO NO SUPERVISOR: {str(e)}")
            log_message(f"🔍 Tipo do erro: {type(e).__name__}")
            log_message("🔄 Tentando continuar operação...")
            stats.registrar_reinicio_falha()
            
            # Se há um processo rodando, tentar encerrar
            if 'processo' in locals() and processo.poll() is None:
                try:
                    log_message("🛑 Encerrando processo devido ao erro...")
                    processo.terminate()
                    processo.wait(timeout=5)
                    log_message("✅ Processo encerrado após erro")
                except:
                    try:
                        processo.kill()
                        processo.wait()
                        log_message("✅ Processo forçadamente encerrado após erro")
                    except:
                        log_message("⚠️ Não foi possível encerrar o processo")
                        pass
            
            # Pausa antes de tentar novamente
            time.sleep(pausa_entre_reinicios_segundos)
            ciclo += 1

if __name__ == "__main__":
    main()