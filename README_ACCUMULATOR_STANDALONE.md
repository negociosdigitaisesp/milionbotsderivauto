# Accumulator Bot - Modo Standalone

## 📋 Descrição

Este é um sistema dedicado para executar **apenas o Accumulator_Scalping_Bot** de forma isolada, sem interferência de outros bots. Ideal para VPS dedicada onde você quer que o bot analise o mercado 24/7.

## 🎯 Características

- ✅ **Execução isolada** - Sem conflitos com outros bots
- ✅ **Auto-recuperação** - Reconecta automaticamente em caso de erro
- ✅ **Rate limiting** - Proteção contra limites da API
- ✅ **Monitoramento contínuo** - Analisa o mercado 24/7
- ✅ **Logs detalhados** - Acompanhe todas as ações do bot

## ⚙️ Configuração

### 1. Configurar Token da API

**Opção A: Arquivo .env (Recomendado)**
```bash
# Copie o arquivo de exemplo
cp .env.accumulator .env

# Edite e configure seu token
nano .env
```

**Opção B: Variável de ambiente**
```bash
export DERIV_TOKEN="seu_token_aqui"
```

### 2. Obter Token da Deriv

1. Acesse: https://app.deriv.com/account/api-token
2. Crie um novo token com as permissões:
   - ✅ Read
   - ✅ Trade
   - ✅ Trading information
3. Copie o token gerado

## 🚀 Execução

### Windows
```cmd
# Executar diretamente
python accumulator_standalone.py

# Ou usar o script batch
start_accumulator.bat
```

### Linux/VPS
```bash
# Executar diretamente
python3 accumulator_standalone.py

# Ou usar o script shell
./start_accumulator.sh

# Para execução em background (daemon)
nohup ./start_accumulator.sh > accumulator.log 2>&1 &
```

## 📊 Configuração do Bot

### Parâmetros Padrão
- **💰 Stake inicial**: $50.0
- **📈 Growth Rate**: 2.0%
- **🎯 Take Profit**: 10.0%
- **🏪 Ativo**: R_75 (Volatility 75 Index)
- **🎲 Estratégia**: Padrão ['Red', 'Red', 'Red', 'Blue']
- **⏱️ Tipo**: Contratos Accumulator

### Personalizar Configurações

Edite o arquivo `.env` para personalizar:
```env
DERIV_TOKEN=seu_token_aqui
ACCUMULATOR_STAKE=100.0
ACCUMULATOR_GROWTH_RATE=1.5
ACCUMULATOR_TAKE_PROFIT=15.0
```

## 🔍 Monitoramento

### Logs em Tempo Real
```bash
# Ver logs do bot em execução
tail -f accumulator.log

# Filtrar apenas trades
grep "VITÓRIA\|DERROTA" accumulator.log

# Ver padrões analisados
grep "Padrão atual" accumulator.log
```

### Exemplo de Logs
```
🔍 Accumulator_Scalping_Bot: Ticks: ['84766.22', '84812.55', '84819.41', '84796.85', '84784.05']
🔍 Accumulator_Scalping_Bot: Padrão atual: ['Blue', 'Blue', 'Red', 'Red'] | Esperado: ['Red', 'Red', 'Red', 'Blue']
⏳ Accumulator_Scalping_Bot: Aguardando padrão correto...
```

## 🛠️ Solução de Problemas

### Erro: "Token da API não encontrado"
```bash
# Verificar se o token está configurado
echo $DERIV_TOKEN

# Ou verificar arquivo .env
cat .env
```

### Erro: "Falha na conexão"
- Verifique sua conexão com a internet
- Confirme se o token está válido
- Verifique se não há firewall bloqueando

### Bot não executa trades
- **Normal**: O bot aguarda o padrão específico ['Red', 'Red', 'Red', 'Blue']
- **Solução**: Seja paciente, o padrão pode demorar para aparecer
- **Verificação**: Acompanhe os logs para ver os padrões analisados

## 🔄 Execução Contínua (VPS)

### Usando systemd (Linux)

1. Criar arquivo de serviço:
```bash
sudo nano /etc/systemd/system/accumulator-bot.service
```

2. Conteúdo do arquivo:
```ini
[Unit]
Description=Accumulator Scalping Bot
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/caminho/para/milionbotsderivauto
ExecStart=/usr/bin/python3 accumulator_standalone.py
Restart=always
RestartSec=10
Environment=DERIV_TOKEN=seu_token_aqui

[Install]
WantedBy=multi-user.target
```

3. Ativar serviço:
```bash
sudo systemctl enable accumulator-bot
sudo systemctl start accumulator-bot
sudo systemctl status accumulator-bot
```

### Usando screen (Alternativa)
```bash
# Criar sessão screen
screen -S accumulator

# Executar bot
./start_accumulator.sh

# Desanexar (Ctrl+A, D)
# Reanexar: screen -r accumulator
```

## 📈 Vantagens do Modo Standalone

1. **🎯 Foco total**: Bot dedicado apenas ao Accumulator
2. **⚡ Performance**: Sem competição por recursos
3. **🔒 Isolamento**: Erros de outros bots não afetam
4. **📊 Monitoramento**: Logs específicos e claros
5. **🔄 Estabilidade**: Auto-recuperação dedicada
6. **💰 Eficiência**: Rate limiting otimizado

## ⚠️ Considerações Importantes

- **Paciência**: O bot aguarda condições específicas de entrada
- **Capital**: Mantenha saldo suficiente na conta Deriv
- **Monitoramento**: Acompanhe regularmente os logs
- **Backup**: Mantenha backup das configurações
- **Teste**: Teste primeiro em conta demo

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs detalhados
2. Confirme as configurações
3. Teste a conectividade
4. Verifique o saldo da conta

---

**🎯 Objetivo**: Maximizar a eficiência do Accumulator bot com execução dedicada e isolada.