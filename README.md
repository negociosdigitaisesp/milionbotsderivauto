# Sistema de Trading Automatizado

Sistema de trading automatizado para a plataforma Deriv com múltiplos bots operando em paralelo.

## 📋 Arquivos Essenciais

### Arquivo Principal
- `bot_trading_system.py` - Sistema principal de trading com 7 bots

### Configuração
- `.env` - Variáveis de ambiente (criar baseado no .env.example)
- `.env.example` - Exemplo de configuração
- `requirements.txt` - Dependências Python

### Sistema Modular
- `trading_system/` - Estrutura modular dos bots
  - `config/settings.py` - Configurações centralizadas
  - `utils/helpers.py` - Funções auxiliares
  - `bots/` - Bots individuais organizados por pasta

### Scripts de Teste
- `test_environment.py` - Teste completo do ambiente
- `test_stake_validation.py` - Validação de stake

### Instalação
- `install_vps.sh` - Script de instalação automática para VPS
- `VPS_QUICK_INSTALL.md` - Guia de instalação

## 🚀 Instalação Rápida

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
cp .env.example .env
# Editar .env com suas credenciais
```

### 3. Testar Ambiente
```bash
python test_environment.py
```

### 4. Executar Sistema
```bash
python bot_trading_system.py
```

## 🤖 Bots Incluídos

1. **BK_BOT_1.0** - Análise de dígitos com martingale adaptativo
2. **Factor50X** - Estratégia conservadora com stake fixo
3. **BotAI_2.0** - Compra contínua com martingale
4. **Bot_Apalancamiento** - Alternância entre DIGITUNDER/DIGITOVER
5. **Wolf_Bot_2.0** - Estratégia de mão fixa
6. **Sniper_Bot_Martingale** - Indicadores SMA com martingale
7. **QuantumBot_FixedStake** - Estratégia quantum com stake fixo

## 📊 Configurações Necessárias

### Deriv API
- `DERIV_APP_ID` - ID da aplicação Deriv
- `DERIV_API_TOKEN` - Token de acesso da API

### Supabase
- `SUPABASE_URL` - URL do projeto Supabase
- `SUPABASE_KEY` - Chave de acesso do Supabase

## 🔧 Características

- ✅ Execução paralela de múltiplos bots
- ✅ Sistema de reconexão automática
- ✅ Logging centralizado
- ✅ Tratamento robusto de erros
- ✅ Stake fixo de $1.00 para todos os bots
- ✅ Salvamento automático no Supabase

## 📈 Monitoramento

O sistema salva automaticamente todas as operações na tabela `operacoes` do Supabase com:
- Nome do bot
- Lucro/prejuízo
- Timestamp da operação

## ⚠️ Importante

- Todos os bots operam com stake fixo de $1.00
- Sistema otimizado para operação contínua
- Requer conexão estável com internet
- Configuração correta das APIs é essencial

## 📞 Suporte

Para dúvidas ou problemas, consulte:
- `VPS_QUICK_INSTALL.md` - Guia detalhado de instalação
- `SISTEMA_COMPLETO_RESUMO.md` - Resumo completo do sistema