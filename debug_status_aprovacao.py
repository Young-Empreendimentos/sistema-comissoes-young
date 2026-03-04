"""
Debug - verificar status_aprovacao no banco
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

result = supabase.table('sienge_comissoes').select('status_aprovacao, installment_status').execute()

# Contar status de aprovação
status_aprovacao_count = {}
installment_status_count = {}

for c in (result.data or []):
    sa = c.get('status_aprovacao') or 'NULL'
    ist = c.get('installment_status') or 'NULL'
    
    status_aprovacao_count[sa] = status_aprovacao_count.get(sa, 0) + 1
    installment_status_count[ist] = installment_status_count.get(ist, 0) + 1

print("STATUS APROVAÇÃO:")
print("-" * 40)
for status, count in sorted(status_aprovacao_count.items()):
    print(f"  '{status}': {count}")

print("\nINSTALLMENT STATUS (Sienge):")
print("-" * 40)
for status, count in sorted(installment_status_count.items()):
    print(f"  '{status}': {count}")

# Buscar comissões aprovadas que não estão pagas
print("\n" + "=" * 60)
print("COMISSÕES APROVADAS E NÃO PAGAS:")
print("=" * 60)

result2 = supabase.table('sienge_comissoes').select('*').eq('status_aprovacao', 'Aprovada').execute()
aprovadas = result2.data or []

nao_pagas = [c for c in aprovadas if 'PAID' not in (c.get('installment_status') or '').upper()]

print(f"Total aprovadas: {len(aprovadas)}")
print(f"Aprovadas e NÃO pagas: {len(nao_pagas)}")

for c in nao_pagas[:10]:
    print(f"  - Contrato {c.get('numero_contrato')} | {c.get('broker_nome')} | Status Sienge: {c.get('installment_status')} | R$ {c.get('commission_value')}")
