#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accumulator Scalping Bot - Demo Mode
Versão de demonstração que simula o funcionamento do bot
sem necessidade de token válido da API.
"""

import asyncio
import random
from datetime import datetime
import signal

class DemoApiManager:
    """Simulador da API para demonstração"""
    
    def __init__(self):
        self.connected = False
        self.tick_counter = 0
        
    async def connect(self):
        """Simula conexão com a API"""
        print("🔌 Conectando à API da Deriv (MODO DEMO)...")
        await asyncio.sleep(2)
        self.connected = True
        print("✅ Conexão estabelecida (SIMULADA)")
        return True
    
    async def ticks_history(self, parameters):
        """Simula obtenção de ticks históricos"""
        await asyncio.sleep(0.5)  # Simula latência da API
        
        # Gerar ticks simulados
        base_price = 84700 + random.uniform(-100, 100)
        ticks = []
        
        for i in range(5):
            price = base_price + random.uniform(-50, 50)
            ticks.append({
                'tick': str(round(price, 5)),
                'epoch': int(datetime.now().timestamp()) - (4-i)
            })
        
        return {
            'history': {
                'times': [tick['epoch'] for tick in ticks],
                'prices': [float(tick['tick']) for tick in ticks]
            }
        }
    
    async def buy(self, parameters):
        """Simula compra de contrato"""
        await asyncio.sleep(1)  # Simula processamento
        
        # Simular resultado aleatório
        profit = random.choice([5.0, -50.0, 10.0, -50.0, 7.5])  # 60% vitória
        
        return {
            'buy': {
                'contract_id': f"demo_{random.randint(1000000, 9999999)}",
                'payout': profit if profit > 0 else 0,
                'purchase_time': int(datetime.now().timestamp())
            }
        }
    
    async def proposal_open_contract(self, parameters):
        """Simula verificação de contrato"""
        await asyncio.sleep(2)  # Simula duração do contrato
        
        # Simular resultado
        is_win = random.random() > 0.4  # 60% chance de vitória
        profit = 5.0 if is_win else -50.0
        
        return {
            'proposal_open_contract': {
                'is_sold': 1,
                'profit': profit,
                'status': 'won' if is_win else 'lost'
            }
        }

class DemoAccumulatorBot:
    """Versão demo do Accumulator bot"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.nome_bot = "Accumulator_Scalping_Bot_DEMO"
        self.stake_inicial = 50.0
        self.growth_rate = 2.0
        self.take_profit = 10.0
        self.ativo = "R_75"
        self.condicao_entrada = ['Red', 'Red', 'Red', 'Blue']
        self.total_profit = 0.0
        self.total_operations = 0
        self.wins = 0
        self.losses = 0
        
    def analisar_direcao_tick(self, preco_anterior, preco_atual):
        """Analisa se o tick é Red ou Blue"""
        return 'Blue' if preco_atual > preco_anterior else 'Red'
    
    async def obter_ticks(self):
        """Obtém ticks simulados"""
        response = await self.api_manager.ticks_history({
            'ticks_history': self.ativo,
            'count': 5
        })
        
        prices = response['history']['prices']
        return [str(price) for price in prices]
    
    async def analisar_ticks(self):
        """Analisa padrão dos ticks"""
        try:
            ticks = await self.obter_ticks()
            
            if len(ticks) < 5:
                print(f"🔍 {self.nome_bot}: Ticks insuficientes ({len(ticks)}/5)")
                return False
            
            # Analisar direção dos últimos 4 ticks
            direcoes = []
            for i in range(1, 5):
                direcao = self.analisar_direcao_tick(float(ticks[i-1]), float(ticks[i]))
                direcoes.append(direcao)
            
            print(f"🔍 {self.nome_bot}: Ticks: {ticks}")
            print(f"🔍 {self.nome_bot}: Padrão atual: {direcoes} | Esperado: {self.condicao_entrada}")
            
            # Verificar se atende à condição
            if direcoes == self.condicao_entrada:
                print(f"✅ {self.nome_bot}: Condição de entrada atendida!")
                return True
            else:
                print(f"⏳ {self.nome_bot}: Aguardando padrão correto...")
                return False
                
        except Exception as e:
            print(f"❌ {self.nome_bot}: Erro ao analisar ticks: {e}")
            return False
    
    async def executar_compra(self):
        """Executa compra do contrato Accumulator"""
        try:
            print(f"🛒 {self.nome_bot}: Executando compra Accumulator...")
            print(f"💰 Stake: ${self.stake_inicial} | Growth Rate: {self.growth_rate}% | Take Profit: {self.take_profit}%")
            
            # Simular compra
            response = await self.api_manager.buy({
                'buy': 'ACCU',
                'parameters': {
                    'amount': self.stake_inicial,
                    'symbol': self.ativo,
                    'growth_rate': self.growth_rate / 100,
                    'take_profit': self.take_profit / 100
                }
            })
            
            contract_id = response['buy']['contract_id']
            print(f"📋 {self.nome_bot}: Contrato criado: {contract_id}")
            
            return contract_id
            
        except Exception as e:
            print(f"❌ {self.nome_bot}: Erro na compra: {e}")
            return None
    
    async def aguardar_resultado(self, contract_id):
        """Aguarda resultado do contrato"""
        try:
            print(f"⏳ {self.nome_bot}: Aguardando resultado do contrato...")
            
            # Simular aguardo
            response = await self.api_manager.proposal_open_contract({
                'proposal_open_contract': 1,
                'contract_id': contract_id
            })
            
            profit = response['proposal_open_contract']['profit']
            status = response['proposal_open_contract']['status']
            
            return profit, status
            
        except Exception as e:
            print(f"❌ {self.nome_bot}: Erro ao aguardar resultado: {e}")
            return 0, 'error'
    
    async def processar_resultado(self, profit, status):
        """Processa resultado da operação"""
        self.total_operations += 1
        self.total_profit += profit
        
        if profit > 0:
            self.wins += 1
            print(f"✅ {self.nome_bot}: VITÓRIA! Lucro: ${profit:.2f}")
        else:
            self.losses += 1
            print(f"❌ {self.nome_bot}: DERROTA! Perda: ${abs(profit):.2f}")
        
        win_rate = (self.wins / self.total_operations) * 100 if self.total_operations > 0 else 0
        
        print(f"📊 {self.nome_bot}: Total: ${self.total_profit:.2f} | Ops: {self.total_operations} | "
              f"Vitórias: {self.wins} | Derrotas: {self.losses} | Taxa: {win_rate:.1f}%")
    
    async def executar_ciclo_trading(self):
        """Executa um ciclo completo de trading"""
        # Analisar condição de entrada
        if await self.analisar_ticks():
            # Executar compra
            contract_id = await self.executar_compra()
            
            if contract_id:
                # Aguardar resultado
                profit, status = await self.aguardar_resultado(contract_id)
                
                # Processar resultado
                await self.processar_resultado(profit, status)
                
                print("-" * 60)

class AccumulatorDemo:
    """Gerenciador da demonstração"""
    
    def __init__(self):
        self.api_manager = DemoApiManager()
        self.running = True
        
    async def start(self):
        """Inicia a demonstração"""
        print("="*60)
        print("🎯 ACCUMULATOR SCALPING BOT - MODO DEMONSTRAÇÃO")
        print("="*60)
        print(f"⏰ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("🧪 MODO DEMO: Simulação sem API real")
        print("🎲 Estratégia: Padrão ['Red', 'Red', 'Red', 'Blue'] no R_75")
        print("💰 Stake: $50.0 | Growth Rate: 2% | Take Profit: 10%")
        print("="*60)
        
        # Conectar à API simulada
        await self.api_manager.connect()
        
        # Criar bot
        bot = DemoAccumulatorBot(self.api_manager)
        
        print(f"🚀 Iniciando {bot.nome_bot}...")
        print("💡 Pressione Ctrl+C para parar a demonstração")
        print("-" * 60)
        
        # Configurar handler para interrupção
        def signal_handler(signum, frame):
            print("\n⏹️ Demonstração interrompida pelo usuário")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            cycle_count = 0
            while self.running and cycle_count < 10:  # Limitar a 10 ciclos para demo
                cycle_count += 1
                print(f"🔄 Ciclo {cycle_count}/10")
                
                # Executar ciclo de trading
                await bot.executar_ciclo_trading()
                
                # Pausa entre ciclos
                if self.running:
                    print("⏳ Aguardando próximo ciclo (30s)...")
                    await asyncio.sleep(5)  # Reduzido para demo
            
            if cycle_count >= 10:
                print("\n🏁 Demonstração concluída (10 ciclos executados)")
                
        except KeyboardInterrupt:
            print("\n⏹️ Demonstração interrompida")
        
        print("\n📊 RESUMO DA DEMONSTRAÇÃO:")
        print(f"   💰 Lucro total simulado: ${bot.total_profit:.2f}")
        print(f"   🎯 Total de operações: {bot.total_operations}")
        print(f"   ✅ Vitórias: {bot.wins}")
        print(f"   ❌ Derrotas: {bot.losses}")
        if bot.total_operations > 0:
            win_rate = (bot.wins / bot.total_operations) * 100
            print(f"   📈 Taxa de vitória: {win_rate:.1f}%")
        print("\n🎯 Esta foi uma demonstração do funcionamento do bot!")
        print("💡 Para usar com dinheiro real, configure um token válido da Deriv.")

async def main():
    """Função principal"""
    demo = AccumulatorDemo()
    await demo.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro na demonstração: {e}")