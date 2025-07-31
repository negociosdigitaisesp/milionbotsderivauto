# Supervisor Script - Guia de Uso

## 📋 Visão Geral

O `supervisor.py` é um script de gerenciamento que monitora e controla o `bot_trading_system.py`, garantindo estabilidade através de reinicializações automáticas periódicas.

## 🎯 Funcionalidades

- **Monitoramento Contínuo**: Supervisiona o bot trading system 24/7
- **Reinício Automático**: Reinicia o sistema a cada 1 hora para limpar memória
- **Encerramento Gracioso**: Gerencia processos de forma segura
- **Logs Detalhados**: Registra todas as ações com timestamps
- **Tratamento de Erros**: Recuperação automática de falhas
- **Controle Manual**: Permite interrupção segura com Ctrl+C

## ⚙️ Configurações

```python
script_a_rodar = "bot_trading_system.py"        # Script a ser supervisionado
tempo_de_execucao_segundos = 3600               # 1 hora de execução
pausa_entre_reinicios_segundos = 15             # 15s de pausa entre ciclos
```

## 🚀 Como Usar

### 1. Execução Direta
```bash
python supervisor.py
```

### 2. Execução em Background (Linux/Mac)
```bash
nohup python supervisor.py > supervisor.log 2>&1 &
```

### 3. Execução em Background (Windows)
```cmd
start /B python supervisor.py > supervisor.log 2>&1
```

## 📊 Logs e Monitoramento

O supervisor gera logs detalhados com timestamps:

```
[2024-01-15 10:30:00] 🚀 SUPERVISOR INICIADO
[2024-01-15 10:30:00] 🤖 Iniciando script dos bots: bot_trading_system.py
[2024-01-15 10:30:00] ✅ Script iniciado com sucesso!
[2024-01-15 10:30:00] 🆔 PID do processo: 12345
[2024-01-15 10:30:00] ⏳ Aguardando execução por 3600s...
```

## 🛑 Encerramento

### Encerramento Manual
- Pressione `Ctrl+C` para encerrar graciosamente
- O supervisor encerrará o bot e sairá de forma segura

### Encerramento Automático
- Após 5 falhas consecutivas de reconexão
- Em caso de erro crítico no sistema

## 🔧 Estrutura de Arquivos

```
bot-strategy-hub/
├── supervisor.py              # Script supervisor
├── bot_trading_system.py      # Sistema de bots
├── venv/                      # Ambiente virtual
│   ├── Scripts/python.exe     # Windows
│   └── bin/python3            # Linux/Mac
└── supervisor.log             # Logs do supervisor
```

## ⚠️ Requisitos

1. **Ambiente Virtual**: Pasta `venv` deve existir
2. **Script Principal**: `bot_trading_system.py` deve estar presente
3. **Permissões**: Permissões de execução adequadas
4. **Python**: Python 3.7+ instalado

## 🔍 Troubleshooting

### Erro: "Executável Python não encontrado"
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Erro: "Script não encontrado"
- Verifique se `bot_trading_system.py` está na mesma pasta
- Confirme o nome do arquivo

### Processo não encerra
- O supervisor tenta encerramento gracioso (10s)
- Se falhar, força o encerramento com `kill()`

## 📈 Benefícios

- **Estabilidade**: Reinicializações periódicas previnem vazamentos
- **Disponibilidade**: Recuperação automática de falhas
- **Monitoramento**: Logs detalhados para análise
- **Controle**: Gerenciamento seguro de processos
- **Automação**: Operação 24/7 sem intervenção manual

## 🔄 Ciclo de Vida

1. **Início**: Supervisor inicia o bot trading system
2. **Monitoramento**: Aguarda por 1 hora ou falha
3. **Encerramento**: Encerra graciosamente o processo
4. **Pausa**: Aguarda 15 segundos
5. **Reinício**: Volta ao passo 1

Este sistema garante operação contínua e estável dos bots de trading! 🚀