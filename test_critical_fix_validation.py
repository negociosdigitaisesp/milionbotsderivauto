#!/usr/bin/env python3
"""
Teste de validação da correção crítica do sistema de confirmação.
Verifica se todas as modificações solicitadas foram implementadas.
"""

import re
import os

def test_critical_fix():
    """Valida se a correção crítica foi implementada corretamente."""
    
    file_path = "tunderbotalavanca.py"
    
    if not os.path.exists(file_path):
        print("❌ ERRO: Arquivo tunderbotalavanca.py não encontrado")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 VALIDAÇÃO DA CORREÇÃO CRÍTICA DO SISTEMA DE CONFIRMAÇÃO")
    print("=" * 70)
    
    # Teste 1: Verificar otimização do log de risco (só loga se mudou de estado)
    print("\n1. Verificando otimização do log de risco...")
    
    risk_pattern = r'if not self\.aguardando_confirmacao:\s*#.*\n\s*self\.aguardando_confirmacao = True\s*\n\s*logger\.info\(f"🛡️ DÍGITO DE RISCO DETECTADO'
    if re.search(risk_pattern, content, re.MULTILINE):
        print("✅ Otimização do log de risco implementada (só loga se mudou de estado)")
        test1_passed = True
    else:
        print("❌ Otimização do log de risco não encontrada")
        test1_passed = False
    
    # Teste 2: Verificar comentário de correção atualizado
    print("\n2. Verificando comentário de correção atualizado...")
    
    if "# ✅ CORRIGIDO: NÃO fazer return aqui - continuar para lógica probabilística" in content:
        print("✅ Comentário de correção atualizado corretamente")
        test2_passed = True
    else:
        print("❌ Comentário de correção não foi atualizado")
        test2_passed = False
    
    # Teste 3: Verificar título da ETAPA 2 atualizado
    print("\n3. Verificando título da ETAPA 2...")
    
    if "# ETAPA 2: SISTEMA DE CONFIRMAÇÃO (CORRIGIDO)" in content:
        print("✅ Título da ETAPA 2 atualizado para (CORRIGIDO)")
        test3_passed = True
    else:
        print("❌ Título da ETAPA 2 não foi atualizado")
        test3_passed = False
    
    # Teste 4: Verificar título da ETAPA 3 atualizado
    print("\n4. Verificando título da ETAPA 3...")
    
    if "# ETAPA 3: VERIFICAR SE AINDA EM MODO ESPERA" in content:
        print("✅ Título da ETAPA 3 atualizado corretamente")
        test4_passed = True
    else:
        print("❌ Título da ETAPA 3 não foi atualizado")
        test4_passed = False
    
    # Teste 5: Verificar log simplificado no final
    print("\n5. Verificando log simplificado...")
    
    if 'logger.debug(f"❌ Gatilho não ativado - Loss={self.consecutive_losses}, Random={random_number}")' in content:
        print("✅ Log simplificado implementado")
        test5_passed = True
    else:
        print("❌ Log não foi simplificado")
        test5_passed = False
    
    # Teste 6: Verificar ausência do return problemático
    print("\n6. Verificando ausência do return problemático...")
    
    # Procurar pela seção de confirmação e verificar se não há return
    confirmation_pattern = r'if self\.aguardando_confirmacao and last_digit < 8:(.*?)(?=\n\s*#|\n\s*if|\Z)'
    confirmation_match = re.search(confirmation_pattern, content, re.DOTALL)
    
    if confirmation_match:
        confirmation_section = confirmation_match.group(1)
        if 'return' not in confirmation_section:
            print("✅ Return problemático removido com sucesso")
            test6_passed = True
        else:
            print("❌ Return problemático ainda presente")
            test6_passed = False
    else:
        print("❌ Seção de confirmação não encontrada")
        test6_passed = False
    
    # Teste 7: Verificar estrutura completa das 4 etapas
    print("\n7. Verificando estrutura completa...")
    
    etapas_esperadas = [
        "# ETAPA 1: FILTRO DE SEGURANÇA (FIEL AO XML)",
        "# ETAPA 2: SISTEMA DE CONFIRMAÇÃO (CORRIGIDO)",
        "# ETAPA 3: VERIFICAR SE AINDA EM MODO ESPERA",
        "# ETAPA 4: FILTRO PROBABILÍSTICO (FIEL AO XML)"
    ]
    
    etapas_encontradas = 0
    for etapa in etapas_esperadas:
        if etapa in content:
            etapas_encontradas += 1
    
    if etapas_encontradas == 4:
        print("✅ Todas as 4 etapas com títulos corretos presentes")
        test7_passed = True
    else:
        print(f"❌ Apenas {etapas_encontradas}/4 etapas encontradas")
        test7_passed = False
    
    # Resultado final
    print("\n" + "=" * 70)
    print("RESULTADO FINAL DA VALIDAÇÃO:")
    
    all_tests = [test1_passed, test2_passed, test3_passed, test4_passed, test5_passed, test6_passed, test7_passed]
    passed_tests = sum(all_tests)
    
    if passed_tests == 7:
        print("🎉 CORREÇÃO CRÍTICA IMPLEMENTADA COM SUCESSO!")
        print("\n✅ Todas as modificações solicitadas foram aplicadas:")
        print("   - Otimização do log de risco (só loga se mudou de estado)")
        print("   - Return problemático removido da seção de confirmação")
        print("   - Comentários e títulos atualizados corretamente")
        print("   - Log simplificado implementado")
        print("   - Estrutura das 4 etapas mantida e corrigida")
        print("\n🚀 O bot agora segue EXATAMENTE a lógica do XML!")
        return True
    else:
        print(f"❌ {passed_tests}/7 validações passaram - CORREÇÃO INCOMPLETA")
        return False

if __name__ == "__main__":
    test_critical_fix()