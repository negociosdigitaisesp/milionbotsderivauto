#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Direto da API Deriv com Growth Rate Corrigido
Testa chamada real para proposal com os parâmetros corrigidos
"""

import asyncio
import json
import websockets
from accumulator_standalone import GROWTH_RATE, ATIVO

class DirectAPITester:
    def __init__(self):
        self.app_id = "85515"
        self.ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
        self.ws = None
        
    async def connect(self):
        """Conecta ao WebSocket da Deriv"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            print("✅ Conectado ao WebSocket da Deriv")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    async def test_proposal_structures(self):
        """Testa diferentes estruturas de proposal ACCU"""
        print("🔬 TESTE DIRETO - PROPOSAL ACCU COM GROWTH_RATE CORRIGIDO")
        print("=" * 70)
        
        if not await self.connect():
            return
        
        # Estruturas para testar
        test_structures = [
            {
                "name": "Estrutura Oficial (com limit_order)",
                "params": {
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
            },
            {
                "name": "Estrutura Simples (sem limit_order)",
                "params": {
                    "proposal": 1,
                    "contract_type": "ACCU",
                    "symbol": ATIVO,
                    "amount": 10,
                    "basis": "stake",
                    "currency": "USD",
                    "growth_rate": GROWTH_RATE
                }
            },
            {
                "name": "Estrutura com Growth Rate 0.02",
                "params": {
                    "proposal": 1,
                    "contract_type": "ACCU",
                    "symbol": ATIVO,
                    "amount": 10,
                    "basis": "stake",
                    "currency": "USD",
                    "growth_rate": 0.02
                }
            },
            {
                "name": "Estrutura com Growth Rate 0.01 (mínimo)",
                "params": {
                    "proposal": 1,
                    "contract_type": "ACCU",
                    "symbol": ATIVO,
                    "amount": 10,
                    "basis": "stake",
                    "currency": "USD",
                    "growth_rate": 0.01
                }
            }
        ]
        
        for i, test in enumerate(test_structures, 1):
            print(f"\n📋 TESTE {i}: {test['name']}")
            print(f"   • Growth Rate: {test['params']['growth_rate']} (tipo: {type(test['params']['growth_rate'])})")
            
            # Enviar proposal
            try:
                await self.ws.send(json.dumps(test['params']))
                print("   • ✅ Proposal enviada")
                
                # Aguardar resposta
                response = await asyncio.wait_for(self.ws.recv(), timeout=10)
                response_data = json.loads(response)
                
                print(f"   • 📥 Resposta recebida:")
                
                if 'error' in response_data:
                    error = response_data['error']
                    print(f"   • ❌ ERRO: {error.get('message', 'Erro desconhecido')}")
                    print(f"   • 🔍 Código: {error.get('code', 'N/A')}")
                    print(f"   • 📋 Detalhes: {error.get('details', 'N/A')}")
                    
                    # Verificar se é erro de growth_rate
                    if 'growth_rate' in str(error).lower():
                        print("   • 🎯 ERRO RELACIONADO AO GROWTH_RATE DETECTADO!")
                    else:
                        print("   • ✅ Erro NÃO relacionado ao growth_rate")
                        
                elif 'proposal' in response_data:
                    proposal = response_data['proposal']
                    print(f"   • ✅ SUCESSO! ID: {proposal.get('id', 'N/A')}")
                    print(f"   • 💰 Payout: {proposal.get('payout', 'N/A')}")
                    print(f"   • 📊 Ask Price: {proposal.get('ask_price', 'N/A')}")
                    
                else:
                    print(f"   • ⚠️ Resposta inesperada: {response_data}")
                    
            except asyncio.TimeoutError:
                print("   • ⏰ Timeout - Sem resposta da API")
            except Exception as e:
                print(f"   • ❌ Erro na comunicação: {e}")
            
            # Aguardar entre testes
            await asyncio.sleep(1)
        
        await self.ws.close()
        print("\n🔚 Teste concluído")
        
    async def test_current_bot_structure(self):
        """Testa a estrutura exata que o bot está usando"""
        print("\n🤖 TESTE - ESTRUTURA EXATA DO BOT")
        print("=" * 50)
        
        if not await self.connect():
            return
            
        # Estrutura exata do bot (conforme código atual)
        bot_structure = {
            "proposal": 1,
            "contract_type": "ACCU",
            "symbol": ATIVO,
            "amount": 50.0,  # STAKE_INICIAL
            "basis": "stake",
            "currency": "USD",
            "growth_rate": GROWTH_RATE,  # 0.03
            "limit_order": {
                "take_profit": 150  # Valor da documentação oficial
            }
        }
        
        print(f"📋 ESTRUTURA DO BOT:")
        print(json.dumps(bot_structure, indent=2))
        
        try:
            await self.ws.send(json.dumps(bot_structure))
            print("✅ Proposal enviada")
            
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            response_data = json.loads(response)
            
            print(f"📥 RESPOSTA:")
            print(json.dumps(response_data, indent=2))
            
            if 'error' in response_data:
                error = response_data['error']
                if 'growth_rate' in str(error).lower():
                    print("❌ ERRO DE GROWTH_RATE AINDA PERSISTE!")
                else:
                    print("✅ ERRO NÃO RELACIONADO AO GROWTH_RATE")
            else:
                print("🎉 SUCESSO! GROWTH_RATE CORRIGIDO!")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            
        await self.ws.close()

async def main():
    tester = DirectAPITester()
    await tester.test_proposal_structures()
    await tester.test_current_bot_structure()

if __name__ == "__main__":
    asyncio.run(main())