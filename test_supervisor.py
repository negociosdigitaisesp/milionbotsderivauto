import subprocess
import sys
import os

def test_python():
    """Testa se consegue encontrar Python"""
    possible_paths = ["python.exe", "python", "python3"]
    
    for python_path in possible_paths:
        try:
            result = subprocess.run([python_path, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Python encontrado: {python_path}")
                print(f"📋 Versão: {result.stdout.strip()}")
                return python_path
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"❌ Erro com {python_path}: {e}")
            continue
    
    print("❌ Nenhum Python encontrado!")
    return None

if __name__ == "__main__":
    print("🔍 Testando detecção do Python...")
    python_exe = test_python()
    
    if python_exe:
        print(f"\n✅ Supervisor pode usar: {python_exe}")
        
        # Testar se o bot_trading_system.py existe
        if os.path.exists("bot_trading_system.py"):
            print("✅ bot_trading_system.py encontrado")
            print("🚀 Supervisor está pronto para funcionar!")
        else:
            print("❌ bot_trading_system.py não encontrado")
    else:
        print("❌ Supervisor não pode funcionar sem Python")