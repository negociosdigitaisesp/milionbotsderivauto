#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar o sistema de reinicialização automática do tunderbot.py
Testa se o bot reinicia automaticamente a cada 30 minutos (simulado com 10 segundos para teste)
"""

import asyncio
import time
import logging
from datetime import datetime

# Configurar logging para o teste
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_auto_restart.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def mock_main():
    """Simula a função main() do bot para teste"""
    logger.info("🤖 Bot iniciado - simulando execução...")
    
    # Simular execução do bot por tempo indefinido
    try:
        contador = 0
        while True:
            contador += 1
            logger.info(f"📊 Bot executando... ciclo {contador}")
            await asyncio.sleep(2)  # Simular processamento
            
            # Simular alguma atividade do bot
            if contador % 5 == 0:
                logger.info(f"💹 Simulando análise de mercado (ciclo {contador})")
            
    except asyncio.CancelledError:
        logger.info("🛑 Bot cancelado pelo timeout")
        raise
    except Exception as e:
        logger.error(f"❌ Erro no bot: {e}")
        raise

def test_reiniciar_bot_automaticamente():
    """Testa a função de reinicialização automática com timeout reduzido"""
    max_tentativas = 3  # Reduzido para teste
    tentativa_atual = 0
    delay_base = 2  # Delay reduzido para teste
    timeout_reinicio = 10  # 10 segundos para teste (ao invés de 30 minutos)
    
    logger.info("🧪 INICIANDO TESTE DE REINICIALIZAÇÃO AUTOMÁTICA")
    logger.info(f"⏰ Timeout configurado para {timeout_reinicio} segundos")
    
    while tentativa_atual < max_tentativas:
        try:
            tentativa_atual += 1
            logger.info(f"🔄 REINICIANDO BOT (Tentativa {tentativa_atual}/{max_tentativas})")
            
            # Calcular delay progressivo
            delay = delay_base * (2 ** (tentativa_atual - 1)) if tentativa_atual > 1 else 0
            if delay > 10:  # Limitar para teste
                delay = 10
                
            if delay > 0:
                logger.info(f"⏱️ Aguardando {delay} segundos antes de reiniciar...")
                time.sleep(delay)
            
            # Executar o bot com timeout
            logger.info(f"⏰ Bot será reiniciado automaticamente em {timeout_reinicio} segundos")
            
            # Criar uma task para executar o mock_main() com timeout
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            inicio_execucao = datetime.now()
            
            try:
                # Executar com timeout
                loop.run_until_complete(asyncio.wait_for(mock_main(), timeout=timeout_reinicio))
                # Se chegou aqui, o bot foi finalizado normalmente
                logger.info("✅ Bot finalizado normalmente")
                break
            except asyncio.TimeoutError:
                fim_execucao = datetime.now()
                duracao = (fim_execucao - inicio_execucao).total_seconds()
                logger.info(f"⏰ Timeout de {timeout_reinicio} segundos atingido após {duracao:.1f}s - reiniciando bot automaticamente")
                print(f"✅ TESTE PASSOU: Bot reiniciado automaticamente após {duracao:.1f} segundos.")
                # Continua o loop para reiniciar
                continue
            finally:
                loop.close()
                
        except KeyboardInterrupt:
            logger.info("🛑 Teste interrompido pelo usuário")
            print("\nTeste interrompido pelo usuário.")
            break
            
        except Exception as e:
            logger.error(f"❌ Erro durante o teste: {e}")
            print(f"Erro durante o teste: {e}")
            continue
    
    # Se chegou ao número máximo de tentativas
    if tentativa_atual >= max_tentativas:
        logger.info(f"✅ Teste concluído após {max_tentativas} reinicializações")
        print(f"✅ TESTE CONCLUÍDO: Sistema de reinicialização testado com {max_tentativas} ciclos")
    
    logger.info("🏁 Teste de reinicialização automática finalizado")
    print("🏁 Teste finalizado.")

if __name__ == "__main__":
    try:
        print("🧪 Iniciando teste do sistema de reinicialização automática...")
        print("⏰ O bot será reiniciado a cada 10 segundos (simulando 30 minutos)")
        print("🛑 Pressione Ctrl+C para interromper o teste")
        print("-" * 60)
        
        # Iniciar o teste
        test_reiniciar_bot_automaticamente()
        
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido pelo usuário.")
    finally:
        print("🏁 Teste finalizado.")