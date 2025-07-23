#!/bin/bash

# ========================================
# SCRIPT DE INICIALIZAÇÃO PARA VPS
# Sistema de Trading Automatizado
# ========================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Verificar se está rodando como root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Rodando como root. Recomendado criar um usuário específico."
        read -p "Continuar mesmo assim? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Atualizar sistema
update_system() {
    print_header "ATUALIZANDO SISTEMA"
    
    print_status "Atualizando lista de pacotes..."
    sudo apt update
    
    print_status "Atualizando pacotes instalados..."
    sudo apt upgrade -y
    
    print_status "Instalando dependências básicas..."
    sudo apt install -y curl wget git build-essential software-properties-common
}

# Instalar Python 3.11+
install_python() {
    print_header "INSTALANDO PYTHON 3.11+"
    
    # Verificar se Python 3.11+ já está instalado
    if command -v python3.11 &> /dev/null; then
        print_status "Python 3.11 já está instalado"
        python3.11 --version
        return
    fi
    
    print_status "Adicionando repositório do Python..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    
    print_status "Instalando Python 3.11..."
    sudo apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev
    
    print_status "Verificando instalação..."
    python3.11 --version
    python3.11 -m pip --version
}

# Instalar ferramentas adicionais
install_tools() {
    print_header "INSTALANDO FERRAMENTAS ADICIONAIS"
    
    print_status "Instalando screen para execução em background..."
    sudo apt install -y screen
    
    print_status "Instalando htop para monitoramento..."
    sudo apt install -y htop
    
    print_status "Instalando ufw para firewall..."
    sudo apt install -y ufw
}

# Configurar firewall básico
setup_firewall() {
    print_header "CONFIGURANDO FIREWALL"
    
    print_status "Configurando UFW..."
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 80
    sudo ufw allow 443
    
    print_status "Status do firewall:"
    sudo ufw status
}

# Clonar repositório
clone_repository() {
    print_header "CONFIGURANDO PROJETO"
    
    # Verificar se o diretório já existe
    if [ -d "bot-strategy-hub" ]; then
        print_warning "Diretório bot-strategy-hub já existe"
        read -p "Remover e clonar novamente? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf bot-strategy-hub
        else
            cd bot-strategy-hub
            print_status "Usando diretório existente"
            return
        fi
    fi
    
    print_status "Clonando repositório..."
    # Substitua pela URL do seu repositório
    if [ -n "$REPO_URL" ]; then
        git clone "$REPO_URL" bot-strategy-hub
    else
        print_error "URL do repositório não fornecida"
        print_status "Por favor, clone manualmente:"
        print_status "git clone https://github.com/SEU_USUARIO/bot-strategy-hub.git"
        exit 1
    fi
    
    cd bot-strategy-hub
}

# Configurar ambiente Python
setup_python_env() {
    print_header "CONFIGURANDO AMBIENTE PYTHON"
    
    print_status "Criando ambiente virtual..."
    python3.11 -m venv venv
    
    print_status "Ativando ambiente virtual..."
    source venv/bin/activate
    
    print_status "Atualizando pip..."
    pip install --upgrade pip
    
    print_status "Instalando dependências..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_error "Arquivo requirements.txt não encontrado"
        exit 1
    fi
    
    print_status "Verificando instalação..."
    pip list
}

# Configurar arquivo .env
setup_environment() {
    print_header "CONFIGURANDO VARIÁVEIS DE AMBIENTE"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_status "Copiando .env.example para .env..."
            cp .env.example .env
            
            print_warning "IMPORTANTE: Configure o arquivo .env com seus dados reais!"
            print_status "Edite o arquivo .env:"
            print_status "nano .env"
            print_status ""
            print_status "Você precisa configurar:"
            print_status "- DERIV_API_TOKEN (obtenha em: https://app.deriv.com/account/api-token)"
            print_status "- SUPABASE_URL (crie projeto em: https://supabase.com/)"
            print_status "- SUPABASE_KEY (chave anônima do Supabase)"
            
            read -p "Pressione Enter para continuar após configurar o .env..."
        else
            print_error "Arquivo .env.example não encontrado"
            exit 1
        fi
    else
        print_status "Arquivo .env já existe"
    fi
}

# Testar configuração
test_configuration() {
    print_header "TESTANDO CONFIGURAÇÃO"
    
    print_status "Ativando ambiente virtual..."
    source venv/bin/activate
    
    print_status "Executando teste de ambiente..."
    if python test_environment.py; then
        print_status "✅ Todos os testes passaram!"
    else
        print_error "❌ Alguns testes falharam. Verifique a configuração."
        exit 1
    fi
}

# Criar serviço systemd
create_service() {
    print_header "CRIANDO SERVIÇO SYSTEMD"
    
    read -p "Criar serviço systemd para inicialização automática? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    USER=$(whoami)
    WORK_DIR=$(pwd)
    
    print_status "Criando arquivo de serviço..."
    sudo tee /etc/systemd/system/trading-bots.service > /dev/null <<EOF
[Unit]
Description=Trading Bots System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/python bot_trading_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    print_status "Habilitando serviço..."
    sudo systemctl daemon-reload
    sudo systemctl enable trading-bots.service
    
    print_status "Serviço criado! Para controlar:"
    print_status "sudo systemctl start trading-bots.service   # Iniciar"
    print_status "sudo systemctl stop trading-bots.service    # Parar"
    print_status "sudo systemctl status trading-bots.service  # Status"
    print_status "sudo journalctl -u trading-bots.service -f  # Logs"
}

# Criar scripts de conveniência
create_scripts() {
    print_header "CRIANDO SCRIPTS DE CONVENIÊNCIA"
    
    # Script de inicialização
    cat > start_bots.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python bot_trading_system.py
EOF
    chmod +x start_bots.sh
    
    # Script de teste
    cat > test_system.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python test_environment.py
EOF
    chmod +x test_system.sh
    
    # Script de monitoramento
    cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== STATUS DO SISTEMA ==="
sudo systemctl status trading-bots.service --no-pager
echo ""
echo "=== ÚLTIMOS LOGS ==="
sudo journalctl -u trading-bots.service -n 20 --no-pager
echo ""
echo "=== RECURSOS DO SISTEMA ==="
free -h
df -h
EOF
    chmod +x monitor.sh
    
    print_status "Scripts criados:"
    print_status "./start_bots.sh   - Iniciar bots manualmente"
    print_status "./test_system.sh  - Testar configuração"
    print_status "./monitor.sh      - Monitorar sistema"
}

# Função principal
main() {
    print_header "INSTALAÇÃO DO SISTEMA DE TRADING NA VPS"
    
    print_status "Iniciando instalação automática..."
    print_warning "Este script irá instalar e configurar o sistema completo"
    
    read -p "Continuar com a instalação? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Instalação cancelada"
        exit 0
    fi
    
    # Verificar argumentos
    if [ "$1" = "--repo" ] && [ -n "$2" ]; then
        export REPO_URL="$2"
        print_status "Usando repositório: $REPO_URL"
    fi
    
    # Executar instalação
    check_root
    update_system
    install_python
    install_tools
    setup_firewall
    
    # Se URL do repo foi fornecida, clonar
    if [ -n "$REPO_URL" ]; then
        clone_repository
    else
        print_warning "URL do repositório não fornecida"
        print_status "Certifique-se de estar no diretório do projeto"
        if [ ! -f "bot_trading_system.py" ]; then
            print_error "Arquivo bot_trading_system.py não encontrado"
            print_status "Clone o repositório manualmente e execute este script novamente"
            exit 1
        fi
    fi
    
    setup_python_env
    setup_environment
    test_configuration
    create_service
    create_scripts
    
    print_header "INSTALAÇÃO CONCLUÍDA!"
    
    print_status "✅ Sistema instalado com sucesso!"
    print_status "✅ Ambiente Python configurado"
    print_status "✅ Dependências instaladas"
    print_status "✅ Firewall configurado"
    print_status "✅ Scripts de conveniência criados"
    
    print_warning "PRÓXIMOS PASSOS:"
    print_status "1. Configure o arquivo .env com seus tokens reais"
    print_status "2. Execute: ./test_system.sh para verificar"
    print_status "3. Execute: ./start_bots.sh para iniciar manualmente"
    print_status "4. Ou use: sudo systemctl start trading-bots.service"
    
    print_status "\nPara monitorar: ./monitor.sh"
    print_status "Para logs em tempo real: sudo journalctl -u trading-bots.service -f"
    
    print_header "SISTEMA PRONTO PARA OPERAR!"
}

# Verificar argumentos de ajuda
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Uso: $0 [--repo URL_DO_REPOSITORIO]"
    echo ""
    echo "Opções:"
    echo "  --repo URL    URL do repositório Git para clonar"
    echo "  --help        Mostrar esta ajuda"
    echo ""
    echo "Exemplo:"
    echo "  $0 --repo https://github.com/usuario/bot-strategy-hub.git"
    exit 0
fi

# Executar função principal
main "$@"