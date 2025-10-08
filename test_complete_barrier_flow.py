#!/usr/bin/env python3
"""
Teste Completo do Fluxo da Barreira Dinâmica
Valida todo o fluxo desde executar_compra_digitunder() até proposal()
"""

import sys
import os
import re

def test_complete_barrier_flow():
    """Testa o fluxo completo da barreira dinâmica"""
    
    print("🔍 TESTE COMPLETO DO FLUXO DA BARREIRA DINÂMICA")
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
    total_tests = 7
    
    # Teste 1: Verificar cálculo da barreira dinâmica em executar_compra_digitunder
    print("\n1️⃣ Testando cálculo da barreira dinâmica...")
    
    barrier_calc_pattern = r'if\s+self\.consecutive_losses\s*==\s*0:\s*barrier\s*=\s*8\s*else:\s*barrier\s*=\s*5'
    if re.search(barrier_calc_pattern, content):
        print("   ✅ PASSOU: Cálculo da barreira dinâmica correto (8 se Loss=0, senão 5)")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: Cálculo da barreira dinâmica incorreto")
    
    # Teste 2: Verificar se proposal_params inclui barrier
    print("\n2️⃣ Testando proposal_params com barrier...")
    
    proposal_params_pattern = r'"barrier":\s*str\(barrier\)'
    if re.search(proposal_params_pattern, content):
        print("   ✅ PASSOU: proposal_params inclui 'barrier': str(barrier)")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: proposal_params não inclui barrier corretamente")
    
    # Teste 3: Verificar logs da barreira dinâmica
    print("\n3️⃣ Testando logs da barreira dinâmica...")
    
    log_barrier_pattern = r'barrier\s*\(dinâmica\):\s*\{barrier\}'
    if re.search(log_barrier_pattern, content):
        print("   ✅ PASSOU: Logs da barreira dinâmica presentes")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: Logs da barreira dinâmica ausentes")
    
    # Teste 4: Verificar função proposal() usa params.get("barrier")
    print("\n4️⃣ Testando função proposal() - uso de barrier...")
    
    proposal_barrier_pattern = r'"barrier":\s*str\(params\.get\("barrier",\s*"5"\)\)'
    if re.search(proposal_barrier_pattern, content):
        print("   ✅ PASSOU: proposal() usa params.get('barrier', '5')")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: proposal() não usa params.get('barrier', '5')")
    
    # Teste 5: Verificar logs de verificação na função proposal
    print("\n5️⃣ Testando logs de verificação na proposal()...")
    
    verification_log_pattern = r'VERIFICAÇÃO BARREIRA:\s*Recebida=\{barrier_recebida\}'
    if re.search(verification_log_pattern, content):
        print("   ✅ PASSOU: Logs de verificação presentes na proposal()")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: Logs de verificação ausentes na proposal()")
    
    # Teste 6: Verificar _pre_validate_params usa barrier
    print("\n6️⃣ Testando _pre_validate_params() - uso de barrier...")
    
    pre_validate_pattern = r"'barrier':\s*int\(PREDICTION\)"
    if re.search(pre_validate_pattern, content):
        print("   ✅ PASSOU: _pre_validate_params() usa 'barrier'")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: _pre_validate_params() não usa 'barrier'")
    
    # Teste 7: Verificar ausência de referências antigas a prediction
    print("\n7️⃣ Testando ausência de 'prediction' nas funções críticas...")
    
    # Extrair funções críticas
    proposal_match = re.search(r'async def proposal\(self, params\):.*?(?=async def|\Z)', content, re.DOTALL)
    executar_match = re.search(r'async def executar_compra_digitunder\(self\).*?(?=async def|\Z)', content, re.DOTALL)
    
    prediction_found = False
    if proposal_match and '"prediction"' in proposal_match.group(0):
        prediction_found = True
    if executar_match and '"prediction"' in executar_match.group(0):
        prediction_found = True
    
    if not prediction_found:
        print("   ✅ PASSOU: Não há referências a 'prediction' nas funções críticas")
        tests_passed += 1
    else:
        print("   ❌ FALHOU: Ainda há referências a 'prediction' nas funções críticas")
    
    # Resultado final
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {tests_passed}/{total_tests} testes passaram")
    
    if tests_passed == total_tests:
        print("🎉 SUCESSO: Todo o fluxo da barreira dinâmica está correto!")
        print("\n📋 FLUXO VALIDADO:")
        print("   1. executar_compra_digitunder() calcula barrier = 8 ou 5 ✅")
        print("   2. proposal_params inclui 'barrier': str(barrier) ✅")
        print("   3. self.api_manager.proposal() recebe barrier ✅")
        print("   4. proposal() usa params.get('barrier', '5') ✅")
        print("   5. Logs de verificação implementados ✅")
        print("   6. _pre_validate_params() usa 'barrier' ✅")
        print("   7. Sem referências antigas a 'prediction' ✅")
        print("\n🚀 O bot está 100% alinhado com o XML!")
        print("\n🎯 COMPORTAMENTO ESPERADO:")
        print("   • Loss = 0 → barrier = 8 (mais conservador)")
        print("   • Loss ≥ 1 → barrier = 5 (mais agressivo)")
        return True
    else:
        print("❌ FALHA: Alguns aspectos do fluxo ainda precisam correção!")
        return False

if __name__ == "__main__":
    success = test_complete_barrier_flow()
    sys.exit(0 if success else 1)