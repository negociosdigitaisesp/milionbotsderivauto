# 🤖 Sistema de Trading Automatizado - Deriv Bots

Sistema Python para execução de múltiplos bots de trading em paralelo usando a API da Deriv e Supabase para armazenamento de dados.

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Conta na Deriv com API Token
- Projeto no Supabase configurado

## 🚀 Instalação

### 1. Clone o repositório e navegue até a pasta
```bash
cd bot-strategy-hub
```

### 2. Crie um ambiente virtual Python
```bash
python -m venv .venv
```

### 3. Ative o ambiente virtual
**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente
O arquivo `.env` já está configurado com suas credenciais. Verifique se contém:

```env
# Credenciais da Deriv API
DERIV_APP_ID="85515"
DERIV_API_TOKEN="W82xX7Z5EFxsWGI"

# Credenciais do Supabase
SUPABASE_URL="https://xwclmxjeombwabfdvyij.supabase.co"
SUPABASE_KEY="sua_chave_aqui"
```

## 🗄️ Configuração do Banco de Dados

### Criar tabela no Supabase
Execute este SQL no editor do Supabase:

```sql
CREATE TABLE operacoes (
    id SERIAL PRIMARY KEY,
    nome_bot VARCHAR(100) NOT NULL,
    lucro DECIMAL(10,2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar índices para melhor performance
CREATE INDEX idx_operacoes_nome_bot ON operacoes(nome_bot);
CREATE INDEX idx_operacoes_timestamp ON operacoes(timestamp);
```

## 🏃‍♂️ Execução

### Executar o sistema de trading
```bash
python bot_trading_system.py
```

### Parar o sistema
Pressione `Ctrl+C` para parar todos os bots com segurança.

## 📊 Estrutura do Sistema

### Bots Implementados
- **Bot 1**: RSI Sobrevenda - Estratégia baseada em indicador RSI
- **Bot 2**: Dígito Par - Estratégia baseada em análise de dígitos

### Bots Planejados (TODO)
- Bot 3: Martingale
- Bot 4: Fibonacci
- Bot 5: Bollinger Bands
- Bot 6: MACD Divergence
- Bot 7: Support/Resistance
- Bot 8: Volume Analysis
- Bot 9: Pattern Recognition
- Bot 10: Multi-timeframe

## 🔧 Personalização

### Adicionar novo bot
1. Crie uma função assíncrona seguindo o padrão:
```python
async def bot_novo(api):
    nome_bot = "Novo_Bot"
    while True:
        try:
            # Sua lógica aqui
            # salvar_operacao(nome_bot, lucro)
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        await asyncio.sleep(5)
```

2. Adicione a tarefa na função `main()`:
```python
tasks = [
    # ... outros bots
    asyncio.create_task(bot_novo(api)),
]
```

### Traduzir lógica XML para Python
Para cada arquivo .xml do DBot:
1. Identifique os indicadores usados
2. Traduza as condições de entrada
3. Configure os parâmetros do contrato
4. Implemente a lógica na função do bot

## 📈 Monitoramento

### Logs do sistema
- ✅ Operações bem-sucedidas
- ❌ Erros e exceções
- 🔄 Status de análise dos bots
- 📊 Conexões com APIs

### Dados no Supabase
Todas as operações são salvas na tabela `operacoes` com:
- Nome do bot
- Lucro/prejuízo
- Timestamp da operação

## ⚠️ Avisos Importantes

1. **Nunca compartilhe o arquivo `.env`**
2. **Teste com valores pequenos primeiro**
3. **Monitore os logs constantemente**
4. **Mantenha backups das configurações**
5. **Respeite os limites da API da Deriv**

## 🆘 Solução de Problemas

### Erro de conexão com Deriv
- Verifique se o `DERIV_API_TOKEN` está correto
- Confirme se o `DERIV_APP_ID` está ativo

### Erro de conexão com Supabase
- Verifique as credenciais no `.env`
- Confirme se a tabela `operacoes` existe

### Erro de dependências
```bash
pip install --upgrade -r requirements.txt
```

## 📞 Suporte

Para dúvidas sobre:
- **API da Deriv**: [Documentação oficial](https://developers.deriv.com/)
- **Supabase**: [Documentação oficial](https://supabase.com/docs)
- **Python asyncio**: [Documentação oficial](https://docs.python.org/3/library/asyncio.html)

---

**⚡ Sistema desenvolvido para trading automatizado profissional**