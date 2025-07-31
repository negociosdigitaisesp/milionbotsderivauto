# Sistema de Trading Automatizado

Sistema de trading automatizado para a plataforma Deriv com múltiplos bots operando em paralelo.

## 📋 Arquivos Essenciais

### Arquivo Principal
- `bot_trading_system.py` - Sistema principal de trading com 7 bots
- `supervisor.py` - **NOVO!** Script supervisor para gerenciamento automático

### Configuração
- `.env` - Variáveis de ambiente (criar baseado no .env.example)
- `.env.example` - Exemplo de configuração
- `requirements.txt` - Dependências Python

### Sistema Modular
- `trading_system/` - Estrutura modular dos bots
  - `config/settings.py` - Configurações centralizadas
  - `utils/helpers.py` - Funções auxiliares com tratamento de erros WebSocket
  - `bots/` - Bots individuais organizados por pasta

### Scripts de Teste
- `test_environment.py` - Teste completo do ambiente
- `test_stake_validation.py` - Validação de stake

### Scripts de Execução
- `start_supervisor.sh` - **NOVO!** Iniciar supervisor (Linux/Mac)
- `start_supervisor.bat` - **NOVO!** Iniciar supervisor (Windows)

### Instalação
- `install_vps.sh` - Script de instalação automática para VPS
- `VPS_QUICK_INSTALL.md` - Guia de instalação

### Documentação
- `SUPERVISOR_GUIDE.md` - **NOVO!** Guia completo do supervisor

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

#### Opção A: Execução Direta
```bash
python bot_trading_system.py
```

#### Opção B: Execução com Supervisor (RECOMENDADO)
```bash
# Linux/Mac
./start_supervisor.sh

# Windows
start_supervisor.bat

# Ou diretamente
python supervisor.py
```

## 🛡️ Sistema Supervisor (NOVO!)

O **supervisor.py** é um sistema de gerenciamento que:

- 🔄 **Reinicia automaticamente** o sistema a cada 1 hora
- 🛡️ **Monitora continuamente** o bot_trading_system.py
- 🔧 **Recupera automaticamente** de falhas de conexão
- 📝 **Gera logs detalhados** com timestamps
- 🚫 **Encerramento gracioso** com Ctrl+C

### Benefícios do Supervisor:
- **Estabilidade**: Limpa vazamentos de memória periodicamente
- **Disponibilidade**: Operação 24/7 sem intervenção manual
- **Resiliência**: Recuperação automática de falhas WebSocket
- **Monitoramento**: Logs detalhados para análise

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
- ✅ **Sistema supervisor para estabilidade máxima**
- ✅ **Tratamento robusto de erros WebSocket**
- ✅ **Reconexão automática com espera progressiva**
- ✅ Logging centralizado
- ✅ Stake fixo de $1.00 para todos os bots
- ✅ Salvamento automático no Supabase

## 📈 Monitoramento

O sistema salva automaticamente todas as operações na tabela `operacoes` do Supabase com:
- Nome do bot
- Lucro/prejuízo
- Timestamp da operação

### Logs do Supervisor
```bash
# Monitorar logs em tempo real
tail -f logs/supervisor.log

# Windows
powershell Get-Content logs\supervisor.log -Wait
```

## ⚠️ Importante

- **USE O SUPERVISOR** para operação em produção
- Todos os bots operam com stake fixo de $1.00
- Sistema otimizado para operação contínua 24/7
- Requer conexão estável com internet
- Configuração correta das APIs é essencial

## 📞 Suporte

Para dúvidas ou problemas, consulte:
- `SUPERVISOR_GUIDE.md` - **Guia completo do supervisor**
- `VPS_QUICK_INSTALL.md` - Guia detalhado de instalação
- `SISTEMA_COMPLETO_RESUMO.md` - Resumo completo do sistema