#!/usr/bin/env python3
"""
EXEMPLO DE USO - ESTRATÉGIA ALAVANCS PRO 2.0
===========================================

Este script demonstra como usar a nova estratégia ALAVANCS PRO 2.0
implementada no AccumulatorScalpingBot.

CARACTERÍSTICAS DA ESTRATÉGIA ALAVANCS PRO 2.0:
- Análise reativa de ticks em tempo real
- Buffer de ticks com filtros probabilísticos
- Detecção de padrões consecutivos
- Sistema de gestão de risco com pausa de segurança
- Predição dinâmica baseada em sinais de mercado

MELHORIAS EM RELAÇÃO À VERSÃO ANTERIOR:
- Redução de perdas consecutivas através de pausa de segurança
- Análise mais precisa com buffer de ticks
- Filtros probabilísticos para melhor entrada
- Sistema reativo ao invés de operações fixas
"""

import asyncio
import logging
from tunderbotalavanca import AccumulatorScalpingBot

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alavancs_pro.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Função principal para executar a estratégia ALAVANCS PRO 2.0"""
    
    # Configuração da conta (substitua pelos seus dados reais)
    account_config = {
        'name': 'ALAVANCS_PRO_DEMO',
        'token': 'SEU_TOKEN_DERIV_AQUI',  # Substitua pelo seu token real
        'app_id': 1089,
        'server': 'frontend.derivws.com'
    }
    
    logger.info("🚀 INICIANDO DEMONSTRAÇÃO ALAVANCS PRO 2.0")
    logger.info("="*60)
    
    try:
        # Criar instância do bot
        bot = AccumulatorScalpingBot(account_config)
        
        logger.info("✅ Bot ALAVANCS PRO 2.0 criado com sucesso")
        logger.info("📊 Configurações:")
        logger.info(f"   - Stake inicial: $2.00")
        logger.info(f"   - Ativo: Volatility 75 Index")
        logger.info(f"   - Meta de lucro: $50.00")
        logger.info(f"   - Limite de perda: $20.00")
        logger.info(f"   - Pausa de segurança: 3 perdas consecutivas")
        logger.info("="*60)
        
        # Iniciar estratégia ALAVANCS PRO 2.0
        await bot.start_alavancs_pro()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}")
    finally:
        logger.info("🏁 Demonstração finalizada")

def exemplo_configuracao_multiplas_contas():
    """Exemplo de configuração para múltiplas contas com ALAVANCS PRO 2.0"""
    
    accounts_config = [
        {
            'name': 'ALAVANCS_PRO_CONTA_1',
            'token': 'TOKEN_CONTA_1',
            'app_id': 1089,
            'server': 'frontend.derivws.com'
        },
        {
            'name': 'ALAVANCS_PRO_CONTA_2', 
            'token': 'TOKEN_CONTA_2',
            'app_id': 1089,
            'server': 'frontend.derivws.com'
        }
    ]
    
    return accounts_config

async def executar_multiplas_contas():
    """Executa ALAVANCS PRO 2.0 em múltiplas contas simultaneamente"""
    
    accounts = exemplo_configuracao_multiplas_contas()
    tasks = []
    
    for account in accounts:
        bot = AccumulatorScalpingBot(account)
        task = asyncio.create_task(bot.start_alavancs_pro())
        tasks.append(task)
        logger.info(f"🤖 Bot ALAVANCS PRO iniciado para conta: {account['name']}")
    
    # Aguardar todos os bots
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ALAVANCS PRO 2.0                          ║
    ║              Estratégia Reativa de Trading                   ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  🎯 CARACTERÍSTICAS PRINCIPAIS:                              ║
    ║  • Análise reativa de ticks em tempo real                   ║
    ║  • Buffer inteligente com filtros probabilísticos           ║
    ║  • Detecção de padrões consecutivos                         ║
    ║  • Sistema de gestão de risco avançado                      ║
    ║  • Pausa de segurança após perdas consecutivas              ║
    ║                                                              ║
    ║  🛡️ SISTEMA DE PROTEÇÃO:                                     ║
    ║  • Pausa automática após 3 perdas consecutivas              ║
    ║  • Análise de mercado durante pausa                         ║
    ║  • Retomada inteligente das operações                       ║
    ║                                                              ║
    ║  ⚠️  IMPORTANTE:                                             ║
    ║  • Configure seu token real antes de executar               ║
    ║  • Teste em conta demo primeiro                             ║
    ║  • Monitore os logs para acompanhar performance             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Executar demonstração
    asyncio.run(main())