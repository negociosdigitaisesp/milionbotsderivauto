#!/usr/bin/env python3
"""
Script para debugar configuração de logging - Teste específico
"""

import logging
import sys
import os

def check_handlers(stage):
    print(f"\n=== HANDLERS ATIVOS - {stage} ===")
    root_logger = logging.getLogger()
    for i, handler in enumerate(root_logger.handlers):
        print(f"Handler {i}: {type(handler).__name__}")
        if hasattr(handler, 'baseFilename'):
            print(f"  Arquivo: {handler.baseFilename}")

# Estado inicial
check_handlers("INICIAL")

# Testar import do radartunder3.5
print("\n=== TESTANDO IMPORT RADARTUNDER3.5 ===")
try:
    # Verificar se radartunder3.5 está sendo importado em algum lugar
    import importlib.util
    spec = importlib.util.find_spec("radartunder3.5")
    if spec:
        print("radartunder3.5 encontrado como módulo")
        # Não importar ainda, só verificar
    else:
        print("radartunder3.5 não encontrado como módulo")
except Exception as e:
    print(f"Erro ao verificar radartunder3.5: {e}")

# Verificar se há algum arquivo sendo importado
print("\n=== VERIFICANDO IMPORTS NO ALAVANCSTUNDERPRO ===")
with open('alavancstunderpro.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'radartunder' in content:
        print("❌ ENCONTRADO: 'radartunder' no alavancstunderpro.py")
        # Encontrar as linhas
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'radartunder' in line.lower():
                print(f"  Linha {i}: {line.strip()}")
    else:
        print("✓ 'radartunder' NÃO encontrado no alavancstunderpro.py")

# Verificar imports indiretos
print("\n=== VERIFICANDO IMPORTS INDIRETOS ===")
modules_to_check = [
    'robust_order_system.py',
    'enhanced_sync_system.py', 
    'error_handler.py'
]

for module_file in modules_to_check:
    if os.path.exists(module_file):
        with open(module_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'radartunder' in content.lower():
                print(f"❌ ENCONTRADO: 'radartunder' em {module_file}")
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'radartunder' in line.lower():
                        print(f"  Linha {i}: {line.strip()}")
            else:
                print(f"✓ 'radartunder' NÃO encontrado em {module_file}")

# Verificar se há algum basicConfig sendo chamado múltiplas vezes
print("\n=== VERIFICANDO MÚLTIPLAS CHAMADAS DE basicConfig ===")
import logging
print(f"Root logger level: {logging.getLogger().level}")
print(f"Root logger handlers: {len(logging.getLogger().handlers)}")

# Simular o que acontece quando alavancstunderpro.py roda
print("\n=== SIMULANDO CONFIGURAÇÃO DO ALAVANCSTUNDERPRO ===")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reset_strategy_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

check_handlers("APÓS BASICCONFIG ALAVANCSTUNDERPRO")

# Agora simular import de módulos
print("\n=== SIMULANDO IMPORTS ===")
try:
    import robust_order_system
    check_handlers("APÓS IMPORT ROBUST_ORDER_SYSTEM")
except Exception as e:
    print(f"Erro: {e}")

try:
    import enhanced_sync_system  
    check_handlers("APÓS IMPORT ENHANCED_SYNC_SYSTEM")
except Exception as e:
    print(f"Erro: {e}")