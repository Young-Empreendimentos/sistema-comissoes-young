"""
Iniciador do Sistema de Comissões Young
Para desenvolvimento local: python start_server.py
Para produção: use gunicorn (ver gunicorn_config.py)
"""
import sys
import os

# Garante que estamos na pasta do projeto (onde está o .env)
_here = os.path.dirname(os.path.abspath(__file__))
os.chdir(_here)

def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        print("=" * 60)
        print("  Sistema de Comissões - Young Empreendimentos")
        print("=" * 60)
        print()
        print("Carregando aplicação...")
        
        import app
        
        port = int(os.getenv("FLASK_PORT", 5000))
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
        
        print()
        print("=" * 60)
        if debug:
            print("  [AVISO] MODO DEBUG ATIVO - NAO USE EM PRODUCAO!")
        else:
            print("  [OK] Modo producao (debug=False)")
        print(f"  Servidor em: http://localhost:{port}")
        print(f"  Ou: http://127.0.0.1:{port}")
        print("=" * 60)
        print()
        
        # NOTA: Para sincronização automática, execute em outro terminal:
        # python scheduler.py
        
        app.app.run(debug=debug, port=port, host="0.0.0.0")
        
    except EnvironmentError as e:
        print()
        print("=" * 60, file=sys.stderr)
        print("  ERRO DE CONFIGURAÇÃO", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(str(e), file=sys.stderr)
        print()
        print("Verifique seu arquivo .env e execute: python validate_env.py")
        print()
        sys.exit(1)
        
    except Exception as e:
        import traceback
        print()
        print("=" * 60, file=sys.stderr)
        print("  ERRO AO INICIAR O SERVIDOR", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(str(e), file=sys.stderr)
        print()
        traceback.print_exc(file=sys.stderr)
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
