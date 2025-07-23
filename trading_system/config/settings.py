"""
Configurações centralizadas do sistema de trading automatizado
Gerencia variáveis de ambiente e configurações globais
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ==================== CONFIGURAÇÕES DA DERIV API ====================
DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")

# ==================== CONFIGURAÇÕES DO SUPABASE ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ==================== VALIDAÇÃO DAS VARIÁVEIS DE AMBIENTE ====================
def validate_environment_variables():
    """
    Valida se todas as variáveis de ambiente necessárias estão configuradas
    
    Raises:
        ValueError: Se alguma variável de ambiente estiver faltando
    """
    required_vars = {
        'DERIV_APP_ID': DERIV_APP_ID,
        'DERIV_API_TOKEN': DERIV_API_TOKEN,
        'SUPABASE_URL': SUPABASE_URL,
        'SUPABASE_KEY': SUPABASE_KEY
    }
    
    missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]
    
    if missing_vars:
        raise ValueError(
            f"❌ Erro: Variáveis de ambiente não encontradas: {', '.join(missing_vars)}. "
            "Verifique o arquivo .env"
        )

# ==================== INICIALIZAÇÃO DO CLIENTE SUPABASE ====================
def get_supabase_client() -> Client:
    """
    Retorna uma instância configurada do cliente Supabase
    
    Returns:
        Client: Cliente Supabase configurado
    """
    validate_environment_variables()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== CONFIGURAÇÕES GERAIS DOS BOTS ====================
class BotConfig:
    """Configurações padrão para os bots de trading"""
    
    # Configurações de tempo
    DEFAULT_SLEEP_TIME = 1  # segundos entre operações
    CONNECTION_RETRY_DELAY = 15  # segundos para tentar reconectar
    CONTRACT_TIMEOUT = 30  # segundos máximo para aguardar resultado do contrato
    
    # Configurações de trading padrão
    DEFAULT_STAKE = 1.0
    DEFAULT_CURRENCY = "USD"
    DEFAULT_DURATION = 1
    DEFAULT_DURATION_UNIT = "t"
    
    # Configurações de logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== CONFIGURAÇÕES ESPECÍFICAS POR BOT ====================
class BotSpecificConfig:
    """Configurações específicas para cada bot - Otimizado para VPS com operação infinita"""
    
    # Configurações para operação infinita em VPS
    INFINITE_STOP = 999999999.0  # Stop loss/win ilimitado
    MAX_MARTINGALE_LEVELS = 5    # Máximo 5 martingales
    STAKE_INICIAL_VPS = 1.0      # Stake inicial fixo $1.00
    
    BK_BOT_CONFIG = {
        'stake_inicial': STAKE_INICIAL_VPS,
        'stake_maximo': STAKE_INICIAL_VPS * (2 ** MAX_MARTINGALE_LEVELS),  # $1 * 2^5 = $32
        'max_martingale_levels': MAX_MARTINGALE_LEVELS,
        'stop_loss': INFINITE_STOP,
        'stop_win': INFINITE_STOP,
        'symbol': '1HZ10V',
        'contract_type': 'DIGITUNDER',
        'martingale_enabled': True
    }
    
    FACTOR50X_CONFIG = {
        'stake_inicial': STAKE_INICIAL_VPS,
        'stake_maximo': STAKE_INICIAL_VPS * (2 ** MAX_MARTINGALE_LEVELS),  # $1 * 2^5 = $32
        'max_martingale_levels': MAX_MARTINGALE_LEVELS,
        'stop_loss': INFINITE_STOP,
        'stop_win': INFINITE_STOP,
        'symbol': 'R_100',
        'contract_type': 'DIGITOVER',
        'trigger_digit': 1,
        'barrier': 3,
        'martingale_enabled': True
    }
    
    AI_BOT_CONFIG = {
        'stake_inicial': STAKE_INICIAL_VPS,
        'stake_maximo': STAKE_INICIAL_VPS * (2 ** MAX_MARTINGALE_LEVELS),  # $1 * 2^5 = $32
        'max_martingale_levels': MAX_MARTINGALE_LEVELS,
        'stop_loss': INFINITE_STOP,
        'stop_win': INFINITE_STOP,
        'symbol': 'R_100',
        'contract_type': 'DIGITOVER',
        'barrier': 0,
        'martingale_enabled': True
    }
    
    APALANCAMIENTO_CONFIG = {
        'stake_inicial': STAKE_INICIAL_VPS,
        'stake_maximo': STAKE_INICIAL_VPS * (2 ** MAX_MARTINGALE_LEVELS),  # $1 * 2^5 = $32
        'max_martingale_levels': MAX_MARTINGALE_LEVELS,
        'stop_loss': INFINITE_STOP,
        'stop_win': INFINITE_STOP,
        'limite_trades_para_troca': 100,
        'symbol': 'R_100',
        'martingale_enabled': True
    }
    
    SNIPER_CONFIG = {
        'stake_inicial': STAKE_INICIAL_VPS,
        'stake_maximo': STAKE_INICIAL_VPS * (2 ** MAX_MARTINGALE_LEVELS),  # $1 * 2^5 = $32
        'max_martingale_levels': MAX_MARTINGALE_LEVELS,
        'martingale_fator': 2.0,  # Fator de multiplicação do martingale
        'stop_loss': INFINITE_STOP,
        'stop_win': INFINITE_STOP,
        'symbol': '1HZ100V',
        'martingale_enabled': True
    }
    
    QUANTUM_CONFIG = {
        'stake_inicial': STAKE_INICIAL_VPS,
        'stake_maximo': STAKE_INICIAL_VPS * (2 ** MAX_MARTINGALE_LEVELS),  # $1 * 2^5 = $32
        'max_martingale_levels': MAX_MARTINGALE_LEVELS,
        'stop_loss': INFINITE_STOP,
        'stop_win': INFINITE_STOP,
        'symbol': 'R_100',
        'contract_type': 'DIGITDIFF',
        'martingale_enabled': True
    }
    
    WOLF_CONFIG = {
        'stake_inicial': STAKE_INICIAL_VPS,
        'stake_maximo': STAKE_INICIAL_VPS * (2 ** MAX_MARTINGALE_LEVELS),  # $1 * 2^5 = $32
        'max_martingale_levels': MAX_MARTINGALE_LEVELS,
        'stop_loss': INFINITE_STOP,
        'stop_win': INFINITE_STOP,
        'symbol': 'R_100',
        'martingale_enabled': True
    }

# Validar configurações na importação
validate_environment_variables()