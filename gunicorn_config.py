"""
Configuração do Gunicorn para produção
Sistema de Comissões - Young Empreendimentos

Uso: gunicorn --config gunicorn_config.py app:app
"""
import os
import multiprocessing

# Bind
bind = f"0.0.0.0:{os.getenv('FLASK_PORT', 5000)}"

# Workers
# IMPORTANTE: Usar apenas 1 worker se tiver scheduler interno
# ou mover scheduler para processo separado
workers = 1
threads = 4

# Worker class
worker_class = 'sync'  # ou 'gthread' para threads

# Timeout
timeout = 120  # segundos (aumentado para operações de sincronização)
graceful_timeout = 30
keepalive = 5

# Logging
errorlog = '-'  # stderr
accesslog = '-'  # stdout
loglevel = os.getenv('LOG_LEVEL', 'info')

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Process naming
proc_name = 'sistema-comissoes-young'

# Server hooks
def on_starting(server):
    """Executado quando Gunicorn inicia"""
    print("=" * 60)
    print("  Sistema de Comissões - Young Empreendimentos")
    print("  Iniciando com Gunicorn...")
    print("=" * 60)

def on_reload(server):
    """Executado no reload"""
    print("Recarregando servidor...")

def worker_int(worker):
    """Executado quando worker recebe SIGINT"""
    print(f"Worker {worker.pid} interrompido")

def worker_abort(worker):
    """Executado quando worker recebe SIGABRT"""
    print(f"Worker {worker.pid} abortado")

def pre_fork(server, worker):
    """Executado antes de criar worker"""
    pass

def post_fork(server, worker):
    """Executado após criar worker"""
    print(f"Worker {worker.pid} criado")

def pre_exec(server):
    """Executado antes de exec"""
    print("Preparando execução...")

def when_ready(server):
    """Executado quando servidor está pronto"""
    print(f"✅ Servidor pronto em {bind}")
    print("Para sincronização automática, execute: python scheduler.py")

def worker_exit(server, worker):
    """Executado quando worker sai"""
    print(f"Worker {worker.pid} finalizado")
