"""
EXEMPLO DE CONFIGURAÇÃO PARA MÚLTIPLAS CONTAS DERIV
===================================================

Este arquivo mostra como configurar múltiplas contas no tunderbotalavanca.py
para contornar a limitação de apenas 1 contrato acumulador por conta.

CONFIGURAÇÃO ATUAL:
==================
Sua conta principal já está configurada com:
- Token: 5iD3wgrYUz39kzS
- App ID: 105327

COMO ADICIONAR MAIS CONTAS:
==========================

1. No arquivo tunderbotalavanca.py, localize a seção ACCOUNTS (linha ~64)

2. Substitua os tokens placeholder pelas suas contas reais:

ACCOUNTS = [
    {
        "name": "Bot_Principal",
        "token": "5iD3wgrYUz39kzS",  # Sua conta atual
        "app_id": "105327"
    },
    {
        "name": "Bot_Secundario",
        "token": "SEU_SEGUNDO_TOKEN_AQUI",  # Adicione seu segundo token
        "app_id": "105327"  # Ou use app_id diferente se necessário
    },
    {
        "name": "Bot_Terciario", 
        "token": "SEU_TERCEIRO_TOKEN_AQUI",  # Adicione seu terceiro token
        "app_id": "105327"
    }
]

3. Para ativar múltiplas contas, modifique ACTIVE_ACCOUNTS:

# Para usar apenas a conta principal (configuração atual):
ACTIVE_ACCOUNTS = [ACCOUNTS[0]]

# Para usar 2 contas:
ACTIVE_ACCOUNTS = [ACCOUNTS[0], ACCOUNTS[1]]

# Para usar todas as 3 contas:
ACTIVE_ACCOUNTS = ACCOUNTS

COMO OBTER NOVOS TOKENS:
=======================

1. Acesse https://app.deriv.com/account/api-token
2. Crie um novo token com as permissões:
   - Read
   - Trade
   - Trading information
   - Payments
3. Copie o token gerado
4. Adicione na configuração ACCOUNTS

VANTAGENS DO SISTEMA MULTI-CONTA:
================================

✅ Múltiplos contratos acumuladores simultâneos
✅ Distribuição automática de operações entre contas
✅ Logs separados por conta para melhor rastreamento
✅ Estatísticas combinadas de todas as contas
✅ Sistema de failover automático
✅ Gerenciamento centralizado via um único script

EXEMPLO DE EXECUÇÃO:
===================

Quando você executar o bot com múltiplas contas ativas, verá logs como:

🏦 MultiAccountManager inicializado com 3 contas
🤖 Inicializando bot para conta: Bot_Principal
✅ Bot inicializado para conta Bot_Principal
🤖 Inicializando bot para conta: Bot_Secundario
✅ Bot inicializado para conta Bot_Secundario
🎯 Total de bots ativos: 2
🚀 Iniciando 2 bots simultaneamente...
📊 Distribuindo operação para conta: Bot_Principal
📊 Distribuindo operação para conta: Bot_Secundario

IMPORTANTE:
===========

- Cada conta deve ter saldo suficiente para as operações
- Monitore os logs para verificar se todas as contas estão funcionando
- O sistema distribui operações em round-robin entre as contas ativas
- Você pode parar e reiniciar o bot a qualquer momento

"""

# Teste rápido da configuração atual
if __name__ == "__main__":
    try:
        from tunderbotalavanca import ACCOUNTS, ACTIVE_ACCOUNTS
        
        print("🔍 CONFIGURAÇÃO ATUAL:")
        print(f"📊 Total de contas configuradas: {len(ACCOUNTS)}")
        print(f"🎯 Contas ativas: {len(ACTIVE_ACCOUNTS)}")
        
        print("\n📋 DETALHES DAS CONTAS:")
        for i, account in enumerate(ACCOUNTS):
            status = "✅ ATIVA" if account in ACTIVE_ACCOUNTS else "⏸️ INATIVA"
            token_preview = account['token'][:10] + "..." if not account['token'].startswith('SEU_TOKEN_') else "❌ TOKEN PLACEHOLDER"
            print(f"  {i+1}. {account['name']}: {status}")
            print(f"     Token: {token_preview}")
            print(f"     App ID: {account['app_id']}")
        
        print(f"\n🚀 Para executar o bot: python tunderbotalavanca.py")
        
    except ImportError as e:
        print(f"❌ Erro ao importar configurações: {e}")
        print("Certifique-se de que o arquivo tunderbotalavanca.py está no mesmo diretório")