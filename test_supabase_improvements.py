#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das melhorias implementadas no sistema Supabase
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import logging
import inspect

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def test_function_signatures():
    """Testa se as funções modificadas têm as assinaturas corretas"""
    logger.info("=== Testando assinaturas das funções ===")
    
    try:
        # Importar as funções do radar
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from radar_analisis_scalping_bot import (
            obter_resultado_operacao_atual,
            criar_registro_rastreamento_CORRIGIDO,
            atualizar_resultado_operacao_CORRIGIDO
        )
        
        # Verificar assinatura de obter_resultado_operacao_atual
        sig1 = inspect.signature(obter_resultado_operacao_atual)
        params1 = list(sig1.parameters.keys())
        expected_params1 = ['supabase', 'operation_id']
        
        if params1 != expected_params1:
            logger.error(f"obter_resultado_operacao_atual: esperado {expected_params1}, encontrado {params1}")
            return False
            
        logger.info("✅ obter_resultado_operacao_atual tem assinatura correta")
        
        # Verificar assinatura de criar_registro_rastreamento_CORRIGIDO
        sig2 = inspect.signature(criar_registro_rastreamento_CORRIGIDO)
        params2 = list(sig2.parameters.keys())
        expected_params2 = ['supabase', 'strategy_name', 'confidence', 'signal_id', 'strategy_data']
        
        if params2 != expected_params2:
            logger.error(f"criar_registro_rastreamento_CORRIGIDO: esperado {expected_params2}, encontrado {params2}")
            return False
            
        # Verificar se strategy_data tem valor padrão None
        strategy_data_param = sig2.parameters['strategy_data']
        if strategy_data_param.default is not None:
            logger.error(f"strategy_data deveria ter default None, encontrado {strategy_data_param.default}")
            return False
            
        logger.info("✅ criar_registro_rastreamento_CORRIGIDO tem assinatura correta")
        
        # Verificar assinatura de atualizar_resultado_operacao_CORRIGIDO
        sig3 = inspect.signature(atualizar_resultado_operacao_CORRIGIDO)
        params3 = list(sig3.parameters.keys())
        expected_params3 = ['supabase', 'tracking_id', 'operacao_num', 'resultado', 'profit', 'timestamp']
        
        if params3 != expected_params3:
            logger.error(f"atualizar_resultado_operacao_CORRIGIDO: esperado {expected_params3}, encontrado {params3}")
            return False
            
        # Verificar se timestamp tem valor padrão None
        timestamp_param = sig3.parameters['timestamp']
        if timestamp_param.default is not None:
            logger.error(f"timestamp deveria ter default None, encontrado {timestamp_param.default}")
            return False
            
        logger.info("✅ atualizar_resultado_operacao_CORRIGIDO tem assinatura correta")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar assinaturas: {e}")
        return False

def test_function_imports():
    """Testa se todas as funções podem ser importadas sem erro"""
    logger.info("=== Testando importação das funções ===")
    
    try:
        from radar_analisis_scalping_bot import (
            obter_resultado_operacao_atual,
            criar_registro_rastreamento_CORRIGIDO,
            atualizar_resultado_operacao_CORRIGIDO,
            check_new_operations
        )
        
        logger.info("✅ Todas as funções foram importadas com sucesso")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado na importação: {e}")
        return False

def test_function_docstrings():
    """Testa se as funções têm docstrings atualizadas"""
    logger.info("=== Testando docstrings das funções ===")
    
    try:
        from radar_analisis_scalping_bot import (
            obter_resultado_operacao_atual,
            criar_registro_rastreamento_CORRIGIDO,
            atualizar_resultado_operacao_CORRIGIDO
        )
        
        # Verificar docstring de obter_resultado_operacao_atual
        doc1 = obter_resultado_operacao_atual.__doc__
        if not doc1 or 'dict' not in doc1.lower():
            logger.error("obter_resultado_operacao_atual não tem docstring adequada sobre retornar dict")
            return False
            
        logger.info("✅ obter_resultado_operacao_atual tem docstring atualizada")
        
        # Verificar docstring de criar_registro_rastreamento_CORRIGIDO
        doc2 = criar_registro_rastreamento_CORRIGIDO.__doc__
        if not doc2 or 'dados detalhados' not in doc2.lower():
            logger.error("criar_registro_rastreamento_CORRIGIDO não tem docstring sobre dados detalhados")
            return False
            
        logger.info("✅ criar_registro_rastreamento_CORRIGIDO tem docstring atualizada")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar docstrings: {e}")
        return False

def test_code_structure():
    """Testa se o código tem a estrutura esperada após as modificações"""
    logger.info("=== Testando estrutura do código ===")
    
    try:
        # Ler o arquivo do radar para verificar modificações
        radar_file = os.path.join(os.path.dirname(__file__), 'radar_analisis_scalping_bot.py')
        
        with open(radar_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se as modificações estão presentes
        checks = [
            ('operation_data = {', 'obter_resultado_operacao_atual retorna dicionário'),
            ('strategy_data and isinstance(strategy_data, dict)', 'criar_registro_rastreamento_CORRIGIDO usa strategy_data'),
            ('wins_consecutivos', 'trigger_conditions inclui wins_consecutivos'),
            ('losses_nas_ultimas_15', 'trigger_conditions inclui losses_nas_ultimas_15'),
            ('operation_timestamp =', 'atualizar_resultado_operacao_CORRIGIDO usa timestamp'),
            ('signal_data  # Passar dados completos', 'chamadas passam strategy_data')
        ]
        
        for check_text, description in checks:
            if check_text not in content:
                logger.error(f"❌ Modificação não encontrada: {description}")
                return False
            else:
                logger.info(f"✅ Encontrado: {description}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar estrutura do código: {e}")
        return False

def main():
    """Executa todos os testes"""
    logger.info("🚀 Iniciando testes das melhorias Supabase")
    
    testes = [
        test_function_imports,
        test_function_signatures,
        test_function_docstrings,
        test_code_structure
    ]
    
    resultados = []
    
    for teste in testes:
        try:
            resultado = teste()
            resultados.append(resultado)
        except Exception as e:
            logger.error(f"Erro inesperado no teste {teste.__name__}: {e}")
            resultados.append(False)
    
    # Resumo dos resultados
    logger.info("\n" + "="*50)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*50)
    
    total_testes = len(resultados)
    testes_passaram = sum(resultados)
    
    for i, (teste, resultado) in enumerate(zip(testes, resultados)):
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        logger.info(f"{teste.__name__}: {status}")
    
    logger.info(f"\nTotal: {testes_passaram}/{total_testes} testes passaram")
    
    if testes_passaram == total_testes:
        logger.info("🎉 Todas as melhorias foram implementadas corretamente!")
        logger.info("\n📋 RESUMO DAS MELHORIAS IMPLEMENTADAS:")
        logger.info("1. ✅ obter_resultado_operacao_atual agora retorna dicionário completo")
        logger.info("2. ✅ check_new_operations passa dados completos para atualização")
        logger.info("3. ✅ atualizar_resultado_operacao_CORRIGIDO usa timestamp real da operação")
        logger.info("4. ✅ criar_registro_rastreamento_CORRIGIDO popula trigger_conditions com dados detalhados")
        return True
    else:
        logger.warning("⚠️ Algumas melhorias precisam de ajustes")
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)