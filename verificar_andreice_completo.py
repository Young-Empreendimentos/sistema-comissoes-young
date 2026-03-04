"""
Verificar todas comissões da Andreice
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
print("COMISSÕES ANDREICE - COMPARAÇÃO BANCO vs API")
print("=" * 70)

# 1. Comissões no Supabase
print("\n[SUPABASE] Comissões da Andreice:")
result = supabase.table('sienge_comissoes').select('*').ilike('broker_nome', '%andreice%').execute()

banco_comissoes = {}
for c in (result.data or []):
    sienge_id = c.get('sienge_id')
    banco_comissoes[sienge_id] = c
    print(f"  - Sienge ID {sienge_id} | Contrato {c.get('numero_contrato')} | {c.get('installment_status')} | R$ {c.get('commission_value')}")

print(f"\nTotal no banco: {len(banco_comissoes)}")

# 2. Comissões na API
print("\n" + "-" * 70)
print("[SIENGE API] Comissões da Andreice:")

commissions = sienge_client.get_commissions_all_companies()
api_comissoes = {}

for c in commissions:
    corretor = (c.get('brokerName') or '').lower()
    if 'andreice' in corretor:
        commission_id = str(c.get('commissionID'))
        api_comissoes[commission_id] = c
        print(f"  - Commission ID {commission_id} | Contrato {c.get('salesContractNumber')} | {c.get('installmentStatus')} | R$ {c.get('value')}")

print(f"\nTotal na API: {len(api_comissoes)}")

# 3. Comparar
print("\n" + "=" * 70)
print("ANÁLISE:")
print("=" * 70)

# IDs no banco mas não na API
no_banco_apenas = set(banco_comissoes.keys()) - set(api_comissoes.keys())
if no_banco_apenas:
    print(f"\nComissões NO BANCO mas NÃO na API (podem estar desatualizadas):")
    for sid in no_banco_apenas:
        c = banco_comissoes[sid]
        print(f"  - Sienge ID {sid} | Contrato {c.get('numero_contrato')} | {c.get('installment_status')} | R$ {c.get('commission_value')}")

# IDs na API mas não no banco
na_api_apenas = set(api_comissoes.keys()) - set(banco_comissoes.keys())
if na_api_apenas:
    print(f"\nComissões NA API mas NÃO no banco (precisam ser adicionadas):")
    for cid in na_api_apenas:
        c = api_comissoes[cid]
        print(f"  - Commission ID {cid} | Contrato {c.get('salesContractNumber')} | {c.get('installmentStatus')} | R$ {c.get('value')}")

# Status diferentes
print(f"\nComissões com STATUS DIFERENTE entre banco e API:")
for sid in set(banco_comissoes.keys()) & set(api_comissoes.keys()):
    banco = banco_comissoes[sid]
    api = api_comissoes[sid]
    status_banco = banco.get('installment_status')
    status_api = api.get('installmentStatus')
    if status_banco != status_api:
        print(f"  - Sienge ID {sid} | Contrato {banco.get('numero_contrato')}")
        print(f"      Banco: {status_banco}")
        print(f"      API:   {status_api}")
