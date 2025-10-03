# 📊 BANCO DE DADOS - TUNDER BOT

## 📋 Resumo Executivo

Este documento detalha todas as operações de banco de dados utilizadas pelo **Tunder Bot** (`tunderbot.py`), incluindo conexões, tabelas, inserções e estruturas de dados enviadas para o Supabase.

---

## 🔗 CONFIGURAÇÃO DE CONEXÃO

### Credenciais e Inicialização
```python
from supabase import create_client, Client

# Credenciais carregadas do arquivo .env
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Inicialização do cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### Variáveis de Ambiente Necessárias
- `SUPABASE_URL`: URL do projeto Supabase
- `SUPABASE_KEY`: Chave de API do Supabase (anon key)

---

## 📊 OPERAÇÕES DE BANCO DE DADOS

### 1. 📝 LOG DE OPERAÇÕES - Função `log_to_supabase()`

**Localização:** Linha 2136-2154

**Função:** Registra resultados de operações de trading no banco de dados

```python
async def log_to_supabase(self, operation_result: str, profit_percentage: float, stake_value: float):
    """Envia log de operação para Supabase"""
    try:
        supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        # Adicionar timestamp fields obrigatórios
        current_time = datetime.now().isoformat()
        
        data = {
            'operation_result': operation_result,
            'profit_percentage': profit_percentage,
            'stake_value': stake_value,
            'created_at': current_time
        }
        
        result = supabase.table('tunder_bot_logs').insert(data).execute()
        logger.info(f"📊 Log enviado para Supabase: {operation_result} - {profit_percentage:.2f}% - ${stake_value}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar log para Supabase: {e}")
```

#### 📋 Estrutura de Dados Enviada

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `operation_result` | string | Resultado da operação (WIN/LOSS) |
| `profit_percentage` | float | Percentual de lucro/prejuízo |
| `stake_value` | float | Valor do stake utilizado |
| `created_at` | timestamp | Data e hora da operação |

#### 🎯 Tabela de Destino
- **Nome:** `tunder_bot_logs`
- **Operação:** INSERT
- **Frequência:** A cada operação de trading finalizada

---

## 📈 FLUXO DE DADOS

### 1. 🔄 Quando os Dados São Enviados

Os dados são enviados para o Supabase nos seguintes momentos:

1. **Após Finalização de Contrato:** Quando um contrato ACCU é finalizado (WIN ou LOSS)
2. **Resultado de Monitoramento:** Após o monitoramento completo do contrato
3. **Cálculo de Lucro/Prejuízo:** Quando o resultado financeiro é calculado

### 2. 📊 Exemplo de Dados Enviados

```json
{
  "operation_result": "WIN",
  "profit_percentage": 45.0,
  "stake_value": 5.0,
  "created_at": "2024-01-15T14:30:25.123456"
}
```

```json
{
  "operation_result": "LOSS",
  "profit_percentage": -100.0,
  "stake_value": 5.0,
  "created_at": "2024-01-15T14:35:10.789012"
}
```

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### 1. 🛡️ Tratamento de Erros

- **Try/Catch:** Todas as operações são envolvidas em blocos try/catch
- **Logging:** Erros são registrados no sistema de logs
- **Continuidade:** Falhas no banco não interrompem o bot

### 2. ⚡ Performance

- **Conexão por Operação:** Nova conexão criada a cada envio
- **Assíncrono:** Operações não bloqueiam o fluxo principal
- **Timeout:** Sem timeout específico configurado

### 3. 🔒 Segurança

- **Variáveis de Ambiente:** Credenciais armazenadas em .env
- **Validação:** Dados validados antes do envio
- **Logs Seguros:** Não exposição de credenciais nos logs

---

## 📋 ESTRUTURA DA TABELA SUPABASE

### Tabela: `tunder_bot_logs`

```sql
CREATE TABLE public.tunder_bot_logs (
    id BIGSERIAL PRIMARY KEY,
    operation_result TEXT NOT NULL,
    profit_percentage DECIMAL(10,2) NOT NULL,
    stake_value DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 📊 Índices Recomendados

```sql
-- Índice para consultas por data
CREATE INDEX idx_tunder_bot_logs_created_at ON public.tunder_bot_logs (created_at DESC);

-- Índice para consultas por resultado
CREATE INDEX idx_tunder_bot_logs_result ON public.tunder_bot_logs (operation_result);

-- Índice composto para análises
CREATE INDEX idx_tunder_bot_logs_result_date ON public.tunder_bot_logs (operation_result, created_at DESC);
```

---

## 📈 ESTATÍSTICAS E ANÁLISES

### 1. 📊 Dados Coletados

- **Volume de Operações:** Quantidade total de trades
- **Taxa de Sucesso:** Percentual de operações WIN vs LOSS
- **Valores de Stake:** Histórico de valores apostados
- **Rentabilidade:** Análise de lucros e prejuízos
- **Timestamps:** Horários precisos das operações

### 2. 🎯 Possíveis Consultas

```sql
-- Total de operações por resultado
SELECT operation_result, COUNT(*) as total
FROM tunder_bot_logs
GROUP BY operation_result;

-- Lucro total por dia
SELECT DATE(created_at) as data, 
       SUM(stake_value * profit_percentage / 100) as lucro_total
FROM tunder_bot_logs
GROUP BY DATE(created_at)
ORDER BY data DESC;

-- Taxa de sucesso
SELECT 
    COUNT(CASE WHEN operation_result = 'WIN' THEN 1 END) * 100.0 / COUNT(*) as taxa_sucesso
FROM tunder_bot_logs;
```

---

## ⚠️ CONSIDERAÇÕES IMPORTANTES

### 1. 🔄 Dependências

- **Conexão Internet:** Necessária para envio dos dados
- **Credenciais Válidas:** SUPABASE_URL e SUPABASE_KEY devem estar corretas
- **Tabela Existente:** A tabela `tunder_bot_logs` deve existir no Supabase

### 2. 🚨 Pontos de Atenção

- **Falhas Silenciosas:** Erros no banco não param o bot
- **Conexões Múltiplas:** Nova conexão a cada operação (pode ser otimizado)
- **Sem Retry:** Não há tentativas automáticas em caso de falha

### 3. 🔧 Melhorias Sugeridas

- **Pool de Conexões:** Reutilizar conexões para melhor performance
- **Retry Logic:** Implementar tentativas automáticas
- **Batch Insert:** Agrupar múltiplas operações
- **Validação de Schema:** Verificar estrutura da tabela

---

## 📝 LOGS E MONITORAMENTO

### 1. 📊 Logs de Sucesso

```
📊 Log enviado para Supabase: WIN - 45.00% - $5.0
📊 Log enviado para Supabase: LOSS - -100.00% - $5.0
```

### 2. ❌ Logs de Erro

```
❌ Erro ao enviar log para Supabase: [detalhes do erro]
```

---

## 🎯 RESUMO FINAL

O **Tunder Bot** utiliza o Supabase como banco de dados principal para:

1. **Armazenar Resultados:** Todos os resultados de trading são registrados
2. **Análise de Performance:** Dados para análise de rentabilidade
3. **Histórico Completo:** Registro temporal de todas as operações
4. **Monitoramento:** Acompanhamento em tempo real via dashboard

**Tabela Principal:** `tunder_bot_logs`  
**Frequência de Envio:** A cada operação finalizada  
**Tipo de Dados:** Resultados financeiros e timestamps  
**Método:** INSERT assíncrono com tratamento de erros

---

*Documento gerado automaticamente a partir da análise do código `tunderbot.py`*  
*Data: Janeiro 2024*