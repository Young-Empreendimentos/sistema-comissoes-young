#!/bin/bash
# ============================================================
# Script de Setup para Hetzner - Sistema de Comissões Young
# Execute como root no servidor Hetzner
# ============================================================

set -e  # Parar em caso de erro

echo "============================================================"
echo "  Setup do Sistema de Comissões - Young Empreendimentos"
echo "  Servidor: Hetzner Cloud"
echo "============================================================"
echo

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Execute como root: sudo bash setup_hetzner.sh"
    exit 1
fi

# Variáveis
APP_USER="comissoes"
APP_DIR="/opt/sistema-comissoes"
REPO_URL="https://github.com/YoungEmpreendimentos/sistema-comissoes-young.git"

echo "📦 Atualizando sistema..."
apt update && apt upgrade -y

echo "📦 Instalando dependências..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor \
    certbot \
    python3-certbot-nginx \
    ufw

echo "🔒 Configurando firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "👤 Criando usuário da aplicação..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
fi

echo "📂 Criando diretório da aplicação..."
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

echo "📥 Clonando repositório..."
if [ -d "$APP_DIR/.git" ]; then
    cd $APP_DIR
    sudo -u $APP_USER git pull
else
    sudo -u $APP_USER git clone $REPO_URL $APP_DIR
fi

echo "🐍 Criando ambiente virtual Python..."
cd $APP_DIR
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER ./venv/bin/pip install --upgrade pip
sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt

echo "⚙️ Configurando Supervisor (processo da aplicação)..."
cat > /etc/supervisor/conf.d/comissoes.conf << 'EOF'
[program:comissoes]
directory=/opt/sistema-comissoes
command=/opt/sistema-comissoes/venv/bin/gunicorn --config gunicorn_config.py app:app
user=comissoes
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/comissoes/error.log
stdout_logfile=/var/log/comissoes/access.log
environment=PATH="/opt/sistema-comissoes/venv/bin"

[program:comissoes-scheduler]
directory=/opt/sistema-comissoes
command=/opt/sistema-comissoes/venv/bin/python scheduler.py
user=comissoes
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/comissoes/scheduler-error.log
stdout_logfile=/var/log/comissoes/scheduler.log
environment=PATH="/opt/sistema-comissoes/venv/bin"
EOF

echo "📁 Criando diretório de logs..."
mkdir -p /var/log/comissoes
chown $APP_USER:$APP_USER /var/log/comissoes

echo "🌐 Configurando Nginx..."
cat > /etc/nginx/sites-available/comissoes << 'EOF'
server {
    listen 80;
    server_name _;  # Substituir pelo seu domínio

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }

    # Static files
    location /static {
        alias /opt/sistema-comissoes/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

ln -sf /etc/nginx/sites-available/comissoes /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "✅ Testando configuração do Nginx..."
nginx -t

echo "🔄 Reiniciando serviços..."
systemctl restart nginx
supervisorctl reread
supervisorctl update

echo
echo "============================================================"
echo "  ✅ SETUP CONCLUÍDO!"
echo "============================================================"
echo
echo "PRÓXIMOS PASSOS:"
echo
echo "1. Criar arquivo .env:"
echo "   sudo -u $APP_USER nano $APP_DIR/.env"
echo "   (copie o conteúdo de env.example.txt e preencha)"
echo
echo "2. Gerar SECRET_KEY:"
echo "   python3 -c \"import secrets; print(secrets.token_hex(32))\""
echo
echo "3. Validar configuração:"
echo "   cd $APP_DIR && sudo -u $APP_USER ./venv/bin/python validate_env.py"
echo
echo "4. Iniciar aplicação:"
echo "   supervisorctl start comissoes"
echo "   supervisorctl start comissoes-scheduler"
echo
echo "5. (Opcional) Configurar SSL com Let's Encrypt:"
echo "   certbot --nginx -d seu-dominio.com"
echo
echo "6. Ver logs:"
echo "   tail -f /var/log/comissoes/error.log"
echo "   tail -f /var/log/comissoes/access.log"
echo
echo "============================================================"
