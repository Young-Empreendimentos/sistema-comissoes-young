#!/bin/bash
# ============================================================
# Script de Atualização - Sistema de Comissões Young
# Execute para atualizar o código no servidor
# ============================================================

set -e

APP_DIR="/opt/sistema-comissoes"
APP_USER="comissoes"

echo "============================================================"
echo "  Atualizando Sistema de Comissões"
echo "============================================================"
echo

cd $APP_DIR

echo "📥 Baixando atualizações..."
sudo -u $APP_USER git pull

echo "📦 Atualizando dependências..."
sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt

echo "✅ Validando configuração..."
sudo -u $APP_USER ./venv/bin/python validate_env.py || true

echo "🔄 Reiniciando aplicação..."
supervisorctl restart comissoes
supervisorctl restart comissoes-scheduler

echo
echo "✅ Atualização concluída!"
echo
echo "Ver status: supervisorctl status"
echo "Ver logs: tail -f /var/log/comissoes/error.log"
