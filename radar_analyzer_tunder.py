#!/usr/bin/env python3
"""
Radar Analyzer Tunder - Monitor de Estrategias de Trading para Tunder Bot
Sistema de analise continua de operacoes para determinar momentos seguros para operar
Baseado no radar_analyzer.py original, adaptado para o Tunder Bot
"""

import os
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()

# Configuracoes especificas para Tunder Bot
BOT_NAME = 'Tunder Bot'
TABELA_LOGS = 'tunder_bot_logs'
ANALISE_INTERVALO = 5  # segundos entre analises
OPERACOES_MINIMAS = 10  # operacoes minimas para analise (ajustado para Tunder Bot)
OPERACOES_HISTORICO = 30  # operacoes para buscar no historico

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
    """
    Busca as ultimas operacoes da tabela tunder_bot_logs
    Retorna lista de resultados ['V', 'D', 'V', ...] onde V=vitoria, D=derrota
    """
    try:
        print(f"* Buscando ultimas {OPERACOES_HISTORICO} operacoes do Tunder Bot...")
        
        response = supabase.table(TABELA_LOGS) \
            .select('profit_percentage, created_at') \
            .order('id', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        if not response.data:
            print("! Nenhuma operacao encontrada na base de dados do Tunder Bot")
            return [], []
        
        # Converter profit_percentage em V/D e manter timestamps
        historico = []
        timestamps = []
        for operacao in response.data:
            profit_percentage = operacao.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            historico.append(resultado)
            timestamps.append(operacao.get('created_at'))
        
        print(f"* Historico Tunder Bot encontrado ({len(historico)} operacoes): {' '.join(historico[:10])}{'...' if len(historico) > 10 else ''}")
        return historico, timestamps
        
    except Exception as e:
        print(f"X Erro ao buscar operacoes do Tunder Bot: {e}")
        return [], []

def analisar_padroes(historico):
    """
    Aplica todos os filtros de analise na ordem correta de prioridade
    Adaptado para o Tunder Bot com growth rate de 1%
    Retorna tuple (is_safe_to_operate, reason)
    """
    
    # Verificacao 1: Dados suficientes
    if len(historico) < OPERACOES_MINIMAS:
        reason = "Aguardando dados suficientes do Tunder Bot..."
        print(f"... {reason} (Temos {len(historico)}/{OPERACOES_MINIMAS} operacoes)")
        return False, reason
    
    # Pegar ultimas 20 operacoes para analise
    ultimas_20 = historico[:20]
    derrotas_ultimas_20 = ultimas_20.count('D')
    
    print(f"* Analise Tunder Bot das ultimas 20 operacoes: {derrotas_ultimas_20} derrotas")
    
    # Verificacao 2: Filtro de Mercado Instavel (mais conservador para Tunder Bot)
    if derrotas_ultimas_20 > 2:  # Mais restritivo que o accumulator (era 3)
        reason = "Tunder Bot: Mercado Instavel, Volte daqui uns minutos."
        print(f"X {reason} ({derrotas_ultimas_20} derrotas > 2)")
        return False, reason
    
    # Verificacao 3: Filtro de Espera
    if derrotas_ultimas_20 > 1:  # Mais conservador (era 2)
        reason = "Tunder Bot: Esperando o Padrao. Nao ligar ainda."
        print(f"- {reason} ({derrotas_ultimas_20} derrotas > 1)")
        return False, reason
    
    # Verificacao 4: Gatilho V-D-V (mesmo padrao)
    if len(historico) < 3:
        reason = "Tunder Bot: Esperando o Padrao. Nao ligar ainda."
        print(f"- {reason} (Historico insuficiente para padrao V-D-V)")
        return False, reason
    
    # Padrao V-D-V: [0]=mais recente, [1]=anterior, [2]=anterior ao anterior
    padrao_vdv = historico[0] == 'V' and historico[1] == 'D' and historico[2] == 'V'
    print(f"* Verificacao padrao V-D-V Tunder Bot: {historico[0]}-{historico[1]}-{historico[2]} = {'OK' if padrao_vdv else 'NAO'}")
    
    if not padrao_vdv:
        reason = "Tunder Bot: Esperando o Padrao. Nao ligar ainda."
        print(f"- {reason} (Padrao V-D-V nao encontrado)")
        return False, reason
    
    print("OK - Gatilho V-D-V encontrado no Tunder Bot! Aplicando filtros adicionais...")
    
    # Verificacao 5: Filtro 1 (Condicao Geral) - 10 operacoes anteriores ao padrao
    if len(historico) < 13:  # Precisamos de pelo menos 13 para ter 10 anteriores
        reason = "Tunder Bot: Gatilho Encontrado, mas Condicao Geral Fraca"
        print(f"! {reason} (Historico insuficiente para Filtro 1)")
        return False, reason
    
    operacoes_anteriores_10 = historico[3:13]  # indices 3 a 12
    derrotas_anteriores_10 = operacoes_anteriores_10.count('D')
    print(f"* Filtro 1 Tunder Bot (Condicao Geral): {derrotas_anteriores_10} derrotas nas 10 operacoes anteriores")
    
    if derrotas_anteriores_10 > 1:  # Mais conservador (era 2)
        reason = "Tunder Bot: Gatilho Encontrado, mas Condicao Geral Fraca"
        print(f"! {reason} ({derrotas_anteriores_10} derrotas > 1)")
        return False, reason
    
    # Verificacao 6: Filtro 2 (Condicao Imediata) - 5 operacoes anteriores ao padrao
    if len(historico) < 8:  # Precisamos de pelo menos 8 para ter 5 anteriores
        reason = "Tunder Bot: Gatilho Encontrado, mas Condicao Imediata Fraca"
        print(f"! {reason} (Historico insuficiente para Filtro 2)")
        return False, reason
    
    operacoes_anteriores_5 = historico[3:8]  # indices 3 a 7
    vitorias_anteriores_5 = operacoes_anteriores_5.count('V')
    print(f"* Filtro 2 Tunder Bot (Condicao Imediata): {vitorias_anteriores_5} vitorias nas 5 operacoes anteriores")
    
    if vitorias_anteriores_5 < 4:  # Mais exigente (era 3)
        reason = "Tunder Bot: Gatilho Encontrado, mas Condicao Imediata Fraca"
        print(f"! {reason} ({vitorias_anteriores_5} vitorias < 4)")
        return False, reason
    
    # Todas as verificacoes aprovadas
    reason = "Tunder Bot: Patron Encontrado, Activar Bot Ahora!"
    print(f"OK - {reason} - Todas as condicoes foram atendidas!")
    return True, reason

def buscar_ultimo_sinal(supabase):
    """
    Busca o ultimo sinal enviado para verificar estado do controle de operacoes do Tunder Bot
    """
    try:
        # Tentar buscar com colunas novas primeiro
        try:
            response = supabase.table('radar_de_apalancamiento_signals') \
                .select('*, pattern_found_at, operations_after_pattern') \
                .eq('bot_name', BOT_NAME) \
                .order('id', desc=True) \
                .limit(1) \
                .execute()
        except:
            # Fallback para colunas basicas
            response = supabase.table('radar_de_apalancamiento_signals') \
                .select('*') \
                .eq('bot_name', BOT_NAME) \
                .order('id', desc=True) \
                .limit(1) \
                .execute()
        
        if response.data:
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"X Erro ao buscar ultimo sinal do Tunder Bot: {e}")
        return None

def contar_operacoes_apos_padrao(supabase, pattern_found_at):
    """
    Conta quantas operacoes do Tunder Bot aconteceram apos o padrao ser encontrado
    """
    try:
        if not pattern_found_at:
            return 0
            
        response = supabase.table(TABELA_LOGS) \
            .select('id') \
            .gte('created_at', pattern_found_at) \
            .execute()
        
        return len(response.data) if response.data else 0
        
    except Exception as e:
        print(f"X Erro ao contar operacoes apos padrao do Tunder Bot: {e}")
        return 0

def calcular_estatisticas_bot(supabase, historico):
    """Calcula estatísticas baseadas no histórico atual"""
    try:
        if len(historico) < 20:
            return 0, 0, 0.0
        
        # Últimas 10 operações para losses
        ultimas_10 = historico[:10]
        losses_10 = ultimas_10.count('D')
        
        # Últimas 5 operações para wins
        ultimas_5 = historico[:5]
        wins_5 = ultimas_5.count('V')
        
        # Precisão histórica geral
        total_wins = historico.count('V')
        total_ops = len(historico)
        accuracy = round((total_wins / total_ops) * 100, 2) if total_ops > 0 else 0.0
        
        return losses_10, wins_5, accuracy
        
    except Exception as e:
        print(f"Erro ao calcular estatísticas: {e}")
        return 0, 0, 0.0

def enviar_sinal_para_supabase(supabase, is_safe_to_operate, reason, pattern_found_at=None, operations_after_pattern=0, historico=None):
    """Envia o sinal com estatísticas calculadas"""
    try:
        # CALCULAR estatísticas reais
        losses_10, wins_5, accuracy = calcular_estatisticas_bot(supabase, historico or [])
        
        data = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': is_safe_to_operate,
            'reason': reason,
            'operations_after_pattern': operations_after_pattern or 0,
            'losses_in_last_10_ops': losses_10,  # VALOR REAL
            'wins_in_last_5_ops': wins_5,        # VALOR REAL
            'historical_accuracy': accuracy,      # VALOR REAL
            'created_at': datetime.now().isoformat(),
            'last_pattern_found': 'V-D-V' if 'Patron Encontrado' in reason else 'Aguardando',
            'auto_disable_after_ops': 3
        }
        
        # Adicionar campos de controle se existirem
        if pattern_found_at:
            data['pattern_found_at'] = pattern_found_at
            
        response = supabase.table('radar_de_apalancamiento_signals').upsert(data, on_conflict='bot_name').execute()
        
        if response.data:
            print(f"✓ Sinal Tunder Bot enviado - Losses(10): {losses_10}, Wins(5): {wins_5}, Accuracy: {accuracy}%")
            return True
        return False
            
    except Exception as e:
        print(f"X Erro ao enviar sinal Tunder Bot: {e}")
        return False

def analisar_e_enviar_sinal(supabase):
    """
    Funcao principal de analise que executa todo o processo para o Tunder Bot
    """
    print(f"\n{'='*60}")
    print(f">> INICIANDO ANALISE TUNDER BOT - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Passo 0: Verificar estado atual do controle de operacoes
    ultimo_sinal = buscar_ultimo_sinal(supabase)
    
    # Passo 1: Buscar dados
    historico, timestamps = buscar_operacoes_historico(supabase)
    
    if not historico:
        # Enviar sinal neutro se nao ha dados
        reason = "Tunder Bot: Aguardando dados suficientes..."
        enviar_sinal_para_supabase(supabase, False, reason)
        return
    
    # Passo 2: Verificar se ja temos um padrao ativo e contar operacoes
    pattern_found_at = None
    operations_after_pattern = 0
    
    # Verificar se o controle de operacoes esta disponivel
    if ultimo_sinal and ultimo_sinal.get('pattern_found_at') is not None:
        # Modo completo - com controle de operacoes
        if ultimo_sinal.get('is_safe_to_operate'):
            pattern_found_at = ultimo_sinal.get('pattern_found_at')
            operations_after_pattern = contar_operacoes_apos_padrao(supabase, pattern_found_at)
            
            print(f"* Padrao Tunder Bot ativo desde: {pattern_found_at}")
            print(f"* Operacoes Tunder Bot apos padrao: {operations_after_pattern}")
            
            # Verificar se deve desligar apos 3 operacoes
            if operations_after_pattern >= 3:
                reason = "Tunder Bot: Bot Desligado - 3 operacoes completadas apos o padrao"
                print(f"! {reason}")
                sucesso = enviar_sinal_para_supabase(supabase, False, reason, pattern_found_at, operations_after_pattern)
                
                # Log final
                print(f"\n[STOP] RESULTADO FINAL TUNDER BOT: BOT DESLIGADO AUTOMATICAMENTE")
                print(f"* Motivo: {reason}")
                print(f"* Status do envio: {'Enviado' if sucesso else 'Falhou'}")
                return False, reason
    else:
        # Modo compatibilidade - sem controle de operacoes
        print(f"* Modo compatibilidade Tunder Bot: Controle de operacoes nao disponivel")
    
    # Passo 3: Aplicar filtros e analise
    is_safe_to_operate, reason = analisar_padroes(historico)
    
    # Passo 4: Se encontrou novo padrao, marcar timestamp
    if is_safe_to_operate and "Patron Encontrado" in reason:
        pattern_found_at = datetime.now().isoformat()
        operations_after_pattern = 0
        print(f"* Novo padrao Tunder Bot encontrado! Timestamp: {pattern_found_at}")
    elif ultimo_sinal and ultimo_sinal.get('pattern_found_at') and ultimo_sinal.get('is_safe_to_operate'):
        # Manter dados do padrao anterior se ainda ativo
        pattern_found_at = ultimo_sinal.get('pattern_found_at')
    
    # Passo 5: Enviar resultado
    sucesso = enviar_sinal_para_supabase(supabase, is_safe_to_operate, reason, pattern_found_at, operations_after_pattern, historico)
    
    # Log final
    status_icon = "OK" if is_safe_to_operate else "WAIT"
    print(f"\n[{status_icon}] RESULTADO FINAL TUNDER BOT: {'SAFE TO OPERATE' if is_safe_to_operate else 'WAIT'}")
    print(f"* Motivo: {reason}")
    print(f"* Operacoes apos padrao: {operations_after_pattern}/3")
    print(f"* Status do envio: {'Enviado' if sucesso else 'Falhou'}")
    
    return is_safe_to_operate, reason

def main():
    """
    Loop principal do radar analyzer para Tunder Bot
    """
    print("\n" + "="*70)
    print("RADAR ANALYZER TUNDER - Monitor de Estrategias de Trading")
    print("="*70)
    print(f"Bot: {BOT_NAME}")
    print(f"Tabela de logs: {TABELA_LOGS}")
    print(f"Intervalo de analise: {ANALISE_INTERVALO} segundos")
    print(f"Operacoes minimas: {OPERACOES_MINIMAS}")
    print(f"Historico analisado: {OPERACOES_HISTORICO} operacoes")
    print(f"Growth Rate: 1% (mais conservador)")
    print("="*70)
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        print("X Encerrando devido a falha na conexao com Supabase")
        return
    
    # Loop infinito
    ciclo = 0
    try:
        while True:
            ciclo += 1
            print(f"\n>> CICLO TUNDER BOT {ciclo} - {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                # Executar analise
                analisar_e_enviar_sinal(supabase)
                
            except Exception as e:
                print(f"X Erro no ciclo de analise Tunder Bot: {e}")
            
            # Aguardar proximo ciclo
            print(f"\n... Aguardando {ANALISE_INTERVALO}s para proxima analise Tunder Bot...")
            time.sleep(ANALISE_INTERVALO)
            
    except KeyboardInterrupt:
        print(f"\n! Radar Analyzer Tunder interrompido pelo usuario")
    except Exception as e:
        print(f"X Erro critico no loop principal Tunder Bot: {e}")
    
    print("* Radar Analyzer Tunder finalizado")

if __name__ == "__main__":
    main()