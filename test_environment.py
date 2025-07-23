#!/usr/bin/env python3
"""
Script de Teste de Ambiente para VPS
Verifica se todas as dependências e configurações estão corretas
"""

import sys
import os
import importlib
import json
from datetime import datetime

def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_status(item, status, details=""):
    """Imprime status de um item"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {item:<40} {details}")

def test_python_version():
    """Testa versão do Python"""
    print_header("VERIFICAÇÃO DA VERSÃO DO PYTHON")
    
    version = sys.version_info
    python_version = f"{version.major}.{version.minor}.{version.micro}"
    
    is_valid = version.major >= 3 and version.minor >= 8
    print_status("Versão do Python", is_valid, f"v{python_version}")
    
    if not is_valid:
        print("⚠️  Recomendado: Python 3.8 ou superior")
    
    return is_valid

def test_required_packages():
    """Testa pacotes Python necessários"""
    print_header("VERIFICAÇÃO DE DEPENDÊNCIAS")
    
    required_packages = [
        'websockets',
        'asyncio',
        'supabase',
        'dotenv',  # python-dotenv se importa como 'dotenv'
        'requests',
        'pandas',
        'numpy',
        'ta',
        'schedule'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            # Mostrar o nome original do pacote para clareza
            display_name = 'python-dotenv' if package == 'dotenv' else package
            print_status(f"Pacote {display_name}", True, "Instalado")
        except ImportError:
            display_name = 'python-dotenv' if package == 'dotenv' else package
            print_status(f"Pacote {display_name}", False, "NÃO ENCONTRADO")
            all_installed = False
    
    return all_installed

def test_environment_variables():
    """Testa variáveis de ambiente"""
    print_header("VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE")
    
    # Tentar carregar .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_status("Arquivo .env", True, "Carregado")
    except Exception as e:
        print_status("Arquivo .env", False, f"Erro: {e}")
        return False
    
    required_vars = {
        'DERIV_APP_ID': 'ID da aplicação Deriv',
        'DERIV_API_TOKEN': 'Token da API Deriv',
        'SUPABASE_URL': 'URL do Supabase',
        'SUPABASE_KEY': 'Chave do Supabase'
    }
    
    all_configured = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mascarar valores sensíveis
            if 'TOKEN' in var or 'KEY' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print_status(f"{var}", True, display_value)
        else:
            print_status(f"{var}", False, "NÃO CONFIGURADO")
            all_configured = False
    
    return all_configured

def test_deriv_connection():
    """Testa conexão com Deriv API"""
    print_header("TESTE DE CONEXÃO - DERIV API")
    
    try:
        import asyncio
        import websockets
        
        app_id = os.getenv('DERIV_APP_ID', '1089')
        token = os.getenv('DERIV_API_TOKEN')
        
        if not token:
            print_status("Token Deriv", False, "Token não configurado")
            return False
        
        async def test_connection():
            try:
                uri = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
                async with websockets.connect(uri) as websocket:
                    # Teste de autorização
                    auth_request = {
                        "authorize": token
                    }
                    await websocket.send(json.dumps(auth_request))
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if 'authorize' in data and data['authorize']:
                        print_status("Conexão WebSocket", True, "Conectado")
                        print_status("Autorização", True, f"Usuário: {data['authorize'].get('loginid', 'N/A')}")
                        return True
                    else:
                        print_status("Autorização", False, "Token inválido")
                        return False
                        
            except Exception as e:
                print_status("Conexão Deriv", False, f"Erro: {str(e)[:50]}")
                return False
        
        return asyncio.run(test_connection())
        
    except Exception as e:
        print_status("Teste Deriv", False, f"Erro: {str(e)[:50]}")
        return False

def test_supabase_connection():
    """Testa conexão com Supabase"""
    print_header("TESTE DE CONEXÃO - SUPABASE")
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print_status("Configuração Supabase", False, "URL ou KEY não configurados")
            return False
        
        supabase = create_client(url, key)
        
        # Teste de conexão simples
        response = supabase.table('operacoes').select('*').limit(1).execute()
        
        print_status("Conexão Supabase", True, "Conectado")
        print_status("Tabela 'operacoes'", True, f"{len(response.data)} registros encontrados")
        
        return True
        
    except Exception as e:
        print_status("Teste Supabase", False, f"Erro: {str(e)[:50]}")
        return False

def test_file_permissions():
    """Testa permissões de arquivos"""
    print_header("VERIFICAÇÃO DE PERMISSÕES")
    
    files_to_check = [
        'bot_trading_system.py',
        'trading_system/utils/helpers.py',
        'requirements.txt'
    ]
    
    all_accessible = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            if os.access(file_path, os.R_OK):
                print_status(f"Leitura {file_path}", True, "OK")
            else:
                print_status(f"Leitura {file_path}", False, "SEM PERMISSÃO")
                all_accessible = False
        else:
            print_status(f"Arquivo {file_path}", False, "NÃO ENCONTRADO")
            all_accessible = False
    
    # Verificar permissão de escrita no diretório de logs
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
            print_status("Criação diretório logs", True, "Criado")
        except Exception as e:
            print_status("Criação diretório logs", False, f"Erro: {e}")
            all_accessible = False
    else:
        print_status("Diretório logs", True, "Existe")
    
    return all_accessible

def generate_report():
    """Gera relatório final"""
    print_header("RELATÓRIO FINAL")
    
    tests = [
        ("Versão Python", test_python_version()),
        ("Dependências", test_required_packages()),
        ("Variáveis de Ambiente", test_environment_variables()),
        ("Conexão Deriv", test_deriv_connection()),
        ("Conexão Supabase", test_supabase_connection()),
        ("Permissões de Arquivos", test_file_permissions())
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print(f"\n📊 RESUMO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 SISTEMA PRONTO PARA EXECUÇÃO!")
        print("✅ Todos os testes passaram")
        print("✅ Você pode executar: python bot_trading_system.py")
    else:
        print("\n⚠️  SISTEMA PRECISA DE AJUSTES")
        print("❌ Alguns testes falharam")
        print("📖 Consulte o VPS_INSTALLATION_GUIDE.md para correções")
    
    return passed == total

def main():
    """Função principal"""
    print(f"""
🔧 TESTE DE AMBIENTE - SISTEMA DE TRADING
{'='*60}
Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sistema: {sys.platform}
Diretório: {os.getcwd()}
""")
    
    try:
        success = generate_report()
        
        print(f"\n{'='*60}")
        print("📋 PRÓXIMOS PASSOS:")
        
        if success:
            print("1. Execute: python bot_trading_system.py")
            print("2. Monitore os logs em tempo real")
            print("3. Verifique operações no Supabase")
        else:
            print("1. Corrija os problemas identificados")
            print("2. Execute este teste novamente")
            print("3. Consulte a documentação VPS_INSTALLATION_GUIDE.md")
        
        print(f"{'='*60}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)