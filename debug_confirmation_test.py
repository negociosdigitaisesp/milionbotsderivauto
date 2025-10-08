#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DEBUG TEST - Identificar exatamente onde está o return problemático
"""

import re

def debug_confirmation_section():
    """Debug detalhado da seção de confirmação"""
    
    with open("tunderbotalavanca.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("="*80)
    print("🔍 DEBUG - ANÁLISE DETALHADA DA SEÇÃO DE CONFIRMAÇÃO")
    print("="*80)
    
    # Encontrar a seção completa de confirmação
    confirmation_match = re.search(r'CONFIRMAÇÃO RECEBIDA.*?ETAPA 3.*?ETAPA 4', content, re.DOTALL)
    
    if confirmation_match:
        section = confirmation_match.group(0)
        print("📋 SEÇÃO ENCONTRADA:")
        print("-" * 60)
        
        # Dividir em linhas e numerar
        lines = section.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:2d}: {line}")
        
        print("-" * 60)
        
        # Procurar por returns na seção
        return_matches = list(re.finditer(r'return', section))
        
        if return_matches:
            print(f"\n🚨 ENCONTRADOS {len(return_matches)} RETURN(S) NA SEÇÃO:")
            for i, match in enumerate(return_matches, 1):
                start = max(0, match.start() - 50)
                end = min(len(section), match.end() + 50)
                context = section[start:end]
                print(f"\nReturn {i}:")
                print(f"Contexto: ...{context}...")
        else:
            print("\n✅ NENHUM RETURN ENCONTRADO NA SEÇÃO DE CONFIRMAÇÃO")
    
    # Análise mais específica - procurar return imediatamente após confirmação
    print("\n" + "="*60)
    print("🔍 ANÁLISE ESPECÍFICA - RETURN APÓS CONFIRMAÇÃO")
    print("="*60)
    
    # Padrão mais específico
    pattern = r'CONFIRMAÇÃO RECEBIDA.*?\n.*?# ✅ CORRIGIDO.*?\n(.*?)(?=\n.*?# ETAPA 3)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        after_confirmation = match.group(1)
        print("📋 CONTEÚDO APÓS CONFIRMAÇÃO (antes da ETAPA 3):")
        print(f"'{after_confirmation}'")
        
        if 'return' in after_confirmation:
            print("🚨 RETURN PROBLEMÁTICO ENCONTRADO!")
        else:
            print("✅ NENHUM RETURN PROBLEMÁTICO ENCONTRADO")
    else:
        print("❌ Não foi possível encontrar a seção específica")

if __name__ == "__main__":
    debug_confirmation_section()