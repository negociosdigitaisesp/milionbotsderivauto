#!/usr/bin/env python3
"""
Script de teste para validar a configuração do ambiente Python 3.12
Testa se todas as dependências podem ser importadas corretamente
"""

import sys
import json
from datetime import datetime

def test_python_version():
    """Testa se a versão do Python é 3.12+"""
    version = sys.version_info
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 12:
        print("✅ Python 3.12+ detected")
        return True
    else:
        print("❌ Python 3.12+ required")
        return False

def test_setuptools():
    """Testa se setuptools está disponível"""
    try:
        import setuptools
        print(f"✅ setuptools version: {setuptools.__version__}")
        
        # Verificar se a versão é >= 65.0.0
        version_parts = setuptools.__version__.split('.')
        major_version = int(version_parts[0])
        
        if major_version >= 65:
            print("✅ setuptools >= 65.0.0 detected")
            return True
        else:
            print("❌ setuptools >= 65.0.0 required")
            return False
            
    except ImportError:
        print("❌ setuptools not available")
        return False

def test_distutils():
    """Testa se distutils está disponível"""
    try:
        import distutils
        from distutils.util import strtobool
        print("✅ distutils is available")
        print("✅ distutils.util is working")
        return True
    except ImportError as e:
        print(f"❌ distutils not available: {e}")
        return False

def test_dependencies():
    """Testa se as dependências principais podem ser importadas"""
    dependencies = [
        'json',
        'os',
        'datetime',
        'http.server'
    ]
    
    success = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} imported successfully")
        except ImportError as e:
            print(f"❌ {dep} import failed: {e}")
            success = False
    
    return success

def test_optional_dependencies():
    """Testa dependências opcionais do requirements.txt"""
    optional_deps = [
        ('supabase', 'Supabase client'),
        ('dotenv', 'python-dotenv'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('colorama', 'Colorama')
    ]
    
    for module, name in optional_deps:
        try:
            __import__(module)
            print(f"✅ {name} imported successfully")
        except ImportError:
            print(f"⚠️ {name} not available (optional)")

def main():
    """Executa todos os testes"""
    print("🔍 Testando configuração do ambiente Python 3.12 para Vercel")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Setuptools", test_setuptools),
        ("Distutils", test_distutils),
        ("Core Dependencies", test_dependencies)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n📋 Testing Optional Dependencies:")
    test_optional_dependencies()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Todos os testes passaram! Ambiente pronto para deploy no Vercel.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique a configuração antes do deploy.")
    
    # Gerar relatório JSON
    report = {
        "timestamp": datetime.now().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "tests": [{"name": name, "passed": result} for name, result in results],
        "all_tests_passed": all_passed,
        "environment": "local_test"
    }
    
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Relatório salvo em: test_report.json")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())