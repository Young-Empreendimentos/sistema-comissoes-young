#!/bin/bash
# ============================================================
# Verifica status do Scheduler de Sincronização
# Execute no servidor: bash verificar_scheduler.sh
# ============================================================

echo "============================================================"
echo "  STATUS DO SCHEDULER - Sistema de Comissões"
echo "============================================================"
echo

echo "📊 Status dos serviços:"
supervisorctl status comissoes
supervisorctl status comissoes-scheduler

echo
echo "📅 Configuração de horário (do .env):"
grep -E "^SYNC_" /opt/sistema-comissoes/.env 2>/dev/null || echo "Usando padrão: 6:00"

echo
echo "📜 Últimas 20 linhas do log do scheduler:"
echo "------------------------------------------------------------"
tail -20 /var/log/comissoes/scheduler.log 2>/dev/null || echo "Log não encontrado"

echo
echo "🔍 Verificar se scheduler está rodando:"
ps aux | grep "[s]cheduler.py" || echo "Processo scheduler não encontrado!"

echo
echo "============================================================"
echo "  COMANDOS ÚTEIS:"
echo "============================================================"
echo "  Reiniciar scheduler:  supervisorctl restart comissoes-scheduler"
echo "  Ver logs em tempo real: tail -f /var/log/comissoes/scheduler.log"
echo "  Forçar sincronização:   cd /opt/sistema-comissoes && ./venv/bin/python scheduler.py --sync"
echo "============================================================"
