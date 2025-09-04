#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Padrão para Testar Correção do Growth Rate
Força o padrão ['Red', 'Red', 'Red', 'Blue'] para testar a API
"""

import asyncio
import json
from accumulator_standalone import AccumulatorScalpingBot, GROWTH_RATE, ATIVO

class PatternSimulator:
    def __init__(self):
        self.bot = None
        
    async def simulate_pattern_entry(self):
        """Simula a entrada do padrão correto"""
        print("🎯 SIMULADOR DE PADRÃO - TESTE GROWTH_RATE")
        print("=" * 60)
        
        # Criar instância do bot
        self.bot = AccumulatorScalpingBot()
        
        # Simular ticks que geram o padrão ['Red', 'Red', 'Red', 'Blue']
        # Para ter Red, Red, Red, Blue precisamos:
        # single1 = Red (tick1 > tick_atual), single2 = Red (tick2 > tick1), single3 = Red (tick3 > tick2), single4 = Blue (tick4 < tick3)
        
        simulated_ticks = [
            97.0,   # tick4 (FROM_END 5) - tick4 < tick3 = Blue (single4)
            100.0,  # tick3 (FROM_END 4) - tick3 > tick2 = Red (single3)
            99.0,   # tick2 (FROM_END 3) - tick2 > tick1 = Red (single2)  
            98.0,   # tick1 (FROM_END 2) - tick1 > tick_atual = Red (single1)
            97.0    # tick_atual
        ]
        
        print(f"📊 TICKS SIMULADOS: {simulated_ticks}")
        
        # Calcular padrão esperado
        tick4, tick3, tick2, tick1, tick_atual = simulated_ticks
        
        single4 = 'Red' if tick4 > tick3 else 'Blue'
        single3 = 'Red' if tick3 > tick2 else 'Blue'
        single2 = 'Red' if tick2 > tick1 else 'Blue'
        single1 = 'Red' if tick1 > tick_atual else 'Blue'
        
        pattern = [single1, single2, single3, single4]
        
        print(f"📈 PADRÃO GERADO: {pattern}")
        print(f"🎯 PADRÃO ESPERADO: ['Red', 'Red', 'Red', 'Blue']")
        print(f"✅ MATCH: {pattern == ['Red', 'Red', 'Red', 'Blue']}")
        
        if pattern == ['Red', 'Red', 'Red', 'Blue']:
            print("\n🚀 PADRÃO CORRETO DETECTADO! Testando envio para API...")
            
            # Testar estruturas de parâmetros
            await self.test_api_structures()
        else:
            print("❌ Padrão não corresponde. Ajustando ticks...")
            
    async def test_api_structures(self):
        """Testa diferentes estruturas de parâmetros ACCU"""
        print("\n🔬 TESTE DE ESTRUTURAS DE PARÂMETROS ACCU")
        print("=" * 60)
        
        # Estrutura 1: Com limit_order (documentação oficial)
        structure1 = {
            "proposal": 1,
            "contract_type": "ACCU",
            "symbol": ATIVO,
            "amount": 10,
            "basis": "stake",
            "currency": "USD",
            "growth_rate": GROWTH_RATE,
            "limit_order": {
                "take_profit": 150
            }
        }
        
        # Estrutura 2: Sem limit_order
        structure2 = {
            "proposal": 1,
            "contract_type": "ACCU",
            "symbol": ATIVO,
            "amount": 10,
            "basis": "stake",
            "currency": "USD",
            "growth_rate": GROWTH_RATE
        }
        
        # Estrutura 3: Com growth_rate como string (teste)
        structure3 = {
            "proposal": 1,
            "contract_type": "ACCU",
            "symbol": ATIVO,
            "amount": 10,
            "basis": "stake",
            "currency": "USD",
            "growth_rate": str(GROWTH_RATE)
        }
        
        structures = [
            ("Com limit_order (oficial)", structure1),
            ("Sem limit_order", structure2),
            ("Growth_rate como string", structure3)
        ]
        
        for name, structure in structures:
            print(f"\n📋 TESTANDO: {name}")
            print(f"   • Growth Rate: {structure['growth_rate']} (tipo: {type(structure['growth_rate'])})")
            print(f"   • JSON: {json.dumps(structure, indent=2)}")
            
            # Validar usando função do bot
            try:
                is_valid = self.bot._validar_parametros_accu(structure)
                print(f"   • Validação: {'✅ VÁLIDO' if is_valid else '❌ INVÁLIDO'}")
            except Exception as e:
                print(f"   • Validação: ❌ ERRO - {e}")
            
            print()
        
        print("🎯 CONCLUSÃO:")
        print(f"• Growth Rate atual: {GROWTH_RATE} (tipo: {type(GROWTH_RATE)})")
        print(f"• Intervalo válido: 0.01 <= {GROWTH_RATE} <= 0.05 = {0.01 <= GROWTH_RATE <= 0.05}")
        print(f"• Estrutura recomendada: Com limit_order conforme documentação oficial")
        
async def main():
    simulator = PatternSimulator()
    await simulator.simulate_pattern_entry()

if __name__ == "__main__":
    asyncio.run(main())