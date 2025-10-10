#!/usr/bin/env python3
"""
Teste de Integração Completa - RadarTunder 3.5
Verifica se todas as classes e funções funcionam em conjunto corretamente.
"""

import sys
import os
import importlib.util
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulo com ponto no nome usando importlib
spec = importlib.util.spec_from_file_location("radartunder35", "radartunder3.5.py")
radartunder35 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radartunder35)

# Importar classes e funções
MartingaleAnalyzer = radartunder35.MartingaleAnalyzer
RiskDetector = radartunder35.RiskDetector
analisar_estrategia_momentum_calmo = radartunder35.analisar_estrategia_momentum_calmo
validacao_cruzada_martingale = radartunder35.validacao_cruzada_martingale
analisar_dados_martingale_banco = radartunder35.analisar_dados_martingale_banco
from datetime import datetime
import logging

# Configurar logging para o teste
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fluxo_completo_integracao():
    """
    Testa o fluxo completo de integração entre todas as classes e funções.
    """
    print("🧪 INICIANDO TESTE DE INTEGRAÇÃO COMPLETA")
    print("=" * 60)
    
    # Dados de teste simulando operações reais
    historico_teste = ['LOSS', 'LOSS', 'WIN', 'LOSS', 'WIN', 'LOSS', 'LOSS', 'LOSS', 'WIN', 'LOSS',
                       'WIN', 'LOSS', 'LOSS', 'WIN', 'LOSS', 'WIN', 'WIN', 'LOSS', 'LOSS', 'WIN']
    
    operacoes_detalhadas_teste = [
        {
            'id': i,
            'resultado': resultado,
            'timestamp': datetime.now().isoformat(),
            'martingale_level': 1 if resultado == 'WIN' else min(i % 3 + 1, 3),
            'profit_loss': 10.0 if resultado == 'WIN' else -10.0
        }
        for i, resultado in enumerate(historico_teste)
    ]
    
    try:
        print("\n1️⃣ TESTANDO MARTINGALE ANALYZER")
        print("-" * 40)
        
        # Teste 1: MartingaleAnalyzer
        martingale_analyzer = MartingaleAnalyzer()
        analise_propria = martingale_analyzer.calculate_hit_statistics(historico_teste)
        
        print(f"✅ MartingaleAnalyzer - Análise própria calculada")
        print(f"   - Win Rate: {analise_propria.get('win_rate', 0):.2f}%")
        print(f"   - Total Operações: {analise_propria.get('total_operations', 0)}")
        
        # Simular dados do banco
        dados_banco_simulados = {
            'sequencia_atual': {
                'nivel_atual': 2,
                'perdas_consecutivas': 1,
                'operacoes_nivel': [{'resultado': 'LOSS', 'timestamp': datetime.now().isoformat()}]
            },
            'estatisticas_banco': {
                'total_operacoes': len(operacoes_detalhadas_teste),
                'win_rate': 55.0,
                'frequencia_martingale': 0.35
            },
            'recomendacoes': {
                'nivel_risco': 'MEDIO',
                'motivo': 'Condições normais de mercado',
                'deve_operar': True
            },
            'fonte_dados': 'banco_supabase'
        }
        
        # Teste integração de dados
        analise_integrada = martingale_analyzer.integrar_dados_banco(dados_banco_simulados, analise_propria)
        print(f"✅ Integração de dados concluída")
        print(f"   - Fonte recomendada: {analise_integrada.get('fonte_recomendada', 'N/A')}")
        
        print("\n2️⃣ TESTANDO RISK DETECTOR")
        print("-" * 40)
        
        # Teste 2: RiskDetector
        risk_detector = RiskDetector()
        
        # Análise das últimas 20 operações
        analise_risco = risk_detector.analyze_last_20_operations(historico_teste)
        print(f"✅ Análise de risco concluída")
        print(f"   - Frequência Martingale: {analise_risco.get('martingale_frequency', 0):.2f}")
        print(f"   - Perdas consecutivas máx: {analise_risco.get('consecutive_losses_max', 0)}")
        print(f"   - Win Rate: {analise_risco.get('win_rate', 0):.2f}%")
        
        # Classificação de risco
        nivel_risco = risk_detector.classify_risk_level(analise_risco.get('martingale_frequency', 0))
        print(f"✅ Nível de risco classificado: {nivel_risco}")
        
        # Teste sinal 3MG
        sinal_3mg = risk_detector.generate_3mg_signal(historico_teste)
        print(f"✅ Análise 3MG concluída")
        print(f"   - Deve operar: {sinal_3mg.get('should_operate', False)}")
        print(f"   - Confiança: {sinal_3mg.get('confidence', 0):.1f}%")
        
        print("\n3️⃣ TESTANDO FUNÇÕES AUXILIARES")
        print("-" * 40)
        
        # Teste 3: Função de estratégia momentum calmo
        resultado_estrategia = analisar_estrategia_momentum_calmo(historico_teste, datetime.now().isoformat())
        print(f"✅ Estratégia momentum calmo analisada")
        print(f"   - Deve operar: {resultado_estrategia.get('should_operate', False)}")
        print(f"   - Razão: {resultado_estrategia.get('reason', 'N/A')}")
        
        # Teste 4: Validação cruzada
        validacao_cruzada = validacao_cruzada_martingale(dados_banco_simulados, historico_teste, operacoes_detalhadas_teste)
        print(f"✅ Validação cruzada concluída")
        print(f"   - Status: {validacao_cruzada.get('status_validacao', 'N/A')}")
        print(f"   - Fonte primária: {validacao_cruzada.get('recomendacao_final', {}).get('fonte_dados_primaria', 'N/A')}")
        print(f"   - Confiabilidade: {validacao_cruzada.get('metricas_confiabilidade', {}).get('confiabilidade_percentual', 0)}%")
        
        print("\n4️⃣ TESTANDO FLUXO INTEGRADO")
        print("-" * 40)
        
        # Teste 5: Fluxo integrado simulando o main_loop
        print("🔄 Simulando fluxo do main_loop...")
        
        # Simular decisão final baseada em todas as análises
        decisao_final = {
            'should_operate': resultado_estrategia.get('should_operate', False),
            'reason': resultado_estrategia.get('reason', ''),
            'risk_level': nivel_risco,
            'martingale_data': dados_banco_simulados,
            'risk_analysis': analise_risco,
            '3mg_signal': sinal_3mg,
            'validation_data': validacao_cruzada
        }
        
        # Aplicar filtros de segurança (simulando o main_loop)
        if nivel_risco == 'HIGH':
            decisao_final['should_operate'] = False
            decisao_final['reason'] = f"RISCO-ALTO: {decisao_final['reason']}"
            print("⚠️ Operação bloqueada por risco alto")
        elif sinal_3mg.get('should_operate', False) and not decisao_final['should_operate']:
            decisao_final['should_operate'] = True
            decisao_final['reason'] = f"3MG-DETECTADO: {sinal_3mg.get('reason', '')}"
            print("✅ Operação habilitada por padrão 3MG")
        
        print(f"✅ Decisão final: OPERAR = {decisao_final['should_operate']}")
        print(f"   - Razão: {decisao_final['reason']}")
        
        print("\n5️⃣ VERIFICAÇÃO DE COMPATIBILIDADE")
        print("-" * 40)
        
        # Verificar se todas as funções retornam dados no formato esperado
        verificacoes = []
        
        # Verificar MartingaleAnalyzer
        if isinstance(analise_propria, dict) and 'win_rate' in analise_propria:
            verificacoes.append("✅ MartingaleAnalyzer retorna formato correto")
        else:
            verificacoes.append("❌ MartingaleAnalyzer formato incorreto")
        
        # Verificar RiskDetector
        if isinstance(analise_risco, dict) and 'martingale_frequency' in analise_risco:
            verificacoes.append("✅ RiskDetector retorna formato correto")
        else:
            verificacoes.append("❌ RiskDetector formato incorreto")
        
        # Verificar função estratégia
        if isinstance(resultado_estrategia, dict) and 'should_operate' in resultado_estrategia:
            verificacoes.append("✅ Estratégia momentum retorna formato correto")
        else:
            verificacoes.append("❌ Estratégia momentum formato incorreto")
        
        # Verificar validação cruzada
        if isinstance(validacao_cruzada, dict) and 'status_validacao' in validacao_cruzada:
            verificacoes.append("✅ Validação cruzada retorna formato correto")
        else:
            verificacoes.append("❌ Validação cruzada formato incorreto")
        
        for verificacao in verificacoes:
            print(f"   {verificacao}")
        
        print("\n" + "=" * 60)
        print("🎉 TESTE DE INTEGRAÇÃO COMPLETA FINALIZADO")
        
        # Contar sucessos
        sucessos = len([v for v in verificacoes if v.startswith("✅")])
        total = len(verificacoes)
        
        print(f"📊 RESULTADO: {sucessos}/{total} verificações passaram")
        
        if sucessos == total:
            print("🟢 TODOS OS TESTES PASSARAM - INTEGRAÇÃO FUNCIONANDO CORRETAMENTE")
            return True
        else:
            print("🟡 ALGUNS TESTES FALHARAM - VERIFICAR COMPATIBILIDADE")
            return False
            
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE INTEGRAÇÃO: {str(e)}")
        logger.error(f"Erro no teste de integração: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    sucesso = test_fluxo_completo_integracao()
    exit(0 if sucesso else 1)