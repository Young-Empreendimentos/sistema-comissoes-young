#!/usr/bin/env python
"""Runner para o Sistema de Comissões"""
import os
import sys

# Definir diretório do projeto
project_dir = os.path.join(os.path.dirname(__file__), "Projeto comissões")

# Mudar para o diretório do projeto
os.chdir(project_dir)

# Adicionar ao path
sys.path.insert(0, project_dir)

# Importar e rodar a aplicação
from app import app

if __name__ == '__main__':
    print(f"Iniciando Sistema de Comissões Young...")
    print(f"Diretório: {project_dir}")
    print(f"Acesse: http://127.0.0.1:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
