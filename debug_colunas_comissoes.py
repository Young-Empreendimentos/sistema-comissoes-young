"""
Debug - verificar colunas existentes na tabela sienge_comissoes
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 60)
print("COLUNAS DA TABELA sienge_comissoes")
print("=" * 60)

# Buscar 1 registro para ver os campos
result = supabase.table('sienge_comissoes').select('*').limit(1).execute()

if result.data:
    print("\nCampos disponíveis:")
    for key in sorted(result.data[0].keys()):
        value = result.data[0][key]
        print(f"  {key}: {type(value).__name__} = {value}")
else:
    print("Nenhum registro encontrado")
