#!/usr/bin/env python3
"""
Scheduler de Sincronização - Sistema de Comissões Young
Execute em processo separado: python scheduler.py

Este script deve rodar separado do servidor web para evitar
duplicação de jobs em ambientes multi-worker (Gunicorn).
"""
import os
import sys
import time
import signal
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Garante que estamos na pasta do projeto
_here = os.path.dirname(os.path.abspath(__file__))
os.chdir(_here)

load_dotenv()

# Configuração
SYNC_HOUR = int(os.getenv('SYNC_HOUR', 6))  # Hora da sincronização (padrão: 6h)
SYNC_MINUTE = int(os.getenv('SYNC_MINUTE', 0))  # Minuto (padrão: 0)

scheduler = BlockingScheduler()
running = True

def sincronizacao_diaria():
    """Executa sincronização diária com o Sienge"""
    print(f"[{datetime.now()}] Iniciando sincronização automática...")
    
    try:
        from sync_sienge_supabase import SiengeSupabaseSync
        
        sync = SiengeSupabaseSync()
        resultado = sync.sync_all()
        
        print(f"[{datetime.now()}] Sincronização concluída!")
        print(f"  - Empreendimentos: {resultado.get('empreendimentos', {})}")
        print(f"  - Contratos: {resultado.get('contratos', {})}")
        print(f"  - Comissões: {resultado.get('comissoes', {})}")
        
    except Exception as e:
        print(f"[{datetime.now()}] ERRO na sincronização: {str(e)}")
        import traceback
        traceback.print_exc()

def sync_manual():
    """Executa sincronização manualmente (para testes)"""
    print("\n" + "=" * 60)
    print("  SINCRONIZAÇÃO MANUAL")
    print("=" * 60 + "\n")
    sincronizacao_diaria()

def signal_handler(signum, frame):
    """Trata sinais de interrupção"""
    global running
    print("\n\nRecebido sinal de parada. Finalizando scheduler...")
    running = False
    scheduler.shutdown(wait=False)
    sys.exit(0)

def main():
    """Função principal do scheduler"""
    global running
    
    # Registrar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("  SCHEDULER DE SINCRONIZAÇÃO")
    print("  Sistema de Comissões - Young Empreendimentos")
    print("=" * 60)
    print()
    print(f"Sincronização agendada para: {SYNC_HOUR:02d}:{SYNC_MINUTE:02d} diariamente")
    print()
    print("Comandos disponíveis:")
    print("  - Ctrl+C: Parar scheduler")
    print("  - Para sincronização manual: python scheduler.py --sync")
    print()
    print("Aguardando próxima execução...")
    print("-" * 60)
    
    # Agendar job
    scheduler.add_job(
        sincronizacao_diaria,
        CronTrigger(hour=SYNC_HOUR, minute=SYNC_MINUTE),
        id='sincronizacao_diaria',
        name='Sincronização Diária Sienge → Supabase',
        replace_existing=True
    )
    
    # Mostrar próxima execução
    jobs = scheduler.get_jobs()
    for job in jobs:
        print(f"Próxima execução: {job.next_run_time}")
    
    print()
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        print("\nScheduler finalizado.")

if __name__ == '__main__':
    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--sync', '-s', 'sync']:
            sync_manual()
        elif sys.argv[1] in ['--help', '-h', 'help']:
            print("Uso: python scheduler.py [opção]")
            print()
            print("Opções:")
            print("  --sync, -s    Executa sincronização manualmente")
            print("  --help, -h    Mostra esta ajuda")
            print()
            print("Sem argumentos: inicia scheduler em modo daemon")
        else:
            print(f"Opção desconhecida: {sys.argv[1]}")
            print("Use --help para ver opções disponíveis")
    else:
        main()
