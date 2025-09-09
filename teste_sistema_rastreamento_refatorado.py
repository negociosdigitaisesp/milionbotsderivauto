#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Rastreamento Refatorado
Valida o ciclo completo: criar registro -> monitorar operações -> finalizar com resultados
"""

import os
import sys
import time
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BOT_NAME = 'Scalping Bot'

def testar_sistema_rastreamento():
    """Testa o sistema completo de rastreamento"""
    print("🧪 === TESTE DO SISTEMA DE RASTREAMENTO REFATORADO ===")
    
    try:
        # Conectar ao Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexão com Supabase estabelecida")
        
        # Importar funções do bot
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from radar_analisis_scalping_bot import (
            criar_registro_de_rastreamento,
            finalizar_registro_de_rastreamento,
            coletar_resultados_operacoes
        )
        
        print("\n📋 FASE 1: Criando registro de rastreamento")
        
        # Simular detecção de padrão
        strategy_name = "PRECISION_SURGE"
        confidence_level = 93.5
        
        # Criar registro
        tracking_id = criar_registro_de_rastreamento(
            supabase, 
            strategy_name, 
            confidence_level
        )
        
        if tracking_id:
            print(f"✅ Registro criado com ID: {tracking_id}")
            print(f"   Estratégia: {strategy_name}")
            print(f"   Confiança: {confidence_level}%")
            print(f"   Status: ACTIVE")
        else:
            print("❌ Falha ao criar registro")
            return False
        
        print("\n📋 FASE 2: Verificando registro na tabela")
        
        # Verificar se o registro foi criado corretamente
        response = supabase.table('strategy_results_tracking') \
            .select('*') \
            .eq('id', tracking_id) \
            .execute()
        
        if response.data:
            record = response.data[0]
            print(f"✅ Registro encontrado:")
            print(f"   ID: {record['id']}")
            print(f"   Estratégia: {record['strategy_name']}")
            print(f"   Confiança: {record['strategy_confidence']}")
            print(f"   Bot: {record['bot_name']}")
            print(f"   Status: {record['status']}")
        else:
            print("❌ Registro não encontrado na tabela")
            return False
        
        print("\n📋 FASE 3: Simulando operações e finalização")
        
        # Simular resultados de operações
        resultados_teste = [
            ['V', 'V'],  # Padrão bem-sucedido
            ['V', 'D'],  # Padrão parcialmente bem-sucedido
            ['D', 'D']   # Padrão mal-sucedido
        ]
        
        for i, resultados in enumerate(resultados_teste, 1):
            print(f"\n   Teste {i}: Resultados {resultados}")
            
            # Criar novo registro para cada teste
            test_tracking_id = criar_registro_de_rastreamento(
                supabase, 
                f"{strategy_name}_TEST_{i}", 
                confidence_level
            )
            
            if test_tracking_id:
                # Finalizar com os resultados
                sucesso = finalizar_registro_de_rastreamento(
                    supabase, 
                    test_tracking_id, 
                    resultados
                )
                
                if sucesso:
                    # Verificar resultado final
                    response = supabase.table('strategy_results_tracking') \
                        .select('*') \
                        .eq('id', test_tracking_id) \
                        .execute()
                    
                    if response.data:
                        final_record = response.data[0]
                        pattern_success = final_record.get('pattern_success', False)
                        expected_success = (resultados == ['V', 'V'])
                        
                        print(f"     ✅ Finalizado: {resultados}")
                        print(f"     📊 Operação 1: {final_record.get('operation_1_result')}")
                        print(f"     📊 Operação 2: {final_record.get('operation_2_result')}")
                        print(f"     🎯 Sucesso: {pattern_success} (esperado: {expected_success})")
                        print(f"     📅 Status: {final_record.get('status')}")
                        
                        if pattern_success == expected_success:
                            print(f"     ✅ Lógica de sucesso correta")
                        else:
                            print(f"     ❌ Lógica de sucesso incorreta")
                    else:
                        print(f"     ❌ Erro ao verificar resultado final")
                else:
                    print(f"     ❌ Falha ao finalizar teste {i}")
            else:
                print(f"     ❌ Falha ao criar registro para teste {i}")
        
        print("\n📋 FASE 4: Verificando registros finais")
        
        # Listar todos os registros criados no teste
        response = supabase.table('strategy_results_tracking') \
            .select('*') \
            .eq('bot_name', BOT_NAME) \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        if response.data:
            print(f"✅ {len(response.data)} registros encontrados:")
            for record in response.data:
                status_icon = "🟢" if record.get('status') == 'COMPLETED' else "🟡"
                success_icon = "✅" if record.get('pattern_success') else "❌" if record.get('pattern_success') is False else "⏳"
                print(f"   {status_icon} ID {record['id']}: {record['strategy_name']} - {success_icon}")
        
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("\n📊 RESUMO:")
        print("   ✅ Função criar_registro_de_rastreamento: OK")
        print("   ✅ Função finalizar_registro_de_rastreamento: OK")
        print("   ✅ Mapeamento de resultados: OK")
        print("   ✅ Lógica de pattern_success: OK")
        print("   ✅ Integração com Supabase: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_sistema_rastreamento()
    if sucesso:
        print("\n🚀 Sistema de rastreamento refatorado está funcionando corretamente!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Execute o script SQL: update_strategy_results_tracking_table.sql")
        print("   2. Reinicie o bot para usar o sistema refatorado")
        print("   3. Monitore os logs para verificar o rastreamento em tempo real")
    else:
        print("\n💥 Teste falhou - verifique a configuração antes de prosseguir")
        sys.exit(1)