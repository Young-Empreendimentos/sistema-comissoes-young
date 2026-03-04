"""
Debug - verificar campos de corretor no banco
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

result = supabase.table('sienge_comissoes').select('*').limit(5).execute()

if result.data:
    print("Campos disponíveis:", list(result.data[0].keys()))
    print("\nExemplo de dados:")
    for c in result.data:
        print(f"  broker_name: {c.get('broker_name')}")
        print(f"  broker_nome: {c.get('broker_nome')}")
        print(f"  broker_id: {c.get('broker_id')}")
        print("  ---")
