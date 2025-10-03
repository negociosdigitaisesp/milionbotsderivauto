#!/usr/bin/env python3
"""
EXEMPLO: Como configurar múltiplas contas no tunderbotalavanca.py

Este arquivo mostra como modificar a configuração ACCOUNTS no arquivo principal
para adicionar mais contas Deriv e executar múltiplos bots simultaneamente.
"""

# ============================================================================
# EXEMPLO DE CONFIGURAÇÃO DE MÚLTIPLAS CONTAS
# ============================================================================

# Configuração atual no tunderbotalavanca.py:
ACCOUNTS_EXEMPLO = [
    {
        "name": "Bot_Principal",
        "token": "5iD3wgrYUz39kzS",  # Token fornecido pelo usuário
        "app_id": "105327"
    },
    {
        "name": "Bot_Secundario",
        "token": "SEU_TOKEN_2_AQUI",  # Substituir pelo token real
        "app_id": "105327"
    },
    {
        "name": "Bot_Terciario", 
        "token": "SEU_TOKEN_3_AQUI",  # Substituir pelo token real
        "app_id": "105327"
    }
]

# ============================================================================
# COMO ADICIONAR MAIS CONTAS
# ============================================================================

# Para adicionar mais contas, edite a lista ACCOUNTS no arquivo tunderbotalavanca.py:

ACCOUNTS_EXPANDIDO = [
    {
        "name": "Bot_Principal",
        "token": "5iD3wgrYUz39kzS",
        "app_id": "105327"
    },
    {
        "name": "Bot_Conta_2",
        "token": "TOKEN_DA_CONTA_2",  # Substituir pelo token real da conta 2
        "app_id": "105327"
    },
    {
        "name": "Bot_Conta_3",
        "token": "TOKEN_DA_CONTA_3",  # Substituir pelo token real da conta 3
        "app_id": "105327"
    },
    {
        "name": "Bot_Conta_4",
        "token": "TOKEN_DA_CONTA_4",  # Substituir pelo token real da conta 4
        "app_id": "105327"
    },
    {
        "name": "Bot_Conta_5",
        "token": "TOKEN_DA_CONTA_5",  # Substituir pelo token real da conta 5
        "app_id": "105327"
    }
]

# ============================================================================
# CONFIGURAÇÃO DE CONTAS ATIVAS
# ============================================================================

# Para controlar quais contas estão ativas, modifique ACTIVE_ACCOUNTS:

# Usar apenas a primeira conta (padrão atual):
ACTIVE_ACCOUNTS_SINGLE = [ACCOUNTS_EXEMPLO[0]]

# Usar todas as contas com tokens válidos:
ACTIVE_ACCOUNTS_ALL = ACCOUNTS_EXPANDIDO

# Usar contas específicas:
ACTIVE_ACCOUNTS_CUSTOM = [
    ACCOUNTS_EXPANDIDO[0],  # Bot_Principal
    ACCOUNTS_EXPANDIDO[1],  # Bot_Conta_2
    ACCOUNTS_EXPANDIDO[3]   # Bot_Conta_4
]

# ============================================================================
# INSTRUÇÕES DE USO
# ============================================================================

print("""
INSTRUÇÕES PARA CONFIGURAR MÚLTIPLAS CONTAS:

1. Obtenha tokens de API para cada conta Deriv:
   - Acesse https://app.deriv.com/account/api-token
   - Crie um novo token para cada conta
   - Copie o token gerado

2. Edite o arquivo tunderbotalavanca.py:
   - Localize a seção "CONFIGURAÇÃO DE MÚLTIPLAS CONTAS"
   - Substitua "SEU_TOKEN_X_AQUI" pelos tokens reais
   - Adicione mais contas se necessário

3. Configure as contas ativas:
   - Modifique a variável ACTIVE_ACCOUNTS
   - Inclua apenas as contas que deseja usar

4. Execute o bot:
   - python tunderbotalavanca.py
   - O sistema iniciará um bot para cada conta ativa
   - Cada bot operará independentemente

RECURSOS DO SISTEMA MULTI-CONTA:

✅ Cada conta executa contratos ACCU independentemente
✅ Logs separados por conta no Supabase
✅ Monitoramento individual de lucros/perdas
✅ Recuperação automática de conexão por conta
✅ Distribuição round-robin de operações
✅ Estatísticas combinadas de todas as contas

LIMITAÇÕES:

⚠️ Cada conta Deriv permite apenas 1 contrato ACCU ativo
⚠️ Tokens devem ter permissões de trading
⚠️ Recomendado máximo 5 contas simultâneas
⚠️ Monitorar limites de API da Deriv

EXEMPLO DE SAÍDA:

[INICIO] Iniciando Accumulator Scalping Bot - Modo Multi-Conta
[CONTAS] Contas configuradas:
   • Bot_Principal: ✅ ATIVA
   • Bot_Conta_2: ✅ ATIVA
   • Bot_Conta_3: ⚠️ TOKEN PLACEHOLDER
🏦 MultiAccountManager inicializado com 2 contas
🤖 Inicializando bot para conta: Bot_Principal
🤖 Inicializando bot para conta: Bot_Conta_2
🎯 Total de bots ativos: 2
🚀 Iniciando 2 bots simultaneamente...
""")