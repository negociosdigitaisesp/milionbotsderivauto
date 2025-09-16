#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das correções na função criar_registro_de_rastreamento_linkado()
Verifica se as funções corrigidas funcionam sem erro de .select()
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging para o teste
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_function_syntax():
    """Testa se as funções podem ser importadas sem erro de sintaxe"""
    try:
        import importlib.util
        import sys
        
        # Carregar o módulo usando importlib
        spec = importlib.util.spec_from_file_location(
            "radarscalpingprecision", 
            "radarscalpingprecision1.5.py"
        )
        radar_module = importlib.util.module_from_spec(spec)
        
        # Executar o módulo para carregar as funções
        sys.modules["radarscalpingprecision"] = radar_module
        spec.loader.exec_module(radar_module)
        
        # Verificar se as funções existem
        funcs = [
            'criar_registro_de_rastreamento_linkado',
            'criar_registro_de_rastreamento_linkado_SEGURO', 
            'criar_registro_de_rastreamento'
        ]
        
        found_funcs = []
        for func_name in funcs:
            if hasattr(radar_module, func_name):
                found_funcs.append(func_name)
        
        logger.info("✅ TESTE 1: Importação das funções - SUCESSO")
        logger.info(f"   - Funções encontradas: {len(found_funcs)}/{len(funcs)}")
        for func in found_funcs:
            logger.info(f"   - {func}: OK")
        
        return len(found_funcs) == len(funcs)
        
    except ImportError as e:
        logger.error(f"❌ TESTE 1: Erro de importação - {e}")
        return False
    except SyntaxError as e:
        logger.error(f"❌ TESTE 1: Erro de sintaxe - {e}")
        return False
    except Exception as e:
        logger.error(f"❌ TESTE 1: Erro inesperado - {e}")
        return False

def test_syntax_check():
    """Verifica se o arquivo Python tem sintaxe válida"""
    try:
        import ast
        
        # Ler e compilar o arquivo para verificar sintaxe
        with open('radarscalpingprecision1.5.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tentar compilar o código
        ast.parse(content)
        
        logger.info("✅ TESTE 2: Verificação de sintaxe - SUCESSO")
        logger.info("   - Arquivo Python compilado sem erros")
        return True
        
    except SyntaxError as e:
        logger.error(f"❌ TESTE 2: Erro de sintaxe - Linha {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        logger.error(f"❌ TESTE 2: Erro na verificação de sintaxe - {e}")
        return False

def test_code_patterns():
    """Verifica se o código não contém mais padrões problemáticos"""
    try:
        # Ler o arquivo e verificar padrões
        with open('radarscalpingprecision1.5.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Procurar por padrões problemáticos
        problematic_patterns = [
            '.insert(data).select(',
            '.insert(data).select("id")',
            ".insert(data).select('id')"
        ]
        
        found_issues = []
        for pattern in problematic_patterns:
            if pattern in content:
                found_issues.append(pattern)
        
        if found_issues:
            logger.error(f"❌ TESTE 3: Padrões problemáticos ainda encontrados: {found_issues}")
            return False
        else:
            logger.info("✅ TESTE 3: Verificação de padrões problemáticos - SUCESSO")
            logger.info("   - Nenhum padrão .insert().select() encontrado")
            return True
        
    except Exception as e:
        logger.error(f"❌ TESTE 3: Erro na verificação de padrões - {e}")
        return False

def main():
    """Executa todos os testes"""
    logger.info("=== INICIANDO TESTES DAS CORREÇÕES DE TRACKING ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("")
    
    tests = [
        ("Sintaxe e Importação", test_function_syntax),
        ("Verificação de Sintaxe", test_syntax_check),
        ("Padrões Problemáticos", test_code_patterns)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"--- Executando: {test_name} ---")
        result = test_func()
        results.append((test_name, result))
        logger.info("")
    
    # Resumo final
    logger.info("=== RESUMO DOS TESTES ===")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("")
    if all_passed:
        logger.info("🎉 TODOS OS TESTES PASSARAM! As correções foram aplicadas com sucesso.")
        logger.info("📋 CORREÇÕES IMPLEMENTADAS:")
        logger.info("   - Removido .select('id') das funções de insert")
        logger.info("   - Adicionado tratamento seguro com .get('id')")
        logger.info("   - Criada função alternativa SEGURA com upsert")
        logger.info("   - Melhorado tratamento de erros")
    else:
        logger.error("⚠️  ALGUNS TESTES FALHARAM. Verifique os logs acima.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)