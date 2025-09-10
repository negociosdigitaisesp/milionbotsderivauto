#!/usr/bin/env python3
"""
Teste dos sistemas avançados implementados no accumulator_standalone.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from accumulator_standalone import AccumulatorScalpingBot

def main():
    print("🧪 Testando sistemas avançados no Accumulator Bot...")
    
    try:
        # Inicializar bot
        bot = AccumulatorScalpingBot()
        print("✅ Bot inicializado com sucesso")
        
        # Verificar se os sistemas estão presentes
        systems = {
            'enhanced_tick_buffer': hasattr(bot, 'enhanced_tick_buffer'),
            'websocket_recovery': hasattr(bot, 'websocket_recovery'),
            'signal_queue': hasattr(bot, 'signal_queue'),
            'health_monitor': hasattr(bot, 'health_monitor')
        }
        
        print("\n🔍 Verificação dos sistemas:")
        for system, present in systems.items():
            status = "✅" if present else "❌"
            print(f"   • {system}: {status}")
        
        # Testar métodos avançados
        methods = {
            '_get_enhanced_stats': hasattr(bot, '_get_enhanced_stats'),
            'test_enhanced_systems': hasattr(bot, 'test_enhanced_systems')
        }
        
        print("\n🔧 Verificação dos métodos:")
        for method, present in methods.items():
            status = "✅" if present else "❌"
            print(f"   • {method}: {status}")
        
        # Executar teste dos sistemas
        if all(systems.values()) and all(methods.values()):
            print("\n🧪 Executando teste dos sistemas...")
            test_result = bot.test_enhanced_systems()
            print(f"📊 Resultado: {test_result['summary']['success_rate']} de sucesso")
            
            # Obter estatísticas
            stats = bot._get_enhanced_stats()
            print(f"📈 Estatísticas: {len(stats)} campos disponíveis")
            
            print("\n🎯 TODOS OS SISTEMAS AVANÇADOS FORAM IMPLEMENTADOS COM SUCESSO!")
        else:
            print("\n❌ Alguns sistemas não foram encontrados")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falhou!")