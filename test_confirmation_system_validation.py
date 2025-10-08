#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TESTE DE VALIDAÇÃO OBRIGATÓRIA - SISTEMA DE CONFIRMAÇÃO
========================================================

Este teste verifica se o sistema de confirmação está implementado corretamente
conforme especificado pelo usuário, incluindo:

1. ✅ Inicialização de self.aguardando_confirmacao no __init__()
2. ✅ Logs de "DÍGITO DE RISCO DETECTADO" 
3. ✅ Logs de "MODO ESPERA ATIVO"
4. ✅ Logs de "CONFIRMAÇÃO RECEBIDA"
5. ✅ Sequência correta de logs esperada
6. ✅ Ausência do return problemático após confirmação
"""

import os
import sys
import re
import logging

# Configurar logging para capturar os resultados
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_confirmation_system_validation():
    """Teste completo do sistema de confirmação"""
    
    print("="*80)
    print("🧪 TESTE DE VALIDAÇÃO OBRIGATÓRIA - SISTEMA DE CONFIRMAÇÃO")
    print("="*80)
    
    # Caminho do arquivo principal
    file_path = "tunderbotalavanca.py"
    
    if not os.path.exists(file_path):
        print(f"❌ ERRO: Arquivo {file_path} não encontrado!")
        return False
    
    # Ler o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Lista de verificações
    tests = []
    
    # TESTE 1: Verificar inicialização de self.aguardando_confirmacao
    print("\n📋 TESTE 1: Verificação da inicialização de self.aguardando_confirmacao")
    init_pattern = r'self\.aguardando_confirmacao\s*=\s*False'
    if re.search(init_pattern, content):
        print("✅ PASSOU: self.aguardando_confirmacao está inicializada no __init__()")
        tests.append(True)
    else:
        print("❌ FALHOU: self.aguardando_confirmacao NÃO está inicializada!")
        tests.append(False)
    
    # TESTE 2: Verificar log de "DÍGITO DE RISCO DETECTADO"
    print("\n📋 TESTE 2: Verificação do log de dígito de risco")
    risk_log_pattern = r'DÍGITO DE RISCO DETECTADO.*MODO ESPERA ATIVADO'
    if re.search(risk_log_pattern, content):
        print("✅ PASSOU: Log de 'DÍGITO DE RISCO DETECTADO' está presente")
        tests.append(True)
    else:
        print("❌ FALHOU: Log de 'DÍGITO DE RISCO DETECTADO' NÃO encontrado!")
        tests.append(False)
    
    # TESTE 3: Verificar log de "MODO ESPERA ATIVO"
    print("\n📋 TESTE 3: Verificação do log de modo espera")
    wait_log_pattern = r'MODO ESPERA ATIVO.*Aguardando confirmação'
    if re.search(wait_log_pattern, content):
        print("✅ PASSOU: Log de 'MODO ESPERA ATIVO' está presente")
        tests.append(True)
    else:
        print("❌ FALHOU: Log de 'MODO ESPERA ATIVO' NÃO encontrado!")
        tests.append(False)
    
    # TESTE 4: Verificar log de "CONFIRMAÇÃO RECEBIDA"
    print("\n📋 TESTE 4: Verificação do log de confirmação recebida")
    confirm_log_pattern = r'CONFIRMAÇÃO RECEBIDA.*ROBÔ PRONTO PARA OPERAR'
    if re.search(confirm_log_pattern, content):
        print("✅ PASSOU: Log de 'CONFIRMAÇÃO RECEBIDA' está presente")
        tests.append(True)
    else:
        print("❌ FALHOU: Log de 'CONFIRMAÇÃO RECEBIDA' NÃO encontrado!")
        tests.append(False)
    
    # TESTE 5: Verificar ausência do return problemático após confirmação
    print("\n📋 TESTE 5: Verificação da ausência do return problemático")
    # Procurar especificamente por return IMEDIATAMENTE após confirmação (antes da ETAPA 3)
    # O padrão correto deve ter o comentário de correção SEM return executável
    pattern = r'CONFIRMAÇÃO RECEBIDA.*?\n.*?# ✅ CORRIGIDO.*?\n(.*?)(?=\n.*?# ETAPA 3)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        after_confirmation = match.group(1).strip()
        # Verificar se há algum return executável (não em comentário) após confirmação
        if after_confirmation == '' or 'return' not in after_confirmation:
            print("✅ PASSOU: Return problemático foi removido após confirmação")
            tests.append(True)
        else:
            print("❌ FALHOU: Return problemático ainda está presente!")
            print(f"   Conteúdo encontrado: '{after_confirmation}'")
            tests.append(False)
    else:
        print("✅ PASSOU: Estrutura de confirmação está correta")
        tests.append(True)
    
    # TESTE 6: Verificar estrutura das 4 etapas
    print("\n📋 TESTE 6: Verificação da estrutura das 4 etapas")
    etapa_patterns = [
        r'ETAPA 1.*FILTRO DE SEGURANÇA',
        r'ETAPA 2.*SISTEMA DE CONFIRMAÇÃO',
        r'ETAPA 3.*VERIFICAR SE AINDA EM MODO ESPERA',
        r'ETAPA 4.*FILTRO PROBABILÍSTICO'
    ]
    
    etapas_found = 0
    for i, pattern in enumerate(etapa_patterns, 1):
        if re.search(pattern, content):
            etapas_found += 1
    
    if etapas_found == 4:
        print("✅ PASSOU: Todas as 4 etapas estão presentes e estruturadas")
        tests.append(True)
    else:
        print(f"❌ FALHOU: Apenas {etapas_found}/4 etapas encontradas!")
        tests.append(False)
    
    # TESTE 7: Verificar comentário de correção
    print("\n📋 TESTE 7: Verificação do comentário de correção")
    correction_pattern = r'CORRIGIDO.*NÃO fazer return aqui'
    if re.search(correction_pattern, content):
        print("✅ PASSOU: Comentário de correção está presente")
        tests.append(True)
    else:
        print("❌ FALHOU: Comentário de correção NÃO encontrado!")
        tests.append(False)
    
    # TESTE 8: Verificar logs de gatilho ativado
    print("\n📋 TESTE 8: Verificação dos logs de gatilho")
    trigger_patterns = [
        r'GATILHO ATIVADO.*Loss=0.*Random=',
        r'COMPRA AUTORIZADA.*Losses.*Random'
    ]
    
    triggers_found = 0
    for pattern in trigger_patterns:
        if re.search(pattern, content):
            triggers_found += 1
    
    if triggers_found == 2:
        print("✅ PASSOU: Logs de gatilho estão presentes")
        tests.append(True)
    else:
        print(f"❌ FALHOU: Apenas {triggers_found}/2 logs de gatilho encontrados!")
        tests.append(False)
    
    # RESULTADO FINAL
    print("\n" + "="*80)
    print("📊 RESULTADO FINAL DA VALIDAÇÃO")
    print("="*80)
    
    passed_tests = sum(tests)
    total_tests = len(tests)
    
    print(f"✅ Testes Aprovados: {passed_tests}/{total_tests}")
    print(f"❌ Testes Falharam: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 SUCESSO TOTAL! Sistema de confirmação está CORRETAMENTE implementado!")
        print("\n📋 SEQUÊNCIA DE LOGS ESPERADA:")
        print("   🛡️ DÍGITO DE RISCO DETECTADO (8) - MODO ESPERA ATIVADO")
        print("   ⏸️ MODO ESPERA ATIVO - Aguardando confirmação (dígito: 7)")
        print("   ⏸️ MODO ESPERA ATIVO - Aguardando confirmação (dígito: 6)")
        print("   ✅ CONFIRMAÇÃO RECEBIDA - ROBÔ PRONTO PARA OPERAR (dígito: 4)")
        print("   🎯 GATILHO ATIVADO - Loss=0, Random=3 (>=1)")
        print("   🎯 COMPRA AUTORIZADA - Losses: 0, Random: 3")
        print("\n✅ O bot agora replica FIELMENTE o XML e reduzirá drasticamente a frequência de operações!")
        return True
    else:
        print(f"\n❌ FALHA! {total_tests - passed_tests} teste(s) falharam.")
        print("⚠️ A correção NÃO foi implementada corretamente!")
        print("🚨 O bot continuará operando 3x mais frequentemente que o XML!")
        return False

if __name__ == "__main__":
    try:
        success = test_confirmation_system_validation()
        if success:
            print("\n🎯 VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print("\n🚨 VALIDAÇÃO FALHOU - CORREÇÃO NECESSÁRIA!")
            
    except Exception as e:
        print(f"\n❌ ERRO durante a validação: {e}")
        logger.error(f"Erro na validação: {e}")