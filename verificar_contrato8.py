"""
Verificar comissão do contrato 8 - Morada da Coxilha
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from sienge_client import sienge_client
from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 80)
print("VERIFICANDO CONTRATO 8 - MORADA DA COXILHA")
print("=" * 80)

# Buscar no banco
result = supabase.table('sienge_comissoes').select('*').eq('numero_contrato', '8').ilike('enterprise_name', '%Morada%').execute()

print("\n--- NO BANCO (Supabase) ---")
if result.data:
    for c in result.data:
        print(f"\nID: {c.get('id')} | Sienge ID: {c.get('sienge_id')}")
        print(f"  Cliente: {c.get('customer_name')}")
        print(f"  Corretor: {c.get('broker_nome')}")
        print(f"  Empreendimento: {c.get('enterprise_name')}")
        print(f"  installment_status: {c.get('installment_status')}")
        print(f"  customer_situation_type: {c.get('customer_situation_type')}")
else:
    print("Não encontrado no banco")

# Buscar na API - empresa 14 (Morada da Coxilha)
print("\n--- NA API DO SIENGE ---")
sienge_client.company_id = '14'
comissoes = sienge_client.get_all_commissions_paginated()

for c in comissoes:
    if str(c.get('salesContractNumber')) == '8':
        print(f"\ncommissionID: {c.get('commissionID')}")
        print(f"  Cliente: {c.get('customerName')}")
        print(f"  Corretor: {c.get('brokerName')}")
        print(f"  installmentStatus: {c.get('installmentStatus')}")
        print(f"  customerSituationType: {c.get('customerSituationType')}")
        print(f"\nTodos os campos:")
        for key, value in sorted(c.items()):
            if value is not None:
                print(f"    {key}: {value}")
