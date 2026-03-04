"""
Debug - verificar comissão 161 do Marcelo
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

print("=" * 70)
print("VERIFICANDO COMISSÃO 161 - MARCELO DE LA ROSA MELLO")
print("=" * 70)

# 1. Verificar no Supabase
print("\n[SUPABASE] Buscando comissão...")
result = supabase.table('sienge_comissoes').select('*').eq('numero_contrato', '161').execute()

if result.data:
    for c in result.data:
        print(f"\n  ID: {c.get('id')}")
        print(f"  sienge_id: {c.get('sienge_id')}")
        print(f"  Corretor: {c.get('broker_nome')}")
        print(f"  Contrato: {c.get('numero_contrato')}")
        print(f"  Empreendimento: {c.get('enterprise_name')}")
        print(f"  Valor: R$ {c.get('commission_value')}")
        print(f"  status_aprovacao: {c.get('status_aprovacao')}")
        print(f"  installment_status: {c.get('installment_status')}")
        print(f"  customer_situation_type: {c.get('customer_situation_type')}")
else:
    print("  Nenhuma comissão encontrada no Supabase")

# 2. Verificar na API do Sienge
print("\n" + "-" * 70)
print("[SIENGE API] Buscando comissão...")
commissions = sienge_client.get_commissions_all_companies()

found = False
for c in commissions:
    if str(c.get('salesContractNumber')) == '161':
        found = True
        print(f"\n  commissionID: {c.get('commissionID')}")
        print(f"  Corretor: {c.get('brokerName')}")
        print(f"  Contrato: {c.get('salesContractNumber')}")
        print(f"  Empreendimento: {c.get('enterpriseName')}")
        print(f"  Valor: R$ {c.get('value')}")
        print(f"  installmentStatus: {c.get('installmentStatus')}")
        print(f"  customerSituationType: {c.get('customerSituationType')}")

if not found:
    print("  Comissão NÃO ENCONTRADA na API do Sienge!")
    print("  (Isso significa que foi removida/cancelada)")
