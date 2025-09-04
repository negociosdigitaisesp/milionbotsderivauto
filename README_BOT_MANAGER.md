# 🤖 Sistema de Gerenciamento de Bots

## Visão Geral

Este sistema implementa um gerenciador robusto para os bots de trading `tunderbot.py` e `accumulator_standalone.py`, com tratamento avançado de erros, monitoramento em tempo real e recuperação automática.

## 📁 Arquivos Principais

### 1. `bot_manager.py`
- **Função**: Gerenciador principal que controla ambos os bots
- **Recursos**:
  - Inicialização automática dos bots
  - Monitoramento contínuo de processos
  - Restart automático em caso de falha
  - Relatórios de status em tempo real
  - Shutdown graceful

### 2. `error_handler.py`
- **Função**: Sistema robusto de tratamento de erros
- **Recursos**:
  - Classificação de erros por tipo e severidade
  - Circuit breakers para prevenção de falhas em cascata
  - Estratégias de recuperação automática
  - Histórico de erros e estatísticas
  - Decorador `@with_error_handling` para funções críticas

### 3. `tunderbot.py` (Atualizado)
- **Função**: Bot de trading Tunder com tratamento de erros
- **Melhorias**:
  - Integração com `RobustErrorHandler`
  - Tratamento de erros em funções críticas
  - Logs aprimorados com nome do bot
  - Ativo alterado de `R_50` para `R_10`

### 4. `accumulator_standalone.py` (Atualizado)
- **Função**: Bot Accumulator Scalping com tratamento de erros
- **Melhorias**:
  - Integração com `RobustErrorHandler`
  - Tratamento de erros em métodos críticos
  - Logs aprimorados com identificação do bot
  - Decoradores de erro em funções principais

## 🚀 Como Usar

### Iniciar o Sistema Completo
```bash
python bot_manager.py
```

### Iniciar Bots Individualmente
```bash
# Tunder Bot
python tunderbot.py

# Accumulator Bot
python accumulator_standalone.py
```

## 📊 Monitoramento

### Status em Tempo Real
O Bot Manager exibe relatórios de status a cada minuto, incluindo:
- Status de cada bot (RUNNING/STOPPED/ERROR)
- PID dos processos
- Tempo de atividade (uptime)
- Contadores de erro e restart
- Estado dos circuit breakers

### Logs Detalhados
Cada bot gera logs específicos:
- `tunderbot.log` - Logs do Tunder Bot
- `accumulator_standalone.log` - Logs do Accumulator Bot
- Logs do Bot Manager no console

## 🛡️ Sistema de Tratamento de Erros

### Tipos de Erro
- **CONNECTION**: Erros de conexão
- **WEBSOCKET**: Problemas com WebSocket
- **AUTHENTICATION**: Falhas de autenticação
- **RATE_LIMIT**: Limitação de taxa da API
- **TICK_PROCESSING**: Erros no processamento de ticks
- **ORDER_EXECUTION**: Falhas na execução de ordens
- **SYSTEM**: Erros gerais do sistema

### Níveis de Severidade
- **LOW**: Erros menores, log apenas
- **MEDIUM**: Erros moderados, tentativa de recuperação
- **HIGH**: Erros graves, recuperação obrigatória
- **CRITICAL**: Erros críticos, podem causar shutdown

### Circuit Breakers
- **WebSocket**: 3 falhas → 30s timeout
- **API Calls**: 5 falhas → 60s timeout
- **Trading**: 2 falhas → 120s timeout

## 🔧 Configuração

### Variáveis de Ambiente
Certifique-se de que os arquivos `.env` estão configurados:
- `.env.accumulator` - Configurações do Accumulator Bot
- Variáveis de API da Deriv
- Configurações do Supabase

### Parâmetros do Bot Manager
```python
max_restart_attempts = 3  # Máximo de tentativas de restart
monitoring_interval = 10  # Intervalo de monitoramento (segundos)
health_check_interval = 30  # Intervalo de verificação de saúde
```

## 🚨 Recuperação Automática

### Estratégias Implementadas
1. **Reconexão WebSocket**: Backoff exponencial
2. **Reautenticação**: Delay fixo de 10s
3. **Rate Limit**: Espera progressiva
4. **Restart de Processo**: Até 3 tentativas

### Shutdown Graceful
- Sinal SIGINT/SIGTERM capturado
- Parada ordenada de todos os bots
- Limpeza de recursos
- Logs de finalização

## 📈 Melhorias Implementadas

### Correções de Erros
1. **Decorador `@with_error_handling`**: Corrigido para aceitar parâmetros `ErrorType` e `ErrorSeverity`
2. **Integração com Error Handler**: Ambos os bots agora usam o sistema robusto
3. **Logs Específicos**: Cada bot tem logs identificados
4. **Ativo Tunder Bot**: Alterado de `R_50` para `R_10`

### Funcionalidades Adicionadas
1. **Monitoramento de Processos**: Verificação contínua de PIDs
2. **Restart Automático**: Recuperação sem intervenção manual
3. **Circuit Breakers**: Prevenção de falhas em cascata
4. **Relatórios JSON**: Status estruturado para integração

## 🔍 Troubleshooting

### Bot Não Inicia
1. Verificar variáveis de ambiente
2. Confirmar dependências instaladas
3. Checar logs de erro no console

### Falhas Frequentes
1. Verificar conexão com internet
2. Validar credenciais da API Deriv
3. Confirmar configuração do Supabase

### Performance
1. Monitorar uso de CPU/memória
2. Verificar latência de rede
3. Analisar logs de circuit breakers

## 📝 Logs de Exemplo

```
2025-09-03 13:24:48,184 - BotManager - INFO - 🚀 Bot Manager inicializado
2025-09-03 13:24:48,202 - BotManager - INFO - ✅ Tunder Bot iniciado com sucesso - PID: 19740
2025-09-03 13:24:48,203 - BotManager - INFO - ✅ Accumulator Bot iniciado com sucesso - PID: 18972
```

## 🎯 Próximos Passos

1. **Métricas Avançadas**: Implementar coleta de métricas de performance
2. **Dashboard Web**: Interface gráfica para monitoramento
3. **Alertas**: Notificações por email/Telegram
4. **Backup Automático**: Backup de configurações e logs
5. **Load Balancing**: Distribuição de carga entre instâncias

---

**Status**: ✅ Sistema funcionando corretamente
**Última Atualização**: 03/09/2025
**Versão**: 1.0.0