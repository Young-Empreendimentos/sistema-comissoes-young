"""
Debug - verificar comissão 161 mais detalhadamente
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
print("VERIFICANDO COMISSÃO 161")
print("=" * 70)

# Buscar na API do Sienge
print("\n[SIENGE API] Todas as comissões do contrato 161:")
commissions = sienge_client.get_commissions_all_companies()

sienge_ids = []
for c in commissions:
    if str(c.get('salesContractNumber')) == '161':
        print(f"\n  commissionID: {c.get('commissionID')}")
        print(f"  brokerID: {c.get('brokerID')}")
        print(f"  Corretor: {c.get('brokerName')}")
        print(f"  installmentStatus: {c.get('installmentStatus')}")
        sienge_ids.append(str(c.get('commissionID')))

# Verificar no Supabase
print("\n" + "-" * 70)
print("[SUPABASE] Comissões do contrato 161:")
result = supabase.table('sienge_comissoes').select('id,sienge_id,broker_id,broker_nome,installment_status,status_aprovacao').eq('numero_contrato', '161').execute()

for c in (result.data or []):
    print(f"\n  DB ID: {c.get('id')}")
    print(f"  sienge_id: {c.get('sienge_id')}")
    print(f"  broker_id: {c.get('broker_id')}")
    print(f"  Corretor: {c.get('broker_nome')}")
    print(f"  installment_status: {c.get('installment_status')}")
    print(f"  status_aprovacao: {c.get('status_aprovacao')}")
    
    if c.get('sienge_id') in sienge_ids:
        print(f"  ✓ sienge_id {c.get('sienge_id')} existe na API")
    else:
        print(f"  ✗ sienge_id {c.get('sienge_id')} NÃO existe na API!")

print("\n" + "-" * 70)
print(f"IDs na API do Sienge: {sienge_ids}")
