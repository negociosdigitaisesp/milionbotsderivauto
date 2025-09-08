#!/usr/bin/env python3
"""
Script de Teste para as Estratégias do Scalping Bot
Valida o funcionamento das 3 estratégias com dados simulados
"""

import sys
import os
from datetime import datetime
import random
from typing import List, Dict

# Adicionar o diretório atual ao path para importar o bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar funções do bot principal
try:
    from radar_analisis_scalping_bot import (
        analisar_micro_burst,
        analisar_precision_surge,
        analisar_quantum_matrix,
        validar_integridade_historico,
        strategy_metrics
    )
    print("✅ Módulos do bot importados com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar módulos do bot: {e}")
    sys.exit(1)

# ===== DADOS DE TESTE =====

# Cenários de teste para MICRO-BURST
MICRO_BURST_TEST_CASES = {
    'cenario_ideal': {
        'historico': ['V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': True,
        'descricao': '2 WINs consecutivos, 1 LOSS isolado em 10 ops'
    },
    'cenario_3_wins': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': True,
        'descricao': '3 WINs consecutivos, sem LOSSes'
    },
    'cenario_muitos_wins': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '4+ WINs consecutivos (deve falhar)'
    },
    'cenario_losses_consecutivos': {
        'historico': ['V', 'V', 'D', 'D', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '2 WINs + LOSSes consecutivos (deve falhar)'
    },
    'cenario_muitos_losses': {
        'historico': ['V', 'V', 'D', 'V', 'D', 'V', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '2 WINs + 2 LOSSes em 10 ops (deve falhar)'
    }
}

# Cenários de teste para PRECISION SURGE
PRECISION_SURGE_TEST_CASES = {
    'cenario_ideal': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': True,
        'descricao': '4 WINs consecutivos, ambiente estável'
    },
    'cenario_5_wins': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V'],
        'esperado': True,
        'descricao': '5 WINs consecutivos, 1 LOSS em 15 ops'
    },
    'cenario_poucos_wins': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '3 WINs consecutivos (deve falhar)'
    },
    'cenario_losses_consecutivos': {
        'historico': ['V', 'V', 'V', 'V', 'D', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '4 WINs + LOSSes consecutivos (deve falhar)'
    },
    'cenario_ambiente_instavel': {
        'historico': ['V', 'V', 'V', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'V'],
        'esperado': False,
        'descricao': '4 WINs + ambiente instável (deve falhar)'
    }
}

# Cenários de teste para QUANTUM MATRIX
QUANTUM_MATRIX_TEST_CASES = {
    'cenario_6_wins': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': True,
        'descricao': '6+ WINs consecutivos, ambiente ultra-estável'
    },
    'cenario_recovery': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': True,
        'descricao': 'Recovery sólido: 3 WINs + LOSS há 7 operações'
    },
    'cenario_poucos_wins': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '5 WINs consecutivos (deve falhar)'
    },
    'cenario_loss_recente': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '6 WINs + LOSS muito recente (deve falhar)'
    },
    'cenario_ambiente_nao_ultra_estavel': {
        'historico': ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'D', 'V', 'V', 'V', 'V'],
        'esperado': False,
        'descricao': '6 WINs + ambiente não ultra-estável (deve falhar)'
    }
}

# ===== FUNÇÕES DE TESTE =====

def gerar_historico_aleatorio(tamanho: int, win_rate: float = 0.75) -> List[str]:
    """Gera histórico aleatório com win rate específico"""
    historico = []
    for _ in range(tamanho):
        if random.random() < win_rate:
            historico.append('V')
        else:
            historico.append('D')
    return historico

def testar_estrategia(nome_estrategia: str, funcao_analise, casos_teste: Dict) -> Dict:
    """Testa uma estratégia com casos específicos"""
    print(f"\n{'='*60}")
    print(f"TESTANDO ESTRATÉGIA: {nome_estrategia}")
    print(f"{'='*60}")
    
    resultados = {
        'total_casos': len(casos_teste),
        'sucessos': 0,
        'falhas': 0,
        'detalhes': []
    }
    
    for nome_caso, caso in casos_teste.items():
        print(f"\n🧪 Testando: {nome_caso}")
        print(f"📝 Descrição: {caso['descricao']}")
        print(f"📊 Histórico: {' '.join(caso['historico'])}")
        
        try:
            resultado = funcao_analise(caso['historico'])
            sucesso = resultado['should_operate'] == caso['esperado']
            
            if sucesso:
                print(f"✅ PASSOU - Resultado: {resultado['should_operate']} (esperado: {caso['esperado']})")
                resultados['sucessos'] += 1
            else:
                print(f"❌ FALHOU - Resultado: {resultado['should_operate']} (esperado: {caso['esperado']})")
                resultados['falhas'] += 1
            
            print(f"📋 Motivo: {resultado['reason']}")
            
            resultados['detalhes'].append({
                'caso': nome_caso,
                'sucesso': sucesso,
                'resultado_obtido': resultado['should_operate'],
                'resultado_esperado': caso['esperado'],
                'motivo': resultado['reason']
            })
            
        except Exception as e:
            print(f"💥 ERRO na execução: {e}")
            resultados['falhas'] += 1
            resultados['detalhes'].append({
                'caso': nome_caso,
                'sucesso': False,
                'erro': str(e)
            })
    
    # Resumo da estratégia
    taxa_sucesso = (resultados['sucessos'] / resultados['total_casos']) * 100
    print(f"\n📊 RESUMO {nome_estrategia}:")
    print(f"   • Total de casos: {resultados['total_casos']}")
    print(f"   • Sucessos: {resultados['sucessos']}")
    print(f"   • Falhas: {resultados['falhas']}")
    print(f"   • Taxa de sucesso: {taxa_sucesso:.1f}%")
    
    return resultados

def testar_validacao_integridade():
    """Testa função de validação de integridade"""
    print(f"\n{'='*60}")
    print("TESTANDO VALIDAÇÃO DE INTEGRIDADE")
    print(f"{'='*60}")
    
    casos_teste = {
        'historico_valido': {
            'dados': ['V', 'D', 'V', 'V', 'D', 'V', 'V', 'V', 'D', 'V'] * 3,
            'esperado': True
        },
        'historico_vazio': {
            'dados': [],
            'esperado': False
        },
        'historico_curto': {
            'dados': ['V', 'D', 'V'],
            'esperado': False
        },
        'dados_invalidos': {
            'dados': ['V', 'X', 'D', 'Y', 'V'],
            'esperado': False
        },
        'apenas_wins': {
            'dados': ['V'] * 25,
            'esperado': False
        },
        'apenas_losses': {
            'dados': ['D'] * 25,
            'esperado': False
        }
    }
    
    sucessos = 0
    total = len(casos_teste)
    
    for nome_caso, caso in casos_teste.items():
        print(f"\n🧪 Testando: {nome_caso}")
        try:
            resultado = validar_integridade_historico(caso['dados'])
            sucesso = resultado == caso['esperado']
            
            if sucesso:
                print(f"✅ PASSOU - Resultado: {resultado} (esperado: {caso['esperado']})")
                sucessos += 1
            else:
                print(f"❌ FALHOU - Resultado: {resultado} (esperado: {caso['esperado']})")
                
        except Exception as e:
            print(f"💥 ERRO: {e}")
    
    taxa_sucesso = (sucessos / total) * 100
    print(f"\n📊 RESUMO VALIDAÇÃO:")
    print(f"   • Taxa de sucesso: {taxa_sucesso:.1f}% ({sucessos}/{total})")
    
    return taxa_sucesso

def teste_stress_performance():
    """Teste de stress e performance"""
    print(f"\n{'='*60}")
    print("TESTE DE STRESS E PERFORMANCE")
    print(f"{'='*60}")
    
    import time
    
    # Gerar dados de teste
    historicos_teste = []
    for _ in range(100):
        historico = gerar_historico_aleatorio(30, random.uniform(0.6, 0.9))
        historicos_teste.append(historico)
    
    estrategias = [
        ('MICRO_BURST', analisar_micro_burst),
        ('PRECISION_SURGE', analisar_precision_surge),
        ('QUANTUM_MATRIX', analisar_quantum_matrix)
    ]
    
    for nome_estrategia, funcao in estrategias:
        print(f"\n🚀 Testando performance: {nome_estrategia}")
        
        start_time = time.time()
        sucessos = 0
        erros = 0
        
        for i, historico in enumerate(historicos_teste):
            try:
                resultado = funcao(historico)
                if resultado['should_operate']:
                    sucessos += 1
            except Exception as e:
                erros += 1
                if i < 5:  # Mostrar apenas os primeiros erros
                    print(f"   ❌ Erro no teste {i+1}: {e}")
        
        end_time = time.time()
        tempo_total = end_time - start_time
        tempo_medio = tempo_total / len(historicos_teste)
        
        print(f"   ⏱️  Tempo total: {tempo_total:.3f}s")
        print(f"   📊 Tempo médio por análise: {tempo_medio:.4f}s")
        print(f"   ✅ Sinais gerados: {sucessos}/100")
        print(f"   ❌ Erros: {erros}/100")
        print(f"   📈 Taxa de detecção: {sucessos}%")

def main():
    """Função principal de teste"""
    print("🧪 INICIANDO TESTES DO SCALPING BOT")
    print(f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)
    
    # Resetar métricas
    for metrics in strategy_metrics.values():
        metrics.total_executions = 0
        metrics.successful_triggers = 0
        metrics.failed_triggers = 0
        metrics.error_count = 0
        metrics.filter_rejections.clear()
        metrics.execution_times.clear()
    
    resultados_gerais = {
        'micro_burst': None,
        'precision_surge': None,
        'quantum_matrix': None,
        'validacao': None
    }
    
    try:
        # Testar cada estratégia
        resultados_gerais['micro_burst'] = testar_estrategia(
            'MICRO_BURST', analisar_micro_burst, MICRO_BURST_TEST_CASES
        )
        
        resultados_gerais['precision_surge'] = testar_estrategia(
            'PRECISION_SURGE', analisar_precision_surge, PRECISION_SURGE_TEST_CASES
        )
        
        resultados_gerais['quantum_matrix'] = testar_estrategia(
            'QUANTUM_MATRIX', analisar_quantum_matrix, QUANTUM_MATRIX_TEST_CASES
        )
        
        # Testar validação
        resultados_gerais['validacao'] = testar_validacao_integridade()
        
        # Teste de performance
        teste_stress_performance()
        
        # Resumo final
        print(f"\n{'='*60}")
        print("RESUMO FINAL DOS TESTES")
        print(f"{'='*60}")
        
        total_casos = 0
        total_sucessos = 0
        
        for nome, resultado in resultados_gerais.items():
            if isinstance(resultado, dict):
                taxa = (resultado['sucessos'] / resultado['total_casos']) * 100
                print(f"📊 {nome.upper()}: {taxa:.1f}% ({resultado['sucessos']}/{resultado['total_casos']})")
                total_casos += resultado['total_casos']
                total_sucessos += resultado['sucessos']
            elif isinstance(resultado, (int, float)):
                print(f"📊 {nome.upper()}: {resultado:.1f}%")
        
        if total_casos > 0:
            taxa_geral = (total_sucessos / total_casos) * 100
            print(f"\n🎯 TAXA GERAL DE SUCESSO: {taxa_geral:.1f}% ({total_sucessos}/{total_casos})")
        
        # Métricas das estratégias
        print(f"\n📈 MÉTRICAS DE EXECUÇÃO:")
        for nome, metrics in strategy_metrics.items():
            if metrics.total_executions > 0:
                print(f"   • {nome}: {metrics.total_executions} execuções, {metrics.get_average_time():.4f}s médio")
        
        print(f"\n✅ TESTES CONCLUÍDOS COM SUCESSO!")
        
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)