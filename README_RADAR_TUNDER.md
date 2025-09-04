# 🎯 Radar Analyzer Tunder Bot

## 📋 Visão Geral

O **Radar Analyzer Tunder** é uma versão especializada do sistema de análise de padrões, desenvolvida especificamente para o **Tunder Bot**. Este sistema monitora continuamente as operações do Tunder Bot e determina os momentos mais seguros para operar, utilizando filtros mais conservadores adequados ao growth rate de 1%.

## 🔄 Diferenças do Radar Original

### Radar Analyzer Original (Accumulator)
- **Bot Analisado**: `accumulator_standalone.py`
- **Tabela de Logs**: `scalping_accumulator_bot_logs`
- **Growth Rate**: 2%
- **Filtros**: Padrão

### Radar Analyzer Tunder (Novo)
- **Bot Analisado**: `tunderbot.py`
- **Tabela de Logs**: `tunder_bot_logs`
- **Growth Rate**: 1% (mais conservador)
- **Filtros**: Mais restritivos

## 📊 Filtros Mais Conservadores

| Critério | Radar Original | Radar Tunder | Justificativa |
|----------|----------------|--------------|---------------|
| **Derrotas em 20 ops** | > 3 = Instável | > 2 = Instável | Maior sensibilidade |
| **Filtro de Espera** | > 2 derrotas | > 1 derrota | Mais cauteloso |
| **Condição Geral** | > 2 derrotas em 10 | > 1 derrota em 10 | Mais exigente |
| **Condição Imediata** | ≥ 3 vitórias em 5 | ≥ 4 vitórias em 5 | Maior confiança |

## 🗂️ Estrutura de Arquivos

```
📁 milionbotsderivauto/
├── 📄 radar_analyzer.py              # Radar original (Accumulator)
├── 📄 radar_analyzer_tunder.py       # Radar para Tunder Bot (NOVO)
├── 📄 test_radar_tunder.py           # Testes do radar Tunder (NOVO)
├── 📄 start_radar_systems.py         # Script de inicialização (NOVO)
├── 📄 tunderbot.py                   # Bot Tunder com sistema de sinais
└── 📄 README_RADAR_TUNDER.md         # Esta documentação (NOVO)
```

## 🚀 Como Usar

### 1. Instalação e Configuração

```bash
# Certifique-se de que as dependências estão instaladas
pip install supabase python-dotenv

# Verifique se o arquivo .env está configurado
# Deve conter SUPABASE_URL e SUPABASE_KEY
```

### 2. Executar Teste

```bash
# Testar o sistema antes de usar
python test_radar_tunder.py
```

### 3. Executar Radar Tunder

```bash
# Executar apenas o radar Tunder
python radar_analyzer_tunder.py
```

### 4. Executar Sistema Completo

```bash
# Menu interativo para gerenciar ambos os radars
python start_radar_systems.py
```

## 📈 Funcionamento

### Fluxo de Análise

1. **Coleta de Dados**
   - Busca últimas 30 operações da tabela `tunder_bot_logs`
   - Converte `profit_percentage` em V (vitória) ou D (derrota)

2. **Aplicação de Filtros**
   - ✅ Dados suficientes (≥20 operações)
   - ✅ Mercado estável (≤2 derrotas em 20 ops)
   - ✅ Filtro de espera (≤1 derrota em 20 ops)
   - ✅ Padrão V-D-V detectado
   - ✅ Condição geral (≤1 derrota em 10 ops anteriores)
   - ✅ Condição imediata (≥4 vitórias em 5 ops anteriores)

3. **Envio de Sinal**
   - **UPSERT** na tabela `radar_de_apalancamiento_signals`
   - Garante apenas 1 linha por bot (`bot_name = 'Tunder Bot'`)
   - Controla operações após padrão (máximo 3)

### Estrutura do Sinal

```json
{
  "bot_name": "Tunder Bot",
  "is_safe_to_operate": true/false,
  "reason": "Motivo da decisão",
  "last_pattern_found": "V-D-V",
  "losses_in_last_10_ops": 0,
  "wins_in_last_5_ops": 4,
  "historical_accuracy": 85.5,
  "pattern_found_at": "2024-01-15T10:30:00",
  "operations_after_pattern": 0,
  "auto_disable_after_ops": 3
}
```

## 🔧 Configurações

### Parâmetros Principais

```python
# radar_analyzer_tunder.py
BOT_NAME = 'Tunder Bot'
TABELA_LOGS = 'tunder_bot_logs'
ANALISE_INTERVALO = 5  # segundos
OPERACOES_MINIMAS = 20
OPERACOES_HISTORICO = 30
```

### Personalização de Filtros

Para ajustar os filtros, modifique a função `analisar_padroes()` em `radar_analyzer_tunder.py`:

```python
# Exemplo: Tornar ainda mais conservador
if derrotas_ultimas_20 > 1:  # Era 2, agora 1
    return False, "Mercado muito instável"
```

## 📊 Monitoramento

### Logs do Sistema

O radar produz logs detalhados:

```
=== INICIANDO ANALISE TUNDER BOT - 15/01/2024 10:30:15 ===
* Buscando ultimas 30 operacoes do Tunder Bot...
* Historico Tunder Bot encontrado (25 operacoes): V D V V V D V V V V...
* Analise Tunder Bot das ultimas 20 operacoes: 2 derrotas
* Verificacao padrao V-D-V Tunder Bot: V-D-V = OK
* Filtro 1 Tunder Bot (Condicao Geral): 1 derrotas nas 10 operacoes anteriores
* Filtro 2 Tunder Bot (Condicao Imediata): 4 vitorias nas 5 operacoes anteriores
OK - Tunder Bot: Padrao Encontrado - Ligar o Bot - Todas as condicoes foram atendidas!

[OK] RESULTADO FINAL TUNDER BOT: SAFE TO OPERATE
* Motivo: Tunder Bot: Padrao Encontrado - Ligar o Bot
* Operacoes apos padrao: 0/3
* Status do envio: Enviado
```

### Verificação na Base de Dados

```sql
-- Verificar sinais do Tunder Bot
SELECT * FROM radar_de_apalancamiento_signals 
WHERE bot_name = 'Tunder Bot' 
ORDER BY created_at DESC;

-- Verificar operações do Tunder Bot
SELECT profit_percentage, created_at 
FROM tunder_bot_logs 
ORDER BY id DESC 
LIMIT 20;
```

## 🔄 Integração com Tunder Bot

O `tunderbot.py` já possui as funções integradas:

```python
# Funções disponíveis no tunderbot.py
async def save_signal_to_radar(...)     # Salvar sinal
async def get_signal_from_radar()       # Obter sinal atual
async def update_signal_status(...)     # Atualizar status
```

### Exemplo de Uso no Bot

```python
# Verificar se é seguro operar
signal = await self.get_signal_from_radar()
if signal and signal.get('is_safe_to_operate'):
    # Executar operação
    await self.executar_compra_accu(...)
else:
    logger.info("Aguardando sinal seguro do radar")
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de Conexão Supabase**
   ```
   ❌ Solução: Verificar .env com SUPABASE_URL e SUPABASE_KEY
   ```

2. **Tabela tunder_bot_logs não encontrada**
   ```
   ❌ Solução: Executar tunderbot.py primeiro para criar logs
   ```

3. **Sem dados suficientes**
   ```
   ❌ Solução: Aguardar pelo menos 20 operações do Tunder Bot
   ```

4. **Filtros muito restritivos**
   ```
   ❌ Solução: Ajustar parâmetros em analisar_padroes()
   ```

### Comandos de Diagnóstico

```bash
# Testar conexão e tabelas
python test_radar_tunder.py

# Verificar status geral
python start_radar_systems.py  # Opção 5

# Executar em modo debug
python -u radar_analyzer_tunder.py
```

## 📈 Próximos Passos

1. **Coleta de Dados**: Execute o `tunderbot.py` para gerar operações
2. **Teste do Radar**: Execute `test_radar_tunder.py` para validar
3. **Monitoramento**: Execute `radar_analyzer_tunder.py` em modo contínuo
4. **Integração**: Use os sinais no `tunderbot.py` para decisões de trading
5. **Otimização**: Ajuste filtros baseado na performance

## 🎯 Objetivos Alcançados

- ✅ **Duplicação da Estratégia**: Radar baseado no original
- ✅ **Análise Específica**: Focado no Tunder Bot e tabela `tunder_bot_logs`
- ✅ **Filtros Conservadores**: Adequados ao growth rate de 1%
- ✅ **Sistema UPSERT**: Garante uma linha por bot na tabela de sinais
- ✅ **Integração Completa**: Funções disponíveis no `tunderbot.py`
- ✅ **Testes e Documentação**: Sistema completo e testável

---

**🤖 Tunder Bot Radar System v1.0**  
*Sistema de análise inteligente para trading automatizado com growth rate conservador*