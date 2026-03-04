"""
Verificar comissão 185 da Andreice
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
print("VERIFICANDO COMISSÃO 185 - ANDREICE")
print("=" * 70)

# 1. Verificar no Supabase
print("\n[SUPABASE] Buscando comissões com contrato 185...")
result = supabase.table('sienge_comissoes').select('*').ilike('numero_contrato', '%185%').execute()

for c in (result.data or []):
    if 'andreice' in (c.get('broker_nome') or '').lower():
        print(f"\n  Encontrada no Supabase:")
        print(f"    ID banco: {c.get('id')}")
        print(f"    Sienge ID: {c.get('sienge_id')}")
        print(f"    Contrato: {c.get('numero_contrato')}")
        print(f"    Corretor: {c.get('broker_nome')}")
        print(f"    Empreendimento: {c.get('enterprise_name')}")
        print(f"    Status Sienge (banco): {c.get('installment_status')}")
        print(f"    Status Aprovação: {c.get('status_aprovacao')}")
        print(f"    Valor: R$ {c.get('commission_value')}")
        print(f"    Atualizado em: {c.get('atualizado_em')}")

# 2. Verificar na API do Sienge
print("\n" + "=" * 70)
print("[SIENGE API] Buscando comissões...")
print("=" * 70)

commissions = sienge_client.get_commissions_all_companies()

for c in commissions:
    contrato = str(c.get('salesContractNumber') or '')
    corretor = (c.get('brokerName') or '').lower()
    
    if '185' in contrato and 'andreice' in corretor:
        print(f"\n  Encontrada na API Sienge:")
        print(f"    Commission ID: {c.get('commissionID')}")
        print(f"    Contrato: {c.get('salesContractNumber')}")
        print(f"    Corretor: {c.get('brokerName')}")
        print(f"    Empreendimento: {c.get('enterpriseName')}")
        print(f"    Status Sienge (API): {c.get('installmentStatus')}")
        print(f"    Valor: R$ {c.get('value')}")
        print(f"    Customer Situation: {c.get('customerSituationType')}")
