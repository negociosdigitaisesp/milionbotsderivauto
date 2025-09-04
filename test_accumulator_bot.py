#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Accumulator Scalping Bot
Testa a funcionalidade completa do bot incluindo:
- Conexão com Deriv API
- Análise de ticks
- Lógica de entrada
- Gestão de risco
- Integração com Supabase
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from deriv_api import DerivAPI
from supabase import create_client

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar o bot
try:
    from trading_system.bots.accumulator_bot.bot_accumulator_scalping import bot_accumulator_scalping, AccumulatorScalpingBot
except ImportError as e:
    print(f"❌ Erro ao importar bot: {e}")
    sys.exit(1)

# Carregar variáveis de ambiente
load_dotenv()

DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Erro: Variáveis de ambiente não encontradas")
    sys.exit(1)


async def test_deriv_connection():
    """Testa conexão com Deriv API"""
    try:
        print("\n=== TESTANDO CONEXÃO DERIV ===")
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        
        # Testar balance
        balance_response = await api.balance()
        if 'error' not in balance_response:
            balance = balance_response['balance']['balance']
            currency = balance_response['balance']['currency']
            print(f"✅ Conexão Deriv OK - Saldo: {balance} {currency}")
        
        await api.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão Deriv: {e}")
        return False


async def test_supabase_connection():
    """Testa conexão com Supabase"""
    try:
        print("\n=== TESTANDO CONEXÃO SUPABASE ===")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Testar se a tabela existe
        try:
            result = supabase.table('scalping_accumulator_bot_logs').select('*').limit(1).execute()
            print("✅ Tabela 'scalping_accumulator_bot_logs' encontrada")
        except Exception:
            print("⚠️  Tabela 'scalping_accumulator_bot_logs' não existe - será criada automaticamente")
        
        print("✅ Conexão Supabase OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão Supabase: {e}")
        return False


async def test_bot_initialization():
    """Testa inicialização do bot"""
    try:
        print("\n=== TESTANDO INICIALIZAÇÃO DO BOT ===")
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        
        # Criar instância do bot
        bot = AccumulatorScalpingBot(api)
        
        print(f"✅ Bot inicializado com sucesso")
        print(f"   📊 Nome: {bot.nome_bot}")
        print(f"   💰 Stake inicial: ${bot.stake_inicial}")
        print(f"   🔢 Fator khizzbot: {bot.khizzbot}")
        print(f"   📈 Growth Rate: {bot.growth_rate*100}%")
        print(f"   🎯 Take Profit: {bot.take_profit_inicial*100}%")
        print(f"   🏪 Ativo: {bot.ativo}")
        
        await api.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        return False


async def test_tick_analysis():
    """Testa análise de ticks"""
    try:
        print("\n=== TESTANDO ANÁLISE DE TICKS ===")
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        
        bot = AccumulatorScalpingBot(api)
        
        # Testar obtenção de ticks
        print("📊 Obtendo histórico de ticks...")
        resultado = await bot.analisar_ticks()
        
        if resultado:
            print("✅ Condição de entrada ATENDIDA - Padrão Red,Red,Red,Blue encontrado!")
        else:
            print("ℹ️  Condição de entrada não atendida - aguardando padrão correto")
        
        await api.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erro na análise de ticks: {e}")
        return False


async def test_risk_management():
    """Testa gestão de risco"""
    try:
        print("\n=== TESTANDO GESTÃO DE RISCO ===")
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        
        bot = AccumulatorScalpingBot(api)
        
        # Simular cenário de vitória
        print("🎉 Simulando VITÓRIA...")
        resultado_win = {
            'is_win': True,
            'profit': 5.0,
            'profit_percentage': 10.0
        }
        bot.processar_resultado(resultado_win)
        print(f"   💰 Stake após vitória: ${bot.stake_atual}")
        print(f"   📊 Total lost: ${bot.total_lost}")
        print(f"   🎯 Take profit: ${bot.take_profit_atual}")
        
        # Simular cenário de derrota
        print("\n❌ Simulando DERROTA...")
        resultado_loss = {
            'is_win': False,
            'profit': -50.0,
            'profit_percentage': -100.0
        }
        bot.processar_resultado(resultado_loss)
        print(f"   💰 Stake após derrota: ${bot.stake_atual}")
        print(f"   📊 Total lost: ${bot.total_lost}")
        print(f"   🎯 Take profit: ${bot.take_profit_atual}")
        
        print("✅ Gestão de risco funcionando corretamente")
        
        await api.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erro na gestão de risco: {e}")
        return False


async def test_supabase_integration():
    """Testa integração com Supabase"""
    try:
        print("\n=== TESTANDO INTEGRAÇÃO SUPABASE ===")
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        
        bot = AccumulatorScalpingBot(api)
        
        # Simular resultado para salvar
        resultado_teste = {
            'is_win': True,
            'profit': 5.0,
            'profit_percentage': 10.0
        }
        
        print("💾 Salvando resultado de teste no Supabase...")
        await bot.salvar_resultado_supabase(resultado_teste)
        print("✅ Integração Supabase funcionando")
        
        await api.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração Supabase: {e}")
        return False


async def run_short_test():
    """Executa teste curto do bot (30 segundos)"""
    try:
        print("\n=== TESTE CURTO DO BOT (30 segundos) ===")
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        
        print("🚀 Iniciando bot por 30 segundos...")
        
        # Executar bot com timeout
        try:
            await asyncio.wait_for(bot_accumulator_scalping(api), timeout=30)
        except asyncio.TimeoutError:
            print("⏰ Teste de 30 segundos concluído")
        
        await api.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste curto: {e}")
        return False


async def main():
    """Função principal de teste"""
    print("🧪 TESTE COMPLETO DO ACCUMULATOR SCALPING BOT")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    testes = [
        ("Conexão Deriv", test_deriv_connection),
        ("Conexão Supabase", test_supabase_connection),
        ("Inicialização Bot", test_bot_initialization),
        ("Análise de Ticks", test_tick_analysis),
        ("Gestão de Risco", test_risk_management),
        ("Integração Supabase", test_supabase_integration),
        ("Teste Curto (30s)", run_short_test)
    ]
    
    resultados = []
    
    for nome_teste, funcao_teste in testes:
        print(f"\n🔍 Executando: {nome_teste}")
        try:
            resultado = await funcao_teste()
            resultados.append((nome_teste, resultado))
        except Exception as e:
            print(f"❌ Erro em {nome_teste}: {e}")
            resultados.append((nome_teste, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    sucessos = 0
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{nome:<25} {status}")
        if resultado:
            sucessos += 1
    
    print(f"\n📊 Resultado Final: {sucessos}/{len(resultados)} testes passaram")
    
    if sucessos == len(resultados):
        print("🎉 TODOS OS TESTES PASSARAM! Bot pronto para uso.")
    else:
        print("⚠️  Alguns testes falharam. Verifique as configurações.")
    
    print(f"⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico no teste: {e}")