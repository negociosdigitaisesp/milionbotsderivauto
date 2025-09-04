#!/usr/bin/env python3
"""
Exemplo de uso das funcionalidades do Tunder Bot
Demonstra como usar o sistema de sinais integrado
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
NOME_BOT = "Tunder Bot"

class TunderBotSignalManager:
    """Gerenciador de sinais do Tunder Bot"""
    
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    
    async def criar_sinal_inicial(self):
        """Cria sinal inicial do Tunder Bot"""
        try:
            signal_data = {
                'bot_name': NOME_BOT,
                'is_safe_to_operate': True,
                'reason': 'Bot inicializado e configurado',
                'last_pattern_found': 'Aguardando padrões',
                'losses_in_last_10_ops': 0,
                'wins_in_last_5_ops': 0,
                'historical_accuracy': 0.0,
                'pattern_found_at': datetime.now().isoformat(),
                'operations_after_pattern': 0,
                'auto_disable_after_ops': 3
            }
            
            result = self.supabase.table('radar_de_apalancamiento_signals') \
                .insert(signal_data) \
                .execute()
            
            print(f"✅ Sinal inicial criado para {NOME_BOT}")
            return result
            
        except Exception as e:
            print(f"❌ Erro ao criar sinal inicial: {e}")
            return None
    
    async def atualizar_sinal_padrao_detectado(self, pattern_type: str):
        """Atualiza sinal quando padrão é detectado"""
        try:
            update_data = {
                'is_safe_to_operate': True,
                'reason': f'Padrão {pattern_type} detectado',
                'last_pattern_found': pattern_type,
                'pattern_found_at': datetime.now().isoformat(),
                'operations_after_pattern': 0
            }
            
            result = self.supabase.table('radar_de_apalancamiento_signals') \
                .update(update_data) \
                .eq('bot_name', NOME_BOT) \
                .execute()
            
            print(f"📊 Sinal atualizado: Padrão {pattern_type} detectado")
            return result
            
        except Exception as e:
            print(f"❌ Erro ao atualizar sinal: {e}")
            return None
    
    async def atualizar_resultado_operacao(self, resultado: str, profit: float):
        """Atualiza sinal após resultado de operação"""
        try:
            # Obter dados atuais
            current_signal = self.supabase.table('radar_de_apalancamiento_signals') \
                .select('*') \
                .eq('bot_name', NOME_BOT) \
                .execute()
            
            if not current_signal.data:
                print(f"⚠️ Nenhum sinal encontrado para {NOME_BOT}")
                return None
            
            signal = current_signal.data[0]
            
            # Atualizar contadores
            operations_after_pattern = signal.get('operations_after_pattern', 0) + 1
            wins_in_last_5_ops = signal.get('wins_in_last_5_ops', 0)
            losses_in_last_10_ops = signal.get('losses_in_last_10_ops', 0)
            
            if resultado == 'WIN':
                wins_in_last_5_ops = min(wins_in_last_5_ops + 1, 5)
            else:
                losses_in_last_10_ops = min(losses_in_last_10_ops + 1, 10)
            
            # Calcular precisão histórica (exemplo simples)
            total_ops = wins_in_last_5_ops + losses_in_last_10_ops
            historical_accuracy = (wins_in_last_5_ops / max(total_ops, 1)) * 100
            
            # Determinar se ainda é seguro operar
            is_safe = True
            reason = f"Última operação: {resultado} (${profit:.2f})"
            
            # Lógica de segurança
            if losses_in_last_10_ops >= 7:  # Muitas perdas
                is_safe = False
                reason = "Muitas perdas recentes - pausando operações"
            elif operations_after_pattern >= signal.get('auto_disable_after_ops', 3):
                is_safe = False
                reason = "Limite de operações após padrão atingido"
            
            update_data = {
                'is_safe_to_operate': is_safe,
                'reason': reason,
                'wins_in_last_5_ops': wins_in_last_5_ops,
                'losses_in_last_10_ops': losses_in_last_10_ops,
                'historical_accuracy': round(historical_accuracy, 2),
                'operations_after_pattern': operations_after_pattern
            }
            
            result = self.supabase.table('radar_de_apalancamiento_signals') \
                .update(update_data) \
                .eq('bot_name', NOME_BOT) \
                .execute()
            
            print(f"📊 Sinal atualizado após operação: {resultado} - Safe: {is_safe}")
            return result
            
        except Exception as e:
            print(f"❌ Erro ao atualizar resultado: {e}")
            return None
    
    async def obter_status_sinal(self):
        """Obtém status atual do sinal"""
        try:
            result = self.supabase.table('radar_de_apalancamiento_signals') \
                .select('*') \
                .eq('bot_name', NOME_BOT) \
                .execute()
            
            if result.data:
                signal = result.data[0]
                print(f"📊 Status do {NOME_BOT}:")
                print(f"   • Seguro para operar: {signal.get('is_safe_to_operate')}")
                print(f"   • Razão: {signal.get('reason')}")
                print(f"   • Último padrão: {signal.get('last_pattern_found')}")
                print(f"   • Vitórias (últimas 5): {signal.get('wins_in_last_5_ops')}")
                print(f"   • Perdas (últimas 10): {signal.get('losses_in_last_10_ops')}")
                print(f"   • Precisão histórica: {signal.get('historical_accuracy')}%")
                print(f"   • Operações após padrão: {signal.get('operations_after_pattern')}")
                return signal
            else:
                print(f"⚠️ Nenhum sinal encontrado para {NOME_BOT}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao obter status: {e}")
            return None

async def exemplo_uso_completo():
    """Exemplo completo de uso do sistema de sinais"""
    print(f"🤖 Exemplo de uso do sistema de sinais - {NOME_BOT}")
    print("="*60)
    
    # Criar gerenciador
    signal_manager = TunderBotSignalManager()
    
    # 1. Criar sinal inicial
    print("\n1. Criando sinal inicial...")
    await signal_manager.criar_sinal_inicial()
    
    # 2. Verificar status
    print("\n2. Verificando status inicial...")
    await signal_manager.obter_status_sinal()
    
    # 3. Simular detecção de padrão
    print("\n3. Simulando detecção de padrão Red-Red-Red-Blue...")
    await signal_manager.atualizar_sinal_padrao_detectado("Red-Red-Red-Blue")
    
    # 4. Simular algumas operações
    print("\n4. Simulando resultados de operações...")
    
    # Operação 1 - WIN
    await signal_manager.atualizar_resultado_operacao("WIN", 0.50)
    await signal_manager.obter_status_sinal()
    
    # Operação 2 - LOSS
    await signal_manager.atualizar_resultado_operacao("LOSS", -5.00)
    await signal_manager.obter_status_sinal()
    
    # Operação 3 - WIN
    await signal_manager.atualizar_resultado_operacao("WIN", 0.50)
    await signal_manager.obter_status_sinal()
    
    print("\n✅ Exemplo concluído!")
    print("\n📋 Resumo das funcionalidades:")
    print("   • save_signal_to_radar() - Salva/atualiza sinal completo")
    print("   • get_signal_from_radar() - Obtém sinal atual")
    print("   • update_signal_status() - Atualização rápida de status")
    print("   • Sistema UPSERT automático (uma linha por bot)")
    print("   • Integração com tabela radar_de_apalancamiento_signals")

if __name__ == "__main__":
    asyncio.run(exemplo_uso_completo())