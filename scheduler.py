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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

# Configuração de E-mail
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_SYNC_NOTIFY', 'antonio@youngempreendimentos.com.br')

scheduler = BlockingScheduler()
running = True


def enviar_email_notificacao(sucesso: bool, resultado: dict, erro: str = None):
    """Envia e-mail de notificação sobre a sincronização"""
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print("[E-mail] Credenciais SMTP não configuradas, pulando envio de e-mail")
            return
        
        data_hora = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        if sucesso:
            assunto = f"[OK] Sincronização Sienge - {data_hora}"
            
            # Montar corpo do e-mail com resultados
            corpo_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #28a745;">Sincronização realizada com sucesso</h2>
                <p><strong>Data/Hora:</strong> {data_hora}</p>
                
                <h3>Resumo:</h3>
                <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Empreendimentos</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{resultado.get('empreendimentos', {}).get('total', 0)} sincronizados</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Contratos</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{resultado.get('contratos', {}).get('total', 0)} sincronizados</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Corretores</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{resultado.get('corretores', {}).get('total', 0)} sincronizados</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Comissões</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{resultado.get('comissoes', {}).get('total', 0)} sincronizadas</td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px; color: #6c757d; font-size: 12px;">
                    Sistema de Comissões - Young Empreendimentos
                </p>
            </body>
            </html>
            """
        else:
            assunto = f"[ERRO] Sincronização Sienge - {data_hora}"
            
            corpo_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #dc3545;">Erro na Sincronização</h2>
                <p><strong>Data/Hora:</strong> {data_hora}</p>
                
                <h3>Detalhes do Erro:</h3>
                <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">
{erro or 'Erro desconhecido'}
                </pre>
                
                <p style="margin-top: 20px;">
                    Por favor, verifique o servidor ou entre em contato com o suporte técnico.
                </p>
                
                <p style="margin-top: 20px; color: #6c757d; font-size: 12px;">
                    Sistema de Comissões - Young Empreendimentos
                </p>
            </body>
            </html>
            """
        
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        msg.attach(MIMEText(corpo_html, 'html'))
        
        # Enviar
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        
        print(f"[E-mail] Notificação enviada para {EMAIL_TO}")
        
    except Exception as e:
        print(f"[E-mail] Erro ao enviar notificação: {str(e)}")


def sincronizacao_diaria():
    """Executa sincronização diária com o Sienge"""
    print(f"[{datetime.now()}] Iniciando sincronização automática...")
    
    resultado = {}
    sucesso = False
    erro_msg = None
    
    try:
        from sync_sienge_supabase import SiengeSupabaseSync
        
        sync = SiengeSupabaseSync()
        resultado = sync.sync_all()
        
        # Verificar se todas as sincronizações foram bem sucedidas
        erros = []
        for chave, valor in resultado.items():
            if isinstance(valor, dict) and not valor.get('sucesso', True):
                erros.append(f"{chave}: {valor.get('erro', 'erro desconhecido')}")
        
        sucesso = len(erros) == 0
        if erros:
            erro_msg = "\n".join(erros)
        
        print(f"[{datetime.now()}] Sincronização concluída!")
        print(f"  - Empreendimentos: {resultado.get('empreendimentos', {})}")
        print(f"  - Contratos: {resultado.get('contratos', {})}")
        print(f"  - Comissões: {resultado.get('comissoes', {})}")
        
    except Exception as e:
        print(f"[{datetime.now()}] ERRO na sincronização: {str(e)}")
        import traceback
        erro_msg = traceback.format_exc()
        traceback.print_exc()
    
    # Enviar e-mail de notificação
    enviar_email_notificacao(sucesso, resultado, erro_msg)

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
