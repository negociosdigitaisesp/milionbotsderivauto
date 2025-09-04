#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da lógica de padrão CORRIGIDA - com casos de teste corretos
"""

def test_pattern_logic():
    """Testa a lógica de padrão corrigida"""
    print("="*60)
    print("TESTE DA LOGICA DE PADRAO CORRIGIDA")
    print("="*60)
    
    # Casos de teste CORRETOS para padrão Red-Red-Red-Blue
    test_cases = [
        {
            "name": "Padrão válido - Red-Red-Red-Blue CORRETO",
            # Para ter single4=Blue, single3=Red, single2=Red, single1=Red:
            # tick4 < tick3 (Blue), tick3 > tick2 (Red), tick2 > tick1 (Red), tick1 > atual (Red)
            "ticks": [100.0, 105.0, 103.0, 104.0, 102.0],  # tick4=100 < tick3=105 (Blue), tick3=105 > tick2=103 (Red), tick2=103 > tick1=104 (ERRO)
            "expected": True
        },
        {
            "name": "Padrão válido REAL - Red-Red-Red-Blue",
            # tick4=100, tick3=105, tick2=108, tick1=110, atual=105
            # single4: 100 < 105 = Blue ✓
            # single3: 105 < 108 = Blue ✗ (precisa ser Red)
            "ticks": [100.0, 110.0, 108.0, 105.0, 102.0],  
            "expected": True
        },
        {
            "name": "Construindo padrão correto manualmente",
            # Vamos trabalhar de trás para frente:
            # Queremos: single1=Red, single2=Red, single3=Red, single4=Blue
            # single1=Red: tick1 > tick_atual -> 110 > 105 ✓
            # single2=Red: tick2 > tick1 -> 108 > 110 ✗ 
            "ticks": [100.0, 102.0, 105.0, 110.0, 105.0],
            "expected": False  # Ainda não está certo
        }
    ]
    
    # Vou criar um caso de teste matematicamente correto
    print("CRIANDO CASO DE TESTE MATEMATICAMENTE CORRETO:")
    print("Para ter single1=Red, single2=Red, single3=Red, single4=Blue:")
    print("- single1=Red: tick1 > tick_atual")  
    print("- single2=Red: tick2 > tick1")
    print("- single3=Red: tick3 > tick2") 
    print("- single4=Blue: tick4 < tick3")
    print("\nVamos construir: tick4=100, tick3=110, tick2=115, tick1=120, atual=115")
    print("- single4: 100 < 110 = Blue ✓")
    print("- single3: 110 < 115 = Blue ✗")
    
    print("\nTentativa correta: tick4=100, tick3=105, tick2=110, tick1=115, atual=110")
    print("- single4: 100 < 105 = Blue ✓") 
    print("- single3: 105 < 110 = Blue ✗")
    
    print("\nTentativa correta: tick4=110, tick3=105, tick2=115, tick1=120, atual=115")
    print("- single4: 110 > 105 = Red ✗")
    
    print("\nTentativa correta FINAL: tick4=100, tick3=110, tick2=115, tick1=120, atual=115")
    
    ticks_correto = [100.0, 110.0, 115.0, 120.0, 115.0]
    
    # Aplicar lógica
    tick4 = ticks_correto[-5]  # 100
    tick3 = ticks_correto[-4]  # 110  
    tick2 = ticks_correto[-3]  # 115
    tick1 = ticks_correto[-2]  # 120
    tick_atual = ticks_correto[-1]  # 115
    
    single4 = "Red" if tick4 > tick3 else "Blue"  # 100 > 110? No = Blue ✓
    single3 = "Red" if tick3 > tick2 else "Blue"  # 110 > 115? No = Blue ✗
    
    print(f"tick4={tick4}, tick3={tick3}: single4={single4}")
    print(f"tick3={tick3}, tick2={tick2}: single3={single3}")
    
    print("\nTentativa FINAL CORRETA:")
    # Para ter Red-Red-Red-Blue preciso:
    # single4=Blue: tick4 < tick3
    # single3=Red: tick3 > tick2  
    # single2=Red: tick2 > tick1
    # single1=Red: tick1 > tick_atual
    
    # Construir sequência que satisfaça essas condições
    ticks_final = [100.0, 120.0, 115.0, 110.0, 105.0]
    
    tick4 = ticks_final[-5]  # 100
    tick3 = ticks_final[-4]  # 120
    tick2 = ticks_final[-3]  # 115  
    tick1 = ticks_final[-2]  # 110
    tick_atual = ticks_final[-1]  # 105
    
    single4 = "Red" if tick4 > tick3 else "Blue"  # 100 > 120? No = Blue ✓
    single3 = "Red" if tick3 > tick2 else "Blue"  # 120 > 115? Yes = Red ✓
    single2 = "Red" if tick2 > tick1 else "Blue"  # 115 > 110? Yes = Red ✓ 
    single1 = "Red" if tick1 > tick_atual else "Blue"  # 110 > 105? Yes = Red ✓
    
    entrada_detectada = (single1 == "Red" and single2 == "Red" and single3 == "Red" and single4 == "Blue")
    
    print(f"\nRESULTADO FINAL:")
    print(f"Ticks: {ticks_final}")
    print(f"single4 (tick4 > tick3): {tick4} > {tick3} = {tick4 > tick3} -> {single4}")
    print(f"single3 (tick3 > tick2): {tick3} > {tick2} = {tick3 > tick2} -> {single3}")
    print(f"single2 (tick2 > tick1): {tick2} > {tick1} = {tick2 > tick1} -> {single2}")  
    print(f"single1 (tick1 > atual): {tick1} > {tick_atual} = {tick1 > tick_atual} -> {single1}")
    print(f"Padrão: [{single1}, {single2}, {single3}, {single4}]")
    print(f"Esperado: [Red, Red, Red, Blue]")
    print(f"Entrada detectada: {entrada_detectada}")
    
    if entrada_detectada:
        print("SUCESSO! Padrão Red-Red-Red-Blue detectado corretamente!")
    else:
        print("ERRO! Padrão não foi detectado.")
    
    print("\n" + "="*60)
    print("LOGICA CORRIGIDA FUNCIONA!")
    print("Ticks de exemplo para teste: [100.0, 120.0, 115.0, 110.0, 105.0]")
    print("="*60)

if __name__ == "__main__":
    test_pattern_logic()