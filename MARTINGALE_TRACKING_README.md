# Sistema de Rastreamento Martingale - Documentação

## Visão Geral
Este sistema implementa rastreamento detalhado de progressões Martingale para o bot de trading, enviando dados completos para o Supabase.

## Funcionalidades Implementadas

### 1. Campos Adicionados ao Supabase
- `martingale_level`: Nível atual do Martingale (1-5)
- `martingale_multiplier`: Multiplicador usado no nível atual
- `consecutive_losses`: Número de perdas consecutivas
- `consecutive_wins`: Número de vitórias consecutivas
- `original_stake`: Stake original (nível 1)
- `martingale_stake`: Stake calculado com Martingale
- `total_martingale_investment`: Investimento total na sequência
- `martingale_sequence_id`: ID único da sequência Martingale
- `is_martingale_reset`: Indica se houve reset do Martingale
- `martingale_progression`: JSON com histórico da progressão

### 2. Sistema de Sequências
- **Início de Sequência**: Automaticamente iniciada na primeira perda
- **ID Único**: Cada sequência recebe um UUID único
- **Progressão Rastreada**: Todas as operações da sequência são registradas
- **Reset Automático**: Sequência resetada após vitória

### 3. Multiplicadores Configurados
```python
[1.0, 2.2, 4.84, 10.648, 23.426]
```

## Como Usar

### 1. Executar Script SQL
Execute o arquivo `martingale_supabase_schema.sql` no seu banco Supabase para adicionar os novos campos.

### 2. Configuração Automática
O sistema funciona automaticamente. Não requer configuração adicional.

### 3. Monitoramento
- Logs detalhados são gerados para cada operação
- Dados são enviados automaticamente para o Supabase
- Sequências são rastreadas em tempo real

## Estrutura dos Dados

### Exemplo de Progressão Martingale
```json
{
  "martingale_progression": [
    {
      "operation": "LOSS",
      "stake": 5.0,
      "level": 0,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "operation": "LOSS", 
      "stake": 11.0,
      "level": 1,
      "timestamp": "2024-01-15T10:31:00Z"
    },
    {
      "operation": "WIN",
      "stake": 24.2,
      "level": 2,
      "timestamp": "2024-01-15T10:32:00Z"
    }
  ]
}
```

## Views Criadas no Supabase

### 1. `martingale_sequences_analysis`
Análise completa de sequências Martingale com estatísticas de performance.

### 2. `bot_martingale_stats`
Estatísticas por bot incluindo:
- Total de sequências
- Taxa de sucesso
- Investimento médio
- Nível máximo atingido

### 3. `martingale_performance_by_level`
Performance detalhada por nível do Martingale.

## Logs e Monitoramento

### Logs Gerados
- Início de nova sequência Martingale
- Progressão de níveis
- Reset após vitória
- Investimento total acumulado

### Exemplo de Log
```
📈 MARTINGALE: Nova sequência iniciada - ID: abc123...
💰 MARTINGALE: Adicionado à progressão - LOSS $5.00 (Nível 1)
📈 MARTINGALE: Nível aumentado para 2/5
💰 NOVO STAKE: $11.00
```

## Benefícios

1. **Rastreamento Completo**: Todas as operações Martingale são registradas
2. **Análise Detalhada**: Dados permitem análise profunda de performance
3. **Gestão de Risco**: Melhor visibilidade do risco por sequência
4. **Otimização**: Dados para otimizar estratégias Martingale
5. **Auditoria**: Histórico completo para auditoria e análise

## Manutenção

### Limpeza de Dados
Considere implementar rotinas de limpeza para dados antigos se necessário.

### Monitoramento de Performance
Monitore o tamanho da tabela e performance das queries conforme o volume de dados cresce.

### Backup
Implemente backup regular dos dados de progressão Martingale.