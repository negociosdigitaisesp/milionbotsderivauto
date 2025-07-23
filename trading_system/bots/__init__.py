# Bots Package
"""
Trading System Bots - Módulo principal dos bots de trading
"""

# Importações dos bots individuais
from .bk_bot import bot_bk_1_0
from .factor50x_bot import bot_factor_50x
from .ai_bot import bot_ai_2_0
from .aplan_bot import bot_apalancamiento
from .sniper_bot import bot_sniper_martingale
from .quantum_bot import bot_quantum_fixed_stake
from .wolf_bot import wolf_bot_2_0
from .scale_bot import bot_scale

__all__ = [
    'bot_bk_1_0',
    'bot_factor_50x',
    'bot_ai_2_0',
    'bot_apalancamiento',
    'bot_sniper_martingale',
    'bot_quantum_fixed_stake',
    'wolf_bot_2_0',
    'bot_scale'
]