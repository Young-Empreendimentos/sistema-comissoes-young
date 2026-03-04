"""
Verificar comissões do contrato 302C
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
print("VERIFICANDO CONTRATO 302C")
print("=" * 70)

# 1. Verificar no Supabase
print("\n[SUPABASE] Comissões do contrato 302C:")
result = supabase.table('sienge_comissoes').select('*').ilike('numero_contrato', '%302%').execute()

for c in (result.data or []):
    print(f"  - Sienge ID: {c.get('sienge_id')}")
    print(f"    Corretor: {c.get('broker_nome')}")
    print(f"    Contrato: {c.get('numero_contrato')}")
    print(f"    Empreendimento: {c.get('enterprise_name')}")
    print(f"    Status: {c.get('installment_status')}")
    print(f"    Valor: R$ {c.get('commission_value')}")
    print()

# 2. Verificar na API do Sienge
print("\n[SIENGE API] Buscando comissões...")
commissions = sienge_client.get_commissions_all_companies()

print(f"Total de comissões na API: {len(commissions)}")

# Filtrar por contrato 302
contrato_302 = [c for c in commissions if '302' in str(c.get('salesContractNumber', ''))]
print(f"\nComissões com contrato contendo '302': {len(contrato_302)}")

for c in contrato_302:
    print(f"  - Commission ID: {c.get('commissionID')}")
    print(f"    Corretor: {c.get('brokerName')}")
    print(f"    Contrato: {c.get('salesContractNumber')}")
    print(f"    Empreendimento: {c.get('enterpriseName')}")
    print(f"    Status: {c.get('installmentStatus')}")
    print(f"    Valor: R$ {c.get('value')}")
    print()

# 3. Buscar comissões do Erivelto
print("\n[SIENGE API] Comissões do Erivelto:")
erivelto = [c for c in commissions if 'erivelto' in (c.get('brokerName') or '').lower()]
print(f"Total: {len(erivelto)}")
for c in erivelto[:5]:
    print(f"  - Commission ID: {c.get('commissionID')}")
    print(f"    Contrato: {c.get('salesContractNumber')}")
    print(f"    Empreendimento: {c.get('enterpriseName')}")
    print(f"    Status: {c.get('installmentStatus')}")
    print()
