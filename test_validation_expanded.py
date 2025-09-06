#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar o sistema expandido de correções
"""

import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from radar_analyzer import validar_correcoes_sistema
    
    print("Iniciando teste de validação do sistema expandido...")
    print("="*80)
    
    # Executar a validação
    resultado = validar_correcoes_sistema()
    
    print("\n" + "="*80)
    if resultado:
        print("✅ TESTE CONCLUÍDO: Sistema aprovado!")
    else:
        print("❌ TESTE CONCLUÍDO: Sistema reprovado.")
        
except ImportError as e:
    print(f"Erro ao importar radar_analyzer: {e}")
except Exception as e:
    print(f"Erro durante a execução: {e}")
    import traceback
    traceback.print_exc()