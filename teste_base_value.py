"""
Teste - buscar baseValue de algumas comissões
"""

import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from supabase import create_client
from sienge_client import sienge_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 60)
print("TESTE - BUSCAR baseValue")
print("=" * 60)

# Buscar algumas comissões do banco
result = supabase.table('sienge_comissoes').select('*').limit(3).execute()

print("\nCampos que contêm 'valor' ou 'value':")
if result.data:
    for key in sorted(result.data[0].keys()):
        if 'valor' in key.lower() or 'value' in key.lower():
            print(f"  {key}: {result.data[0][key]}")

print("\n\nTestando busca de baseValue da API:")
for c in result.data[:3]:
    sienge_id = c.get('sienge_id')
    print(f"\nComissão {sienge_id} - Contrato {c.get('numero_contrato')}")
    
    # Buscar detalhe da API
    detalhe = sienge_client.get_commission_details(int(sienge_id))
    if detalhe:
        print(f"  baseValue da API: {detalhe.get('baseValue')}")
    else:
        print(f"  ERRO: Não foi possível buscar detalhes")
