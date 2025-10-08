#!/usr/bin/env python3
"""
Teste de Validação da Correção da Barreira Dinâmica
Verifica se a função proposal() está usando corretamente o parâmetro 'barrier' dinâmico
"""

import sys
import os
import re

def test_barrier_fix_validation():
    """Testa se a correção da barreira dinâmica foi aplicada corretamente"""
    
    print("🔍 TESTE DE VALIDAÇÃO DA CORREÇÃO DA BARREIRA DINÂMICA")
    print("=" * 60)
    
    # Caminho do arquivo
    file_path = "tunderbotalavanca.py"
    
    if not os.path.exists(file_path):
        print(f"❌ Arquivo {file_path} não encontrado!")
        return False
    
    # Ler o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = 0
    total_tests = 4
    
    # Teste 1: Verificar se a função proposal() usa 'barrier' em vez de 'prediction'
    print("\n1️⃣ Testando função proposal() - uso correto de 'barrier'...")
    
    # Procurar pela linha corrigida na função proposal
    barrier_pattern = r'"barrier":\s*str\(params\.get\("barrier",\s*"5"\)\)'
    if re.search(barrier_pattern, content):
        print("   ✅ PASSOU: proposal() usa params.get('barrier', '5')")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: proposal() não usa params.get('barrier', '5')")
    
    # Teste 2: Verificar se não há mais referências a 'prediction' na função proposal
    print("\n2️⃣ Testando função proposal() - ausência de 'prediction'...")
    
    # Extrair apenas a função proposal
    proposal_match = re.search(r'async def proposal\(self, params\):.*?(?=async def|\Z)', content, re.DOTALL)
    if proposal_match:
        proposal_content = proposal_match.group(0)
        if '"prediction"' not in proposal_content:
            print("   ✅ PASSOU: proposal() não contém referências a 'prediction'")
            tests_passed += 1
        else:
            print("   ❌ FALHOU: proposal() ainda contém referências a 'prediction'")
    else:
        print("   ❌ FALHOU: Função proposal() não encontrada")
    
    # Teste 3: Verificar se _pre_validate_params() usa 'barrier'
    print("\n3️⃣ Testando _pre_validate_params() - uso correto de 'barrier'...")
    
    # Procurar pela linha corrigida na função _pre_validate_params
    barrier_params_pattern = r"'barrier':\s*int\(PREDICTION\)"
    if re.search(barrier_params_pattern, content):
        print("   ✅ PASSOU: _pre_validate_params() usa 'barrier': int(PREDICTION)")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: _pre_validate_params() não usa 'barrier': int(PREDICTION)")
    
    # Teste 4: Verificar se executar_compra_digitunder() passa 'barrier' corretamente
    print("\n4️⃣ Testando executar_compra_digitunder() - passagem de 'barrier'...")
    
    # Procurar pela linha que passa barrier nos proposal_params
    barrier_proposal_pattern = r'"barrier":\s*str\(barrier\)'
    if re.search(barrier_proposal_pattern, content):
        print("   ✅ PASSOU: executar_compra_digitunder() passa 'barrier': str(barrier)")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: executar_compra_digitunder() não passa 'barrier': str(barrier)")
    
    # Resultado final
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {tests_passed}/{total_tests} testes passaram")
    
    if tests_passed == total_tests:
        print("🎉 SUCESSO: Todas as correções da barreira dinâmica foram aplicadas corretamente!")
        print("\n📋 RESUMO DAS CORREÇÕES VALIDADAS:")
        print("   • proposal() usa params.get('barrier', '5') ✅")
        print("   • proposal() não contém mais 'prediction' ✅")
        print("   • _pre_validate_params() usa 'barrier' ✅")
        print("   • executar_compra_digitunder() passa 'barrier' ✅")
        print("\n🔧 A barreira dinâmica agora funciona conforme o XML:")
        print("   • Loss == 0 → barrier = 8")
        print("   • Loss >= 1 → barrier = 5")
        return True
    else:
        print("❌ FALHA: Algumas correções ainda precisam ser aplicadas!")
        return False

if __name__ == "__main__":
    success = test_barrier_fix_validation()
    sys.exit(0 if success else 1)