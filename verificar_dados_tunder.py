#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from supabase import create_client
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Conectar ao Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Buscar dados da tabela tunder_bot_logs
response = supabase.table('tunder_bot_logs') \
    .select('id, operation_result, timestamp') \
    .order('timestamp', desc=True) \
    .limit(35) \
    .execute()

if not response.data:
    logger.warning("Nenhum dado encontrado na tabela tunder_bot_logs")
    exit(1)

# Mostrar os dados brutos
print("\n=== DADOS BRUTOS DA TABELA tunder_bot_logs ===")
for i, op in enumerate(response.data[:10]):  # Mostrar apenas os 10 primeiros para não sobrecarregar
    print(f"{i+1}. ID: {op['id']}, Resultado: {op['operation_result']}, Timestamp: {op['timestamp']}")

# Traduzir e mostrar os resultados como o bot faz
historico_raw = [op['operation_result'] for op in response.data]
historico_traduzido = ['WIN' if res == 'V' else 'LOSS' for res in historico_raw]

print("\n=== DADOS TRADUZIDOS (como o bot interpreta) ===")
print(f"Últimas 3 operações: {historico_traduzido[:3]}")
print(f"Últimas 10 operações: {historico_traduzido[:10]}")

# Verificar se o padrão LLL está presente
gatilho_lll = ['LOSS', 'LOSS', 'LOSS']
padrao_encontrado = (historico_traduzido[:3] == gatilho_lll)

print(f"\n=== ANÁLISE DO PADRÃO ===")
print(f"Padrão LLL encontrado: {padrao_encontrado}")
print(f"Primeiras 3 operações: {historico_traduzido[:3]}")

# Verificar se há algum problema de tradução
print("\n=== VERIFICAÇÃO DE TRADUÇÃO ===")
for i, (raw, traduzido) in enumerate(zip(historico_raw[:10], historico_traduzido[:10])):
    print(f"{i+1}. Original: '{raw}' -> Traduzido: '{traduzido}'")
    if (raw == 'V' and traduzido != 'WIN') or (raw != 'V' and traduzido != 'LOSS'):
        print(f"   ⚠️ ERRO DE TRADUÇÃO DETECTADO!")