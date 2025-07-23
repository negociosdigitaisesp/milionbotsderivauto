# 🚀 INSTALAÇÃO RÁPIDA NA VPS

## 📋 Instalação Automática (Recomendado)

### 1. Conectar à VPS
```bash
ssh root@SEU_IP_DA_VPS
```

### 2. Baixar e Executar Script de Instalação
```bash
# Baixar o script
wget https://raw.githubusercontent.com/SEU_USUARIO/bot-strategy-hub/main/install_vps.sh

# Tornar executável
chmod +x install_vps.sh

# Executar instalação
./install_vps.sh --repo https://github.com/SEU_USUARIO/bot-strategy-hub.git
```

### 3. Configurar Tokens
```bash
# Editar arquivo de configuração
nano .env

# Configurar:
# - DERIV_API_TOKEN (obter em: https://app.deriv.com/account/api-token)
# - SUPABASE_URL e SUPABASE_KEY (criar em: https://supabase.com/)
```

### 4. Testar e Iniciar
```bash
# Testar configuração
./test_system.sh

# Iniciar sistema
sudo systemctl start trading-bots.service

# Monitorar logs
sudo journalctl -u trading-bots.service -f
```

---

## 📋 Instalação Manual

### 1. Preparar Sistema
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv -y

# Instalar ferramentas
sudo apt install git screen htop -y
```

### 2. Clonar Projeto
```bash
git clone https://github.com/SEU_USUARIO/bot-strategy-hub.git
cd bot-strategy-hub
```

### 3. Configurar Ambiente
```bash
# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 4. Configurar Variáveis
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

### 5. Testar e Executar
```bash
# Testar configuração
python test_environment.py

# Executar sistema
python bot_trading_system.py
```

---

## 🔧 Comandos Úteis

### Controle do Serviço
```bash
# Iniciar
sudo systemctl start trading-bots.service

# Parar
sudo systemctl stop trading-bots.service

# Reiniciar
sudo systemctl restart trading-bots.service

# Status
sudo systemctl status trading-bots.service

# Habilitar inicialização automática
sudo systemctl enable trading-bots.service
```

### Monitoramento
```bash
# Logs em tempo real
sudo journalctl -u trading-bots.service -f

# Últimos 50 logs
sudo journalctl -u trading-bots.service -n 50

# Monitorar recursos
htop

# Status do sistema
./monitor.sh
```

### Execução Manual
```bash
# Com screen (recomendado)
screen -S trading_bots
source venv/bin/activate
python bot_trading_system.py
# Ctrl+A, D para sair

# Voltar ao screen
screen -r trading_bots

# Script de conveniência
./start_bots.sh
```

---

## 🛠️ Troubleshooting

### Problema: Erro de Conexão Deriv
```bash
# Verificar token
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Token:', os.getenv('DERIV_API_TOKEN')[:10] + '...')
"

# Testar conexão
python test_environment.py
```

### Problema: Erro Supabase
```bash
# Verificar configurações
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('URL:', os.getenv('SUPABASE_URL'))
print('Key:', os.getenv('SUPABASE_KEY')[:20] + '...')
"
```

### Problema: Sistema Não Inicia
```bash
# Verificar logs
sudo journalctl -u trading-bots.service -n 50

# Verificar permissões
ls -la ~/bot-strategy-hub/

# Testar manualmente
cd ~/bot-strategy-hub
source venv/bin/activate
python bot_trading_system.py
```

---

## 📊 Configuração do Supabase

### 1. Criar Projeto
1. Acesse: https://supabase.com/
2. Crie conta gratuita
3. Crie novo projeto
4. Anote URL e ANON KEY

### 2. Configurar Banco
Execute no SQL Editor do Supabase:
```sql
CREATE TABLE operacoes (
    id SERIAL PRIMARY KEY,
    nome_bot VARCHAR(100) NOT NULL,
    lucro DECIMAL(10,2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operacoes_nome_bot ON operacoes(nome_bot);
CREATE INDEX idx_operacoes_timestamp ON operacoes(timestamp);
```

---

## 🔐 Configuração de Segurança

### Firewall
```bash
# Configurar UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw status
```

### Backup
```bash
# Criar backup dos dados
tar -czf backup_$(date +%Y%m%d).tar.gz bot-strategy-hub/

# Backup automático (crontab)
0 2 * * * cd /home/usuario && tar -czf backup_$(date +\%Y\%m\%d).tar.gz bot-strategy-hub/
```

---

## 📈 Monitoramento Avançado

### Logs Personalizados
```bash
# Ver apenas erros
sudo journalctl -u trading-bots.service -p err

# Logs de hoje
sudo journalctl -u trading-bots.service --since today

# Logs por período
sudo journalctl -u trading-bots.service --since "2024-01-01" --until "2024-01-02"
```

### Performance
```bash
# CPU e Memória
top -p $(pgrep -f bot_trading_system.py)

# Conexões de rede
netstat -an | grep python

# Espaço em disco
df -h
du -sh bot-strategy-hub/
```

---

## ✅ Checklist de Produção

- [ ] VPS configurada e atualizada
- [ ] Python 3.11+ instalado
- [ ] Dependências instaladas
- [ ] Arquivo .env configurado
- [ ] Tokens válidos configurados
- [ ] Supabase configurado
- [ ] Testes passando
- [ ] Serviço systemd criado
- [ ] Firewall configurado
- [ ] Monitoramento ativo
- [ ] Backup configurado

---

## 🆘 Suporte

### Arquivos de Log
- Sistema: `sudo journalctl -u trading-bots.service`
- Aplicação: `logs/trading_system.log`
- Sistema: `/var/log/syslog`

### Comandos de Diagnóstico
```bash
# Status completo
./monitor.sh

# Processos Python
ps aux | grep python

# Conexões ativas
netstat -tulpn | grep python

# Recursos do sistema
free -h && df -h
```

---

**🎯 Seu sistema estará operacional em menos de 10 minutos!**