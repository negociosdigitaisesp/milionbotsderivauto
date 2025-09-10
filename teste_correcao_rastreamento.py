#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da Correção da Lógica de Rastreamento
Verifica se os resultados são capturados em tempo real durante o monitoramento
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar funções do bot principal
try:
    from radar_analisis_scalping_bot import (
        BotState, bot_current_state, monitoring_results, monitoring_operations_count,
        last_operation_id_when_signal, last_checked_operation_id,
        activate_monitoring_state, check_new_operations, reset_bot_state,
        finalizar_registro_de_rastreamento, PERSISTENCIA_OPERACOES
    )
    print("✅ Importações realizadas com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    sys.exit(1)

def simular_ativacao_monitoring():
    """Simula a ativação do estado MONITORING"""
    import radar_analisis_scalping_bot as bot
    
    # Definir variáveis globais diretamente para simular estado MONITORING
    bot.bot_current_state = BotState.MONITORING
    bot.last_operation_id_when_signal = "op_sinal"
    bot.last_checked_operation_id = "op_sinal"
    bot.monitoring_operations_count = 0
    bot.monitoring_results = []
    
    print("🔄 Estado MONITORING simulado:")
    print(f"   - Estado: {bot.bot_current_state}")
    print(f"   - ID do sinal: {bot.last_operation_id_when_signal}")
    print(f"   - Último verificado: {bot.last_checked_operation_id}")
    print(f"   - Contador: {bot.monitoring_operations_count}")
    print(f"   - Resultados: {bot.monitoring_results}")

def teste_captura_resultados_tempo_real():
    """Testa se os resultados são capturados em tempo real"""
    print("\n🧪 Testando captura de resultados em tempo real...")
    
    # Simular ativação do estado MONITORING
    simular_ativacao_monitoring()
    
    import radar_analisis_scalping_bot as bot
    
    # Simular detecção de novas operações com resultados
    operation_ids = ['op_001', 'op_002']
    resultados = ['V', 'D']
    
    for i, (op_id, resultado) in enumerate(zip(operation_ids, resultados)):
        print(f"\n🔄 Simulando operação {i+1}: {op_id} com resultado '{resultado}'")
        
        # Verificar nova operação
        nova_op = check_new_operations(op_id, resultado)
        
        print(f"   ✓ Nova operação detectada: {nova_op}")
        print(f"   ✓ Contador de operações: {bot.monitoring_operations_count}")
        print(f"   ✓ Resultados coletados: {bot.monitoring_results}")
        
        # Verificar se o resultado foi capturado
        if resultado in bot.monitoring_results:
            print(f"   ✅ Resultado '{resultado}' capturado com sucesso")
        else:
            print(f"   ❌ Resultado '{resultado}' NÃO foi capturado")
    
    return len(bot.monitoring_results) == len(resultados)

def teste_finalizacao_com_resultados():
    """Testa se a finalização recebe os resultados corretos"""
    print("\n🧪 Testando finalização com resultados...")
    
    import radar_analisis_scalping_bot as bot
    
    # Verificar se temos resultados suficientes
    if len(bot.monitoring_results) >= PERSISTENCIA_OPERACOES:
        print(f"✅ Resultados suficientes para finalização: {bot.monitoring_results}")
        
        # Simular finalização (sem supabase real)
        print(f"🔄 Simulando finalização com resultados: {bot.monitoring_results}")
        
        # Verificar se os resultados estão no formato correto
        resultados_validos = all(r in ['V', 'D'] for r in bot.monitoring_results)
        if resultados_validos:
            print("✅ Todos os resultados estão no formato válido ('V' ou 'D')")
        else:
            print("❌ Alguns resultados estão em formato inválido")
            
        return resultados_validos
    else:
        print(f"❌ Resultados insuficientes: {len(bot.monitoring_results)}/{PERSISTENCIA_OPERACOES}")
        return False

def teste_reset_estado():
    """Testa se o reset limpa corretamente as variáveis"""
    print("\n🧪 Testando reset de estado...")
    
    import radar_analisis_scalping_bot as bot
    
    print(f"📊 Antes do reset:")
    print(f"   - Estado: {bot.bot_current_state}")
    print(f"   - Operações: {bot.monitoring_operations_count}")
    print(f"   - Resultados: {bot.monitoring_results}")
    
    # Executar reset (sem supabase para teste)
    reset_bot_state()
    
    print(f"📊 Após o reset:")
    print(f"   - Estado: {bot.bot_current_state}")
    print(f"   - Operações: {bot.monitoring_operations_count}")
    print(f"   - Resultados: {bot.monitoring_results}")
    
    # Verificar se foi resetado corretamente
    reset_ok = (
        bot.bot_current_state == BotState.ANALYZING and
        bot.monitoring_operations_count == 0 and
        len(bot.monitoring_results) == 0
    )
    
    if reset_ok:
        print("✅ Reset executado corretamente")
    else:
        print("❌ Reset NÃO foi executado corretamente")
    
    return reset_ok

def teste_fluxo_completo():
    """Testa o fluxo completo de rastreamento"""
    print("\n🧪 Testando fluxo completo de rastreamento...")
    
    import radar_analisis_scalping_bot as bot
    
    # 1. Resetar estado inicial
    reset_bot_state()
    print(f"1️⃣ Estado inicial: {bot.bot_current_state}")
    
    # 2. Simular ativação do MONITORING
    simular_ativacao_monitoring()
    print(f"2️⃣ Estado após ativação: {bot.bot_current_state}")
    
    # 3. Simular operações com resultados
    operacoes = [('op_001', 'V'), ('op_002', 'D')]
    
    for op_id, resultado in operacoes:
        nova_op = check_new_operations(op_id, resultado)
        print(f"3️⃣ Operação {op_id}: {resultado} - Detectada: {nova_op}")
    
    # 4. Verificar estado final
    print(f"4️⃣ Resultados finais: {bot.monitoring_results}")
    print(f"4️⃣ Contador final: {bot.monitoring_operations_count}")
    
    # 5. Verificar se pode finalizar
    pode_finalizar = len(bot.monitoring_results) >= PERSISTENCIA_OPERACOES
    print(f"5️⃣ Pode finalizar: {pode_finalizar}")
    
    return pode_finalizar and len(bot.monitoring_results) == len(operacoes)

def main():
    """Função principal de teste"""
    print("🚀 TESTE DA CORREÇÃO DA LÓGICA DE RASTREAMENTO")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    testes = [
        ("Fluxo Completo de Rastreamento", teste_fluxo_completo),
        ("Captura de Resultados em Tempo Real", teste_captura_resultados_tempo_real),
        ("Finalização com Resultados", teste_finalizacao_com_resultados),
        ("Reset de Estado", teste_reset_estado)
    ]
    
    resultados = []
    
    for nome_teste, funcao_teste in testes:
        print(f"\n{'='*20} {nome_teste} {'='*20}")
        try:
            resultado = funcao_teste()
            resultados.append(resultado)
            status = "✅ PASSOU" if resultado else "❌ FALHOU"
            print(f"\n{status} - {nome_teste}")
        except Exception as e:
            print(f"\n💥 ERRO no teste '{nome_teste}': {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            resultados.append(False)
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passou = sum(resultados)
    total = len(resultados)
    
    for i, (nome, resultado) in enumerate(zip([t[0] for t in testes], resultados)):
        status = "✅" if resultado else "❌"
        print(f"{status} {nome}")
    
    print(f"\n🎯 Resultado Final: {passou}/{total} testes passaram")
    
    if passou == total:
        print("🎉 TODOS OS TESTES PASSARAM! A correção está funcionando.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique a implementação.")
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)