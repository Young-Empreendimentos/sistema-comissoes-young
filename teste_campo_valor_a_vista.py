"""
Teste - verificar se o campo valor_a_vista existe e pode ser atualizado
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 60)
print("TESTE - Campo valor_a_vista")
print("=" * 60)

# Buscar uma comissão
result = supabase.table('sienge_comissoes').select('id,sienge_id,numero_contrato').limit(1).execute()

if result.data:
    c = result.data[0]
    print(f"\nTestando com comissão ID {c['id']} - Contrato {c['numero_contrato']}")
    
    # Tentar atualizar o campo valor_a_vista
    try:
        update_result = supabase.table('sienge_comissoes').update({
            'valor_a_vista': 12345.67
        }).eq('id', c['id']).execute()
        
        print(f"  Atualização OK!")
        
        # Verificar se foi salvo
        check = supabase.table('sienge_comissoes').select('valor_a_vista').eq('id', c['id']).execute()
        print(f"  Valor salvo: {check.data[0].get('valor_a_vista')}")
        
        # Reverter para None
        supabase.table('sienge_comissoes').update({
            'valor_a_vista': None
        }).eq('id', c['id']).execute()
        print(f"  Revertido para None")
        
    except Exception as e:
        print(f"  ERRO: {e}")
