#!/usr/bin/env python3
"""
Teste de um ciclo completo do Radar Analyzer
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()

BOT_NAME = 'Scalping Bot'
OPERACOES_MINIMAS = 20
OPERACOES_HISTORICO = 30

def inicializar_supabase():
    """Inicializa conexao com Supabase"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Credenciais do Supabase nao encontradas no arquivo .env")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("OK - Conexao com Supabase estabelecida com sucesso")
        return supabase
        
    except Exception as e:
        print(f"X Erro ao conectar com Supabase: {e}")
        return None

def buscar_operacoes_historico(supabase):
    """Busca as ultimas operacoes"""
    try:
        print(f"* Buscando ultimas {OPERACOES_HISTORICO} operacoes...")
        
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('profit_percentage') \
            .order('id', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        if not response.data:
            print("! Nenhuma operacao encontrada na base de dados")
            return []
        
        # Converter profit_percentage em V/D
        historico = []
        for operacao in response.data:
            profit_percentage = operacao.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            historico.append(resultado)
        
        print(f"* Historico encontrado ({len(historico)} operacoes): {' '.join(historico[:10])}{'...' if len(historico) > 10 else ''}")
        return historico
        
    except Exception as e:
        print(f"X Erro ao buscar operacoes: {e}")
        return []

def analisar_padroes(historico):
    """Aplica todos os filtros de analise"""
    
    # Verificacao 1: Dados suficientes
    if len(historico) < OPERACOES_MINIMAS:
        reason = "Aguardando dados suficientes..."
        print(f"... {reason} (Temos {len(historico)}/{OPERACOES_MINIMAS} operacoes)")
        return False, reason
    
    # Pegar ultimas 20 operacoes para analise
    ultimas_20 = historico[:20]
    derrotas_ultimas_20 = ultimas_20.count('D')
    
    print(f"* Analise das ultimas 20 operacoes: {derrotas_ultimas_20} derrotas")
    
    # Verificacao 2: Filtro de Mercado Instavel
    if derrotas_ultimas_20 > 3:
        reason = "Mercado Instavel, Volte daqui uns minutos."
        print(f"X {reason} ({derrotas_ultimas_20} derrotas > 3)")
        return False, reason
    
    # Verificacao 3: Filtro de Espera
    if derrotas_ultimas_20 > 2:
        reason = "Esperando o Padrao. Nao ligar ainda."
        print(f"- {reason} ({derrotas_ultimas_20} derrotas > 2)")
        return False, reason
    
    # Verificacao 4: Gatilho V-D-V
    if len(historico) < 3:
        reason = "Esperando o Padrao. Nao ligar ainda."
        print(f"- {reason} (Historico insuficiente para padrao V-D-V)")
        return False, reason
    
    # Padrao V-D-V: [0]=mais recente, [1]=anterior, [2]=anterior ao anterior
    padrao_vdv = historico[0] == 'V' and historico[1] == 'D' and historico[2] == 'V'
    print(f"* Verificacao padrao V-D-V: {historico[0]}-{historico[1]}-{historico[2]} = {'OK' if padrao_vdv else 'NAO'}")
    
    if not padrao_vdv:
        reason = "Esperando o Padrao. Nao ligar ainda."
        print(f"- {reason} (Padrao V-D-V nao encontrado)")
        return False, reason
    
    print("OK - Gatilho V-D-V encontrado! Aplicando filtros adicionais...")
    
    # Verificacao 5: Filtro 1 (Condicao Geral) - 10 operacoes anteriores ao padrao
    if len(historico) < 13:  # Precisamos de pelo menos 13 para ter 10 anteriores
        reason = "Gatilho Encontrado, mas Condicao Geral Fraca"
        print(f"! {reason} (Historico insuficiente para Filtro 1)")
        return False, reason
    
    operacoes_anteriores_10 = historico[3:13]  # indices 3 a 12
    derrotas_anteriores_10 = operacoes_anteriores_10.count('D')
    print(f"* Filtro 1 (Condicao Geral): {derrotas_anteriores_10} derrotas nas 10 operacoes anteriores")
    
    if derrotas_anteriores_10 > 2:
        reason = "Gatilho Encontrado, mas Condicao Geral Fraca"
        print(f"! {reason} ({derrotas_anteriores_10} derrotas > 2)")
        return False, reason
    
    # Verificacao 6: Filtro 2 (Condicao Imediata) - 5 operacoes anteriores ao padrao
    if len(historico) < 8:  # Precisamos de pelo menos 8 para ter 5 anteriores
        reason = "Gatilho Encontrado, mas Condicao Imediata Fraca"
        print(f"! {reason} (Historico insuficiente para Filtro 2)")
        return False, reason
    
    operacoes_anteriores_5 = historico[3:8]  # indices 3 a 7
    vitorias_anteriores_5 = operacoes_anteriores_5.count('V')
    print(f"* Filtro 2 (Condicao Imediata): {vitorias_anteriores_5} vitorias nas 5 operacoes anteriores")
    
    if vitorias_anteriores_5 < 3:
        reason = "Gatilho Encontrado, mas Condicao Imediata Fraca"
        print(f"! {reason} ({vitorias_anteriores_5} vitorias < 3)")
        return False, reason
    
    # Todas as verificacoes aprovadas
    reason = "Padrao Encontrado - Ligar o Bot"
    print(f"OK - {reason} - Todas as condicoes foram atendidas!")
    return True, reason

def enviar_sinal_para_supabase(supabase, is_safe_to_operate, reason):
    """Envia sinal para tabela"""
    try:
        payload = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': is_safe_to_operate,
            'reason': reason
        }
        
        print(f">> Enviando sinal: is_safe={is_safe_to_operate}, reason='{reason}'")
        
        response = supabase.table('radar_de_apalancamiento_signals') \
            .insert(payload) \
            .execute()
        
        print("OK - Sinal enviado com sucesso para Supabase")
        return True
        
    except Exception as e:
        print(f"X Erro ao enviar sinal para Supabase: {e}")
        return False

def main():
    print("=== TESTE CICLO COMPLETO RADAR ANALYZER ===")
    
    supabase = inicializar_supabase()
    if not supabase:
        print("FALHA: Nao foi possivel conectar")
        return
    
    print(f"\n{'='*50}")
    print(f">> EXECUTANDO ANALISE COMPLETA")
    print(f"{'='*50}")
    
    # Passo 1: Buscar dados
    historico = buscar_operacoes_historico(supabase)
    
    if not historico:
        # Enviar sinal neutro se nao ha dados
        reason = "Aguardando dados suficientes..."
        enviar_sinal_para_supabase(supabase, False, reason)
        print("\n=== ANALISE FINALIZADA (SEM DADOS) ===")
        return
    
    # Passo 2: Aplicar filtros e analise
    is_safe_to_operate, reason = analisar_padroes(historico)
    
    # Passo 3: Enviar resultado
    sucesso = enviar_sinal_para_supabase(supabase, is_safe_to_operate, reason)
    
    # Log final
    status_icon = "SAFE" if is_safe_to_operate else "WAIT"
    print(f"\n{'='*50}")
    print(f"[{status_icon}] RESULTADO FINAL: {'SAFE TO OPERATE' if is_safe_to_operate else 'WAIT'}")
    print(f"* Motivo: {reason}")
    print(f"* Status do envio: {'Enviado' if sucesso else 'Falhou'}")
    print(f"{'='*50}")
    
    print("\n=== CICLO COMPLETO FINALIZADO ===")

if __name__ == "__main__":
    main()