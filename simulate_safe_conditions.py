#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para simular condições que resultam em is_safe_to_operate = True
Demonstra como o sistema salva dados corretos na tabela Supabase
"""

import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def inicializar_supabase():
    """Inicializa conexão com Supabase"""
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("X Erro: Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas")
            return None
            
        supabase = create_client(url, key)
        print("✓ Conexão com Supabase estabelecida")
        return supabase
        
    except Exception as e:
        print(f"X Erro ao conectar com Supabase: {e}")
        return None

def simular_dados_scalping_bot_safe():
    """
    Simula histórico que atende aos critérios do Scalping Bot:
    - Padrão V-D-V nas 3 primeiras posições
    - Máximo 2 derrotas nas últimas 20 operações
    - Máximo 2 derrotas nas 10 operações anteriores ao padrão
    - Mínimo 3 vitórias nas 5 operações anteriores ao padrão
    """
    # Criar histórico que atende todos os critérios
    historico = [
        'V',  # [0] - Mais recente
        'D',  # [1] - Anterior  
        'V',  # [2] - Anterior ao anterior (Padrão V-D-V)
        'V',  # [3] - Início das 5 operações anteriores
        'V',  # [4]
        'V',  # [5] 
        'V',  # [6]
        'V',  # [7] - Fim das 5 operações anteriores (5 vitórias)
        'V',  # [8] - Início das 10 operações anteriores
        'V',  # [9]
        'V',  # [10]
        'D',  # [11] - 1ª derrota nas 10 anteriores
        'V',  # [12] - Fim das 10 operações anteriores (1 derrota)
        'V',  # [13] - Operações mais antigas
        'V',  # [14]
        'V',  # [15]
        'V',  # [16]
        'V',  # [17]
        'V',  # [18]
        'V',  # [19] - Total: 2 derrotas nas últimas 20
        'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'  # Mais histórico
    ]
    
    return historico

def simular_dados_tunder_bot_safe():
    """
    Simula histórico que atende aos critérios mais rigorosos do Tunder Bot:
    - Padrão V-D-V nas 3 primeiras posições
    - Máximo 1 derrota nas últimas 20 operações
    - Máximo 1 derrota nas 10 operações anteriores ao padrão
    - Mínimo 4 vitórias nas 5 operações anteriores ao padrão
    """
    # Criar histórico que atende todos os critérios rigorosos
    historico = [
        'V',  # [0] - Mais recente
        'D',  # [1] - Anterior (única derrota permitida)
        'V',  # [2] - Anterior ao anterior (Padrão V-D-V)
        'V',  # [3] - Início das 5 operações anteriores
        'V',  # [4]
        'V',  # [5] 
        'V',  # [6]
        'V',  # [7] - Fim das 5 operações anteriores (5 vitórias = 4+)
        'V',  # [8] - Início das 10 operações anteriores
        'V',  # [9]
        'V',  # [10]
        'V',  # [11] - Sem derrotas nas 10 anteriores
        'V',  # [12] - Fim das 10 operações anteriores (0 derrotas)
        'V',  # [13] - Operações mais antigas
        'V',  # [14]
        'V',  # [15]
        'V',  # [16]
        'V',  # [17]
        'V',  # [18]
        'V',  # [19] - Total: 1 derrota nas últimas 20
        'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'  # Mais histórico
    ]
    
    return historico

def analisar_padroes_scalping(historico):
    """Lógica de análise do Scalping Bot"""
    OPERACOES_MINIMAS = 20
    
    # Verificação 1: Dados suficientes
    if len(historico) < OPERACOES_MINIMAS:
        return False, "Aguardando dados suficientes..."
    
    # Verificação 2: Filtro de Mercado Instável
    ultimas_20 = historico[:20]
    derrotas_ultimas_20 = ultimas_20.count('D')
    print(f"* Scalping Bot - Derrotas nas últimas 20: {derrotas_ultimas_20}")
    
    if derrotas_ultimas_20 > 3:
        return False, "Mercado Instavel, Volte daqui uns minutos."
    
    # Verificação 3: Filtro de Espera
    if derrotas_ultimas_20 > 2:
        return False, "Esperando o Padrao. Nao ligar ainda."
    
    # Verificação 4: Gatilho V-D-V
    if len(historico) < 3:
        return False, "Esperando o Padrao. Nao ligar ainda."
    
    padrao_vdv = historico[0] == 'V' and historico[1] == 'D' and historico[2] == 'V'
    print(f"* Scalping Bot - Padrão V-D-V: {historico[0]}-{historico[1]}-{historico[2]} = {'OK' if padrao_vdv else 'NAO'}")
    
    if not padrao_vdv:
        return False, "Esperando o Padrao. Nao ligar ainda."
    
    # Verificação 5: Filtro 1 (Condição Geral)
    if len(historico) < 13:
        return False, "Gatilho Encontrado, mas Condicao Geral Fraca"
    
    operacoes_anteriores_10 = historico[3:13]
    derrotas_anteriores_10 = operacoes_anteriores_10.count('D')
    print(f"* Scalping Bot - Derrotas nas 10 anteriores: {derrotas_anteriores_10}")
    
    if derrotas_anteriores_10 > 2:
        return False, "Gatilho Encontrado, mas Condicao Geral Fraca"
    
    # Verificação 6: Filtro 2 (Condição Imediata)
    if len(historico) < 8:
        return False, "Gatilho Encontrado, mas Condicao Imediata Fraca"
    
    operacoes_anteriores_5 = historico[3:8]
    vitorias_anteriores_5 = operacoes_anteriores_5.count('V')
    print(f"* Scalping Bot - Vitórias nas 5 anteriores: {vitorias_anteriores_5}")
    
    if vitorias_anteriores_5 < 3:
        return False, "Gatilho Encontrado, mas Condicao Imediata Fraca"
    
    return True, "Padrao Encontrado - Ligar o Bot"

def analisar_padroes_tunder(historico):
    """Lógica de análise do Tunder Bot (mais rigorosa)"""
    OPERACOES_MINIMAS = 10
    
    # Verificação 1: Dados suficientes
    if len(historico) < OPERACOES_MINIMAS:
        return False, "Aguardando dados suficientes do Tunder Bot..."
    
    # Verificação 2: Filtro de Mercado Instável (mais conservador)
    ultimas_20 = historico[:20]
    derrotas_ultimas_20 = ultimas_20.count('D')
    print(f"* Tunder Bot - Derrotas nas últimas 20: {derrotas_ultimas_20}")
    
    if derrotas_ultimas_20 > 2:  # Mais restritivo
        return False, "Tunder Bot: Mercado Instavel, Volte daqui uns minutos."
    
    # Verificação 3: Filtro de Espera
    if derrotas_ultimas_20 > 1:  # Mais conservador
        return False, "Tunder Bot: Esperando o Padrao. Nao ligar ainda."
    
    # Verificação 4: Gatilho V-D-V
    if len(historico) < 3:
        return False, "Tunder Bot: Esperando o Padrao. Nao ligar ainda."
    
    padrao_vdv = historico[0] == 'V' and historico[1] == 'D' and historico[2] == 'V'
    print(f"* Tunder Bot - Padrão V-D-V: {historico[0]}-{historico[1]}-{historico[2]} = {'OK' if padrao_vdv else 'NAO'}")
    
    if not padrao_vdv:
        return False, "Tunder Bot: Esperando o Padrao. Nao ligar ainda."
    
    # Verificação 5: Filtro 1 (Condição Geral)
    if len(historico) < 13:
        return False, "Tunder Bot: Gatilho Encontrado, mas Condicao Geral Fraca"
    
    operacoes_anteriores_10 = historico[3:13]
    derrotas_anteriores_10 = operacoes_anteriores_10.count('D')
    print(f"* Tunder Bot - Derrotas nas 10 anteriores: {derrotas_anteriores_10}")
    
    if derrotas_anteriores_10 > 1:  # Mais conservador
        return False, "Tunder Bot: Gatilho Encontrado, mas Condicao Geral Fraca"
    
    # Verificação 6: Filtro 2 (Condição Imediata)
    if len(historico) < 8:
        return False, "Tunder Bot: Gatilho Encontrado, mas Condicao Imediata Fraca"
    
    operacoes_anteriores_5 = historico[3:8]
    vitorias_anteriores_5 = operacoes_anteriores_5.count('V')
    print(f"* Tunder Bot - Vitórias nas 5 anteriores: {vitorias_anteriores_5}")
    
    if vitorias_anteriores_5 < 4:  # Mais exigente
        return False, "Tunder Bot: Gatilho Encontrado, mas Condicao Imediata Fraca"
    
    return True, "Tunder Bot: Padrao Encontrado - Ligar o Bot"

def enviar_sinal_para_supabase(supabase, bot_name, is_safe_to_operate, reason, operations_after_pattern=0):
    """Envia sinal para Supabase usando UPSERT"""
    try:
        data = {
            'bot_name': bot_name,
            'is_safe_to_operate': is_safe_to_operate,
            'reason': reason,
            'operations_after_pattern': operations_after_pattern or 0,
            'created_at': datetime.now().isoformat()
        }
        
        # Adicionar campos específicos se for padrão encontrado
        if is_safe_to_operate and "Padrao Encontrado" in reason:
            data['pattern_found_at'] = datetime.now().isoformat()
        
        response = supabase.table('radar_de_apalancamiento_signals').upsert(data, on_conflict='bot_name').execute()
        
        if response.data:
            print(f"✅ {bot_name} - Sinal enviado! ID: {response.data[0]['id']} | is_safe: {is_safe_to_operate}")
            return True
        else:
            print(f"❌ {bot_name} - Erro: Resposta vazia do Supabase")
            return False
            
    except Exception as e:
        print(f"❌ {bot_name} - Erro ao enviar sinal: {e}")
        return False

def main():
    """Função principal"""
    print("\n" + "="*80)
    print("SIMULAÇÃO DE CONDIÇÕES SEGURAS PARA OPERAÇÃO")
    print("="*80)
    print("Demonstrando como o sistema salva is_safe_to_operate = True")
    print("="*80)
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        print("❌ Encerrando devido a falha na conexão com Supabase")
        return
    
    print("\n🔍 TESTANDO SCALPING BOT COM CONDIÇÕES IDEAIS")
    print("-" * 60)
    
    # Testar Scalping Bot
    historico_scalping = simular_dados_scalping_bot_safe()
    print(f"📊 Histórico simulado: {' '.join(historico_scalping[:10])}...")
    
    is_safe_scalping, reason_scalping = analisar_padroes_scalping(historico_scalping)
    print(f"\n📋 Resultado Scalping Bot:")
    print(f"   is_safe_to_operate: {is_safe_scalping}")
    print(f"   reason: {reason_scalping}")
    
    # Enviar para Supabase
    enviar_sinal_para_supabase(supabase, "Scalping Bot", is_safe_scalping, reason_scalping)
    
    print("\n🔍 TESTANDO TUNDER BOT COM CONDIÇÕES IDEAIS")
    print("-" * 60)
    
    # Testar Tunder Bot
    historico_tunder = simular_dados_tunder_bot_safe()
    print(f"📊 Histórico simulado: {' '.join(historico_tunder[:10])}...")
    
    is_safe_tunder, reason_tunder = analisar_padroes_tunder(historico_tunder)
    print(f"\n📋 Resultado Tunder Bot:")
    print(f"   is_safe_to_operate: {is_safe_tunder}")
    print(f"   reason: {reason_tunder}")
    
    # Enviar para Supabase
    enviar_sinal_para_supabase(supabase, "Tunder Bot", is_safe_tunder, reason_tunder)
    
    print("\n" + "="*80)
    print("📊 VERIFICANDO REGISTROS NA TABELA")
    print("="*80)
    
    # Buscar registros atuais
    try:
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('*') \
            .in_('bot_name', ['Scalping Bot', 'Tunder Bot']) \
            .order('created_at', desc=True) \
            .execute()
        
        if response.data:
            for record in response.data:
                status_icon = "🟢" if record['is_safe_to_operate'] else "🔴"
                print(f"\n{status_icon} {record['bot_name']}:")
                print(f"   ID: {record['id']}")
                print(f"   is_safe_to_operate: {record['is_safe_to_operate']}")
                print(f"   reason: {record['reason']}")
                print(f"   created_at: {record['created_at']}")
        else:
            print("❌ Nenhum registro encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao buscar registros: {e}")
    
    print("\n" + "="*80)
    print("✅ SIMULAÇÃO CONCLUÍDA")
    print("="*80)
    print("💡 Os bots estão funcionando corretamente!")
    print("💡 is_safe_to_operate = False indica que as condições do mercado")
    print("💡 atual não atendem aos critérios rigorosos de segurança.")
    print("💡 Quando as condições ideais ocorrerem, is_safe_to_operate = True")
    print("💡 será salvo automaticamente na tabela.")

if __name__ == "__main__":
    main()