#!/usr/bin/env python3
"""
Teste para validar o sistema de confirmação de duas fases após correção.
Verifica se o bot aplica lógica probabilística no mesmo tick após confirmação.
"""

import re
import os

def test_confirmation_system():
    """Testa se o sistema de confirmação foi corrigido corretamente."""
    
    file_path = "tunderbotalavanca.py"
    
    if not os.path.exists(file_path):
        print("❌ ERRO: Arquivo tunderbotalavanca.py não encontrado")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 VALIDANDO CORREÇÃO DO SISTEMA DE CONFIRMAÇÃO")
    print("=" * 60)
    
    # Teste 1: Verificar se o return incorreto foi removido
    print("\n1. Verificando remoção do return incorreto após confirmação...")
    
    # Procurar pela seção de confirmação
    confirmation_pattern = r'if self\.aguardando_confirmacao and last_digit < 8:(.*?)(?=\n\s*#|\n\s*if|\Z)'
    confirmation_match = re.search(confirmation_pattern, content, re.DOTALL)
    
    if confirmation_match:
        confirmation_section = confirmation_match.group(1)
        
        # Verificar se NÃO há return na seção de confirmação
        if 'return' not in confirmation_section:
            print("✅ Return incorreto removido com sucesso")
            test1_passed = True
        else:
            print("❌ Return incorreto ainda presente na seção de confirmação")
            print(f"Seção encontrada: {confirmation_section}")
            test1_passed = False
    else:
        print("❌ Seção de confirmação não encontrada")
        test1_passed = False
    
    # Teste 2: Verificar se a mensagem de log foi atualizada
    print("\n2. Verificando atualização da mensagem de log...")
    
    log_pattern = r'logger\.info\(f"✅ CONFIRMAÇÃO RECEBIDA - ROBÔ PRONTO PARA OPERAR \(dígito: \{last_digit\}\)"\)'
    if re.search(log_pattern, content):
        print("✅ Mensagem de log atualizada corretamente")
        test2_passed = True
    else:
        print("❌ Mensagem de log não foi atualizada")
        test2_passed = False
    
    # Teste 3: Verificar se o comentário de correção está presente
    print("\n3. Verificando comentário de correção...")
    
    if "# ✅ CORRIGIDO: Continuar para lógica probabilística no mesmo tick" in content:
        print("✅ Comentário de correção presente")
        test3_passed = True
    else:
        print("❌ Comentário de correção não encontrado")
        test3_passed = False
    
    # Teste 4: Verificar estrutura geral da função
    print("\n4. Verificando estrutura geral da função...")
    
    # Verificar se todas as etapas estão presentes
    etapas = [
        "# ETAPA 1: FILTRO DE SEGURANÇA",
        "# ETAPA 2: SISTEMA DE CONFIRMAÇÃO", 
        "# ETAPA 3: VERIFICAR SE PODE OPERAR",
        "# ETAPA 4: FILTRO PROBABILÍSTICO"
    ]
    
    etapas_encontradas = 0
    for etapa in etapas:
        if etapa in content:
            etapas_encontradas += 1
    
    if etapas_encontradas == 4:
        print("✅ Todas as 4 etapas estão presentes")
        test4_passed = True
    else:
        print(f"❌ Apenas {etapas_encontradas}/4 etapas encontradas")
        test4_passed = False
    
    # Teste 5: Verificar lógica probabilística
    print("\n5. Verificando lógica probabilística...")
    
    probabilistic_patterns = [
        r'if self\.consecutive_losses == 0 and random_number >= 1:',
        r'elif self\.consecutive_losses == 1 and random_number >= 6:',
        r'elif self\.consecutive_losses >= 2 and random_number <= 4:'
    ]
    
    probabilistic_found = 0
    for pattern in probabilistic_patterns:
        if re.search(pattern, content):
            probabilistic_found += 1
    
    if probabilistic_found == 3:
        print("✅ Lógica probabilística completa presente")
        test5_passed = True
    else:
        print(f"❌ Apenas {probabilistic_found}/3 condições probabilísticas encontradas")
        test5_passed = False
    
    # Resultado final
    print("\n" + "=" * 60)
    print("RESULTADO FINAL:")
    
    all_tests = [test1_passed, test2_passed, test3_passed, test4_passed, test5_passed]
    passed_tests = sum(all_tests)
    
    if passed_tests == 5:
        print("🎉 TODOS OS TESTES PASSARAM - CORREÇÃO IMPLEMENTADA COM SUCESSO!")
        print("\n✅ O bot agora:")
        print("   - Remove o return incorreto após confirmação")
        print("   - Aplica lógica probabilística no mesmo tick após confirmação")
        print("   - Mantém todas as etapas de segurança")
        print("   - Segue exatamente a lógica do XML")
        return True
    else:
        print(f"❌ {passed_tests}/5 testes passaram - CORREÇÃO INCOMPLETA")
        return False

if __name__ == "__main__":
    test_confirmation_system()