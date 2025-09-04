# 🎯 Guia de Execução dos Sistemas de Radar

## 📋 Visão Geral

O sistema foi configurado para permitir a execução simultânea de ambos os radares:
- **Radar Analyzer Original** (para Accumulator Bot)
- **Radar Analyzer Tunder** (para Tunder Bot)

## 🚀 Formas de Execução

### 1. Modo Automático (Recomendado)

**Execução via linha de comando:**
```bash
python start_radar_systems.py --auto
```

**Execução via arquivo batch:**
```bash
start_both_radars.bat
```

### 2. Modo Interativo

**Execução com menu:**
```bash
python start_radar_systems.py
```

No menu interativo, escolha a opção **3** para executar ambos em paralelo.

## ⚙️ Configurações dos Radares

### Radar Analyzer Original
- **Bot monitorado:** scalping_accumulator_bot_logs
- **Intervalo de análise:** 5 segundos
- **Operações mínimas:** 20
- **Histórico analisado:** 30 operações
- **Growth Rate:** Padrão

### Radar Analyzer Tunder
- **Bot monitorado:** tunder_bot_logs (Tunder Bot)
- **Intervalo de análise:** 5 segundos
- **Operações mínimas:** 10 (ajustado)
- **Histórico analisado:** 30 operações
- **Growth Rate:** 1% (mais conservador)

## 📊 Monitoramento

Ambos os radares enviam sinais para a tabela `radar_de_apalancamiento_signals`:

- **Radar Original:** Monitora padrões V-D-V para o Accumulator
- **Radar Tunder:** Aplica filtros conservadores para o Tunder Bot

## 🛑 Como Parar

- **Ctrl+C** no terminal para interromper ambos os processos
- Os radares finalizam de forma segura e coordenada

## 📁 Arquivos Relacionados

- `start_radar_systems.py` - Script principal de inicialização
- `start_both_radars.bat` - Arquivo batch para execução rápida
- `radar_analyzer.py` - Radar original (Accumulator)
- `radar_analyzer_tunder.py` - Radar do Tunder Bot

## ✅ Verificação de Status

Para verificar se os sistemas estão funcionando:

1. Execute o modo interativo: `python start_radar_systems.py`
2. Escolha a opção **5** (Verificar status dos sistemas)

## 🔧 Solução de Problemas

### Arquivos Faltando
O sistema verifica automaticamente:
- `radar_analyzer.py`
- `radar_analyzer_tunder.py`
- `.env`

### Conexão com Supabase
Ambos os radares verificam a conexão antes de iniciar a análise.

### Logs de Execução
Cada radar exibe logs detalhados de sua execução, incluindo:
- Conexão com banco de dados
- Análise de operações
- Envio de sinais
- Status de segurança

## 🎯 Integração com Bots

- **Accumulator Bot:** Lê sinais do radar original
- **Tunder Bot:** Lê sinais do radar tunder via `tunderbot.py`

Ambos os bots verificam a coluna `is_safe_to_operate` na tabela de sinais antes de executar operações.