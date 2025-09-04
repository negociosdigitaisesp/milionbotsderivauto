#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debugar as variáveis de ambiente
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=== DEBUG VARIÁVEIS DE AMBIENTE ===")
print(f"DERIV_APP_ID: {os.getenv('DERIV_APP_ID')}")
print(f"DERIV_API_TOKEN: {os.getenv('DERIV_API_TOKEN')[:10]}...{os.getenv('DERIV_API_TOKEN')[-4:] if os.getenv('DERIV_API_TOKEN') else 'None'}")
print(f"DERIV_TOKEN: {os.getenv('DERIV_TOKEN')[:10]}...{os.getenv('DERIV_TOKEN')[-4:] if os.getenv('DERIV_TOKEN') else 'None'}")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY: {'Configurado' if os.getenv('SUPABASE_KEY') else 'Não configurado'}")

# Verificar se há outros arquivos .env
print("\n=== ARQUIVOS .env ENCONTRADOS ===")
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.startswith('.env'):
            print(f"Encontrado: {os.path.join(root, file)}")