#!/usr/bin/env python3
"""
Radar Analyzer - Monitor de Estrategias de Trading para Deriv
Sistema de analise continua de operacoes para determinar momentos seguros para operar
"""

import os
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()

# Configuracoes
BOT_NAME = 'Scalping Bot'
ANALISE_INTERVALO = 5  # segundos entre analises
OPERACOES_MINIMAS = 20  # operacoes minimas para analise
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
    Busca as ultimas operacoes da tabela scalping_accumulator_bot_logs
    Retorna lista de resultados ['V', 'D', 'V', ...] onde V=vitoria, D=derrota
    """
    try:
        print(f"* Buscando ultimas {OPERACOES_HISTORICO} operacoes...")
        
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('profit_percentage, created_at') \
            .order('id', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        if not response.data:
            print("! Nenhuma operacao encontrada na base de dados")
            return [], []
        
        # Converter profit_percentage em V/D e manter timestamps
        historico = []
        timestamps = []
        for operacao in response.data:
            profit_percentage = operacao.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            historico.append(resultado)
            timestamps.append(operacao.get('created_at'))
        
        print(f"* Historico encontrado ({len(historico)} operacoes): {' '.join(historico[:10])}{'...' if len(historico) > 10 else ''}")
        return historico, timestamps
        
    except Exception as e:
        print(f"X Erro ao buscar operacoes: {e}")
        return [], []

def analisar_padroes(historico):
    """
    Sistema de 3 Sinais Combinados para Scalping Bot
    Retorna tuple (is_safe_to_operate, reason)
    """
    
    if len(historico) < 20:
        return False, "Esperando el patrón. No activar aún."
    
    print(f"* Analisando 3 Sinais: {' '.join(historico[:20])}")
    
    # SINAL 1: LOSS após 4+ WINS consecutivos
    def sinal_reset():
        for i in range(len(historico) - 4):
            # Procurar por 4+ WINS consecutivos seguidos de LOSS
            if historico[i] == 'D':  # LOSS encontrado
                wins_consecutivos = 0
                # Contar WINS consecutivos após o LOSS
                for j in range(i + 1, len(historico)):
                    if historico[j] == 'V':
                        wins_consecutivos += 1
                    else:
                        break
                
                if wins_consecutivos >= 4:
                    # Verificar se já houve 2 WINS consecutivos após este padrão
                    if len(historico) >= 2 and historico[0] == 'V' and historico[1] == 'V':
                        return False, -1, ""  # Padrão consumido pelos 2 WINS
                    return True, i, "Patrón encontrado - encender bot"
        return False, -1, ""
    
    # SINAL 2: WIN após exatamente 2 LOSS consecutivos
    def sinal_confirmacao():
        for i in range(len(historico) - 2):
            # Procurar por WIN seguido de exatamente 2 LOSS
            if (historico[i] == 'V' and 
                historico[i+1] == 'D' and 
                historico[i+2] == 'D'):
                # Verificar se não há mais LOSS após os 2
                if i + 3 >= len(historico) or historico[i+3] != 'D':
                    # Verificar se já houve 2 WINS consecutivos após este padrão
                    if len(historico) >= 2 and historico[0] == 'V' and historico[1] == 'V':
                        return False, -1, ""  # Padrão consumido pelos 2 WINS
                    return True, i, "Patrón encontrado - encender bot"
        return False, -1, ""
    
    # SINAL 3: Analisar apenas as últimas 20 operações com 7+ LOSS
    def sinal_pos_estresse():
        # Verificar se há pelo menos 20 operações
        if len(historico) < 20:
            return False, -1, ""
            
        # Pegar exatamente as últimas 20 operações
        ultimas_20 = historico[:20]
        losses = ultimas_20.count('D')
        
        if losses >= 7:
            # Verificar se já houve 2 WINS consecutivos após detectar este padrão
            if len(historico) >= 2 and historico[0] == 'V' and historico[1] == 'V':
                return False, -1, ""  # Padrão consumido pelos 2 WINS
            return True, 0, "Patrón encontrado - encender bot"
        return False, -1, ""
    
    # Verificar sinais
    s1, p1, d1 = sinal_reset()
    s2, p2, d2 = sinal_confirmacao()
    s3, p3, d3 = sinal_pos_estresse()
    
    if not (s1 or s2 or s3):
        return False, "Esperando el patrón. No activar aún."
    
    # Sinal mais recente
    sinais = []
    if s1: sinais.append((p1, "RESET", d1))
    if s2: sinais.append((p2, "CONFIRMAÇÃO", d2))
    if s3: sinais.append((p3, "PÓS-ESTRESSE", d3))
    
    sinais.sort(key=lambda x: x[0])
    pos, tipo, desc = sinais[0]
    
    print(f"* Sinal ativo: {tipo} - {desc}")
    
    # Retornar mensagem em espanhol para ativar bot
    return True, f"Patrón encontrado - encender bot"

def buscar_ultimo_sinal(supabase):
    """
    Busca o ultimo sinal enviado para verificar estado do controle de operacoes
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
        print(f"X Erro ao buscar ultimo sinal: {e}")
        return None

def contar_operacoes_apos_padrao(supabase, pattern_found_at):
    """
    Conta quantas operacoes aconteceram apos o padrao ser encontrado
    """
    try:
        if not pattern_found_at:
            return 0
            
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('id') \
            .gte('created_at', pattern_found_at) \
            .execute()
        
        return len(response.data) if response.data else 0
        
    except Exception as e:
        print(f"X Erro ao contar operacoes apos padrao: {e}")
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
    """Envia sinal com estatísticas calculadas e timestamp para realtime"""
    try:
        losses_10, wins_5, accuracy = calcular_estatisticas_bot(supabase, historico or [])
        
        current_time = datetime.now().isoformat()
        
        data = {
            'bot_name': BOT_NAME,  # 'Scalping Bot'
            'is_safe_to_operate': is_safe_to_operate,
            'reason': reason,
            'operations_after_pattern': operations_after_pattern or 0,
            'losses_in_last_10_ops': losses_10,
            'wins_in_last_5_ops': wins_5,
            'historical_accuracy': accuracy,
            'created_at': current_time,
            'last_pattern_found': 'SINAL_COMBINADO' if 'Patrón Encontrado' in reason else 'Aguardando',
            'auto_disable_after_ops': 2  # Buscar apenas 2 WINS
        }
        
        if pattern_found_at:
            data['pattern_found_at'] = pattern_found_at
            
        response = supabase.table('radar_de_apalancamiento_signals').upsert(data, on_conflict='bot_name').execute()
        
        if response.data:
            print(f"✓ Sinal Scalping Bot enviado - Losses(10): {losses_10}, Wins(5): {wins_5}, Accuracy: {accuracy}%")
            return True
        return False
            
    except Exception as e:
        print(f"X Erro ao enviar sinal Scalping Bot: {e}")
        return False

def analisar_e_enviar_sinal(supabase):
    """
    Funcao principal de analise que executa todo o processo
    """
    print(f"\n{'='*60}")
    print(f">> INICIANDO ANALISE - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Passo 0: Verificar estado atual do controle de operacoes
    ultimo_sinal = buscar_ultimo_sinal(supabase)
    
    # Passo 1: Buscar dados
    historico, timestamps = buscar_operacoes_historico(supabase)
    
    if not historico:
        # Enviar sinal neutro se nao ha dados
        reason = "Aguardando dados suficientes..."
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
            
            print(f"* Padrao ativo desde: {pattern_found_at}")
            print(f"* Operacoes apos padrao: {operations_after_pattern}")
            
            # Verificar se deve desligar após 2 operações (não 3)
            if operations_after_pattern >= 2:
                reason = "Scalping Bot: Desligado - 2 operações completadas após sinal combinado"
                print(f"! {reason}")
                sucesso = enviar_sinal_para_supabase(supabase, False, reason, pattern_found_at, operations_after_pattern, historico)
                return False, reason
    else:
        # Modo compatibilidade - sem controle de operacoes
        print(f"* Modo compatibilidade: Controle de operacoes nao disponivel")
    
    # Passo 3: Aplicar filtros e analise
    is_safe_to_operate, reason = analisar_padroes(historico)
    
    # Passo 4: Se encontrou novo padrao, marcar timestamp
    if is_safe_to_operate and reason == "Padrao Encontrado - Ligar o Bot":
        pattern_found_at = datetime.now().isoformat()
        operations_after_pattern = 0
        print(f"* Novo padrao encontrado! Timestamp: {pattern_found_at}")
    elif ultimo_sinal and ultimo_sinal.get('pattern_found_at') and ultimo_sinal.get('is_safe_to_operate'):
        # Manter dados do padrao anterior se ainda ativo
        pattern_found_at = ultimo_sinal.get('pattern_found_at')
    
    # Passo 5: Enviar resultado
    sucesso = enviar_sinal_para_supabase(supabase, is_safe_to_operate, reason, pattern_found_at, operations_after_pattern, historico)
    
    # Log final
    status_icon = "OK" if is_safe_to_operate else "WAIT"
    print(f"\n[{status_icon}] RESULTADO FINAL: {'SAFE TO OPERATE' if is_safe_to_operate else 'WAIT'}")
    print(f"* Motivo: {reason}")
    print(f"* Operacoes apos padrao: {operations_after_pattern}/3")
    print(f"* Status do envio: {'Enviado' if sucesso else 'Falhou'}")
    
    return is_safe_to_operate, reason

def main():
    """
    Loop principal do radar analyzer
    """
    print("\n" + "="*70)
    print("RADAR ANALYZER - Monitor de Estrategias de Trading")
    print("="*70)
    print(f"Bot: {BOT_NAME}")
    print(f"Intervalo de analise: {ANALISE_INTERVALO} segundos")
    print(f"Operacoes minimas: {OPERACOES_MINIMAS}")
    print(f"Historico analisado: {OPERACOES_HISTORICO} operacoes")
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
            print(f"\n>> CICLO {ciclo} - {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                # Executar analise
                analisar_e_enviar_sinal(supabase)
                
            except Exception as e:
                print(f"X Erro no ciclo de analise: {e}")
            
            # Aguardar proximo ciclo
            print(f"\n... Aguardando {ANALISE_INTERVALO}s para proxima analise...")
            time.sleep(ANALISE_INTERVALO)
            
    except KeyboardInterrupt:
        print(f"\n! Radar Analyzer interrompido pelo usuario")
    except Exception as e:
        print(f"X Erro critico no loop principal: {e}")
    
    print("* Radar Analyzer finalizado")

if __name__ == "__main__":
    main()