# 🤖 NOVA GERAÇÃO DE ROBÔS - SISTEMA DE ORQUESTRAÇÃO

## 📋 Visão Geral

Este sistema implementa uma nova geração de robôs de trading que coexistem com os robôs existentes na VPS. O sistema é composto por:

- **orchestrator.py**: Gerenciador principal que controla todos os robôs
- **bot_instance.py**: Script genérico que executa a lógica de trading
- **Tabelas Supabase**: Central de controle e logs unificados

## 🗄️ PASSO 1: Configuração do Supabase

### 1.1 Executar Script SQL

Execute o arquivo `setup_supabase_tables.sql` no seu painel do Supabase:

```sql
-- Copie e cole todo o conteúdo do arquivo setup_supabase_tables.sql
-- no SQL Editor do Supabase e execute
```

### 1.2 Verificar Tabelas Criadas

Após executar o SQL, verifique se as seguintes tabelas foram criadas:

- ✅ `bot_configurations` - Controle e configuração dos robôs
- ✅ `bot_operation_logs` - Logs unificados de todas as operações

### 1.3 Verificar Registros Iniciais

Confirme que os robôs foram registrados:

```sql
SELECT * FROM bot_configurations;
```

Deve mostrar:
- ID 1: Accumulator
- ID 2: Speed Bot

## 🚀 PASSO 2: Preparação do Ambiente

### 2.1 Verificar Variáveis de Ambiente

Certifique-se de que o arquivo `.env.accumulator` contém:

```env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_ANON_KEY=sua_chave_anonima
DERIV_API_TOKEN=seu_token_da_deriv
```

### 2.2 Instalar Dependências (se necessário)

```bash
pip install supabase websockets aiohttp python-dotenv
```

## 🧪 PASSO 3: Testes do Sistema

### 3.1 Teste Individual do Bot Instance

Teste um bot individual primeiro:

```bash
# Testar o Accumulator (ID 1)
python bot_instance.py --bot_id 1

# Testar o Speed Bot (ID 2)
python bot_instance.py --bot_id 2
```

**Verificações esperadas:**
- ✅ Conexão com Supabase estabelecida
- ✅ Configuração do bot carregada
- ✅ Conexão WebSocket com Deriv estabelecida
- ✅ Heartbeats sendo enviados a cada 60 segundos
- ✅ Logs sendo registrados na tabela `bot_operation_logs`

### 3.2 Teste do Orchestrator

Após confirmar que os bots individuais funcionam:

```bash
python orchestrator.py
```

**Verificações esperadas:**
- ✅ Sincronização com banco de dados a cada 60 segundos
- ✅ Detecção automática dos robôs ativos
- ✅ Inicialização dos processos dos robôs
- ✅ Monitoramento de heartbeats
- ✅ Reinicialização automática de robôs "zumbis"

## 📊 PASSO 4: Monitoramento

### 4.1 Verificar Status dos Robôs

```sql
SELECT 
    bot_name,
    status,
    is_active,
    last_heartbeat,
    total_operations,
    total_profit
FROM bot_configurations;
```

### 4.2 Verificar Logs de Operações

```sql
SELECT 
    bot_name,
    operation_type,
    status,
    stake,
    profit_loss,
    created_at
FROM bot_operation_logs
ORDER BY created_at DESC
LIMIT 20;
```

### 4.3 Arquivos de Log

Verifique os arquivos de log criados:
- `orchestrator.log` - Logs do orquestrador
- `bot_instance_1.log` - Logs do Accumulator
- `bot_instance_2.log` - Logs do Speed Bot

## 🔧 PASSO 5: Controle dos Robôs

### 5.1 Parar um Robô Específico

```sql
UPDATE bot_configurations 
SET is_active = false 
WHERE bot_name = 'Accumulator';
```

### 5.2 Reativar um Robô

```sql
UPDATE bot_configurations 
SET is_active = true 
WHERE bot_name = 'Accumulator';
```

### 5.3 Parar Todos os Robôs

```sql
UPDATE bot_configurations 
SET is_active = false;
```

## 🚨 PASSO 6: Transição na VPS

### 6.1 Parar o Sistema Antigo

```bash
# Parar apenas o accumulator_standalone.py
# (manter outros robôs rodando)
pkill -f accumulator_standalone.py
```

### 6.2 Iniciar o Novo Sistema

```bash
# Iniciar o orquestrador
nohup python orchestrator.py > orchestrator_output.log 2>&1 &
```

### 6.3 Verificar Funcionamento

```bash
# Verificar se o processo está rodando
ps aux | grep orchestrator

# Verificar logs em tempo real
tail -f orchestrator.log
```

## 📈 PASSO 7: Adicionando Novos Robôs

Para adicionar um novo robô ao sistema:

```sql
INSERT INTO bot_configurations 
(bot_name, param_take_profit, param_stake_inicial, param_growth_rate, param_max_operations)
VALUES 
('Novo Bot', 15.0, 100.0, 3.0, 15);
```

O orquestrador detectará automaticamente o novo robô na próxima sincronização.

## 🛠️ Solução de Problemas

### Problema: Bot não inicia
- Verificar variáveis de ambiente
- Verificar conexão com Supabase
- Verificar token da Deriv API

### Problema: Heartbeat não funciona
- Verificar permissões da tabela no Supabase
- Verificar conectividade de rede

### Problema: Operações não são registradas
- Verificar estrutura da tabela `bot_operation_logs`
- Verificar permissões de escrita no Supabase

## 📞 Suporte

Em caso de problemas:
1. Verificar logs dos arquivos `.log`
2. Verificar status no Supabase
3. Testar conexões individualmente

---

**✅ Sistema pronto para produção!**

O novo sistema de orquestração está configurado e pronto para gerenciar os robôs Accumulator e Speed Bot de forma isolada e controlada.