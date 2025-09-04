import os
import re
from datetime import datetime, timedelta

def search_log_files():
    """Busca por arquivos de log e operações finalizadas"""
    
    print("🔍 BUSCANDO LOGS DE OPERAÇÕES FINALIZADAS")
    print("=" * 50)
    
    # Padrões para buscar
    patterns = [
        r"📤 Enviando dados para Supabase",
        r"✅ Operação registrada no banco",
        r"❌ Erro ao registrar operação no Supabase",
        r"🏁 Contrato .* finalizado - Lucro",
        r"📊 Estado atual: Stake",
        r"🏁 Registro final:",
        r"WIN|LOSS",
        r"aplicar_gestao_risco",
        r"log_operation"
    ]
    
    # Buscar em arquivos de log
    log_files = []
    
    # Verificar se há arquivos de log na pasta
    for file in os.listdir('.'):
        if file.endswith('.log') or 'log' in file.lower():
            log_files.append(file)
    
    if not log_files:
        print("❌ Nenhum arquivo de log encontrado na pasta atual")
        print("💡 Os logs podem estar sendo exibidos apenas no terminal")
        return
    
    print(f"📁 Arquivos de log encontrados: {log_files}")
    
    for log_file in log_files:
        print(f"\n📄 Analisando: {log_file}")
        print("-" * 30)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Buscar por padrões relevantes
            matches = []
            for i, line in enumerate(lines):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        matches.append((i+1, line.strip()))
                        break
            
            if matches:
                print(f"✅ {len(matches)} linhas relevantes encontradas:")
                for line_num, line in matches[-10:]:  # Últimas 10 ocorrências
                    print(f"   {line_num}: {line}")
            else:
                print("❌ Nenhuma linha relevante encontrada")
                
        except Exception as e:
            print(f"❌ Erro ao ler {log_file}: {e}")

def search_current_terminal_output():
    """Busca por evidências de operações no output atual"""
    
    print("\n\n🔍 ANÁLISE DO PROBLEMA DE REGISTRO")
    print("=" * 50)
    
    print("📋 EVIDÊNCIAS ENCONTRADAS:")
    print("✅ Compras sendo executadas (Contract IDs vistos nos logs)")
    print("✅ Padrões sendo analisados continuamente")
    print("❓ Falta: logs de finalização de contratos e registro no Supabase")
    
    print("\n🔍 POSSÍVEIS CAUSAS:")
    print("1. ❌ Erro na função aplicar_gestao_risco() que chama log_operation()")
    print("2. ❌ Erro de conexão com Supabase durante o registro")
    print("3. ❌ Contratos não finalizando devido a timeouts/erros de API")
    print("4. ❌ Exceções sendo capturadas silenciosamente")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Verificar se aplicar_gestao_risco() está sendo chamada")
    print("2. Adicionar logs mais detalhados na função log_operation()")
    print("3. Verificar se há exceções sendo ignoradas")
    print("4. Testar conexão Supabase durante execução")

if __name__ == "__main__":
    search_log_files()
    search_current_terminal_output()