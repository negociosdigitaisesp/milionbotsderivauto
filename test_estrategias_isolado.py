#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste isolado das estratégias sem conexão Supabase
Para identificar se o problema está no decorator ou na conexão
"""

import sys
import os
import time
from datetime import datetime

# Adicionar o diretório atual ao path para importar radar_analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar apenas as funções necessárias
from radar_analyzer import analisar_estrategias_portfolio

def testar_estrategias_com_dados_mockados():
    """
    Testa as estratégias com dados conhecidos que deveriam ativar pelo menos uma estratégia
    """
    print("\n" + "="*70)
    print("TESTE ISOLADO DAS ESTRATÉGIAS - SEM SUPABASE")
    print("="*70)
    
    # Dados do usuário: D V V V V V V V V V V V V V V V V V V V V V D V V
    # 30 operações, 90% win rate, LOSS isolada na posição 0
    historico_teste = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 
                       'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 
                       'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    
    print(f"Histórico de teste ({len(historico_teste)} operações):")
    print(f"{''.join(historico_teste[:10])}...")
    print(f"Win rate: {(historico_teste.count('V') / len(historico_teste)) * 100:.1f}%")
    print(f"Padrão: LOSS isolada na posição 0, seguida de WINs")
    print("\nEste padrão deveria ativar pelo menos 2-3 estratégias...\n")
    
    try:
        print("[TESTE] Iniciando análise das estratégias...")
        start_time = time.time()
        
        # Chamar a função principal de análise
        resultado = analisar_estrategias_portfolio(historico_teste)
        
        execution_time = time.time() - start_time
        print(f"\n[TESTE] Análise concluída em {execution_time:.3f}s")
        
        # Exibir resultados
        print("\n" + "-"*50)
        print("RESULTADOS DO TESTE:")
        print("-"*50)
        
        if resultado:
            print(f"✓ Função executada com sucesso")
            print(f"Should operate: {resultado.get('should_operate', 'N/A')}")
            print(f"Reason: {resultado.get('reason', 'N/A')}")
            
            if resultado.get('melhor_estrategia'):
                melhor = resultado['melhor_estrategia']
                print(f"\n✓ Melhor estratégia: {melhor.get('strategy', 'N/A')}")
                print(f"  Confiança: {melhor.get('confidence', 0)}%")
                print(f"  Risk level: {melhor.get('risk_level', 'N/A')}")
            
            if resultado.get('estrategias_disponiveis'):
                print(f"\n✓ Total de estratégias disponíveis: {len(resultado['estrategias_disponiveis'])}")
                for i, estrategia in enumerate(resultado['estrategias_disponiveis'][:3]):
                    print(f"  {i+1}. {estrategia.get('strategy', 'N/A')} - {estrategia.get('confidence', 0)}%")
        else:
            print("X Função retornou None - possível erro")
            
    except Exception as e:
        print(f"\nX ERRO durante o teste: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    print("\n" + "="*70)
    print("TESTE CONCLUÍDO")
    print("="*70)

if __name__ == "__main__":
    testar_estrategias_com_dados_mockados()