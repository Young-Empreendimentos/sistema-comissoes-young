"""
Verificar comissão do Erivelto
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Buscar por nome do cliente
result = supabase.table('sienge_comissoes').select('*').ilike('customer_name', '%ERIVELTO%').execute()

print("=== COMISSÕES DO ERIVELTO ===")
if result.data:
    for c in result.data:
        print(f"\nID: {c.get('id')} | Sienge ID: {c.get('sienge_id')}")
        print(f"  Cliente: {c.get('customer_name')}")
        print(f"  Contrato: {c.get('numero_contrato')}")
        print(f"  Lote: {c.get('unit_name')}")
        print(f"  Empreendimento: {c.get('enterprise_name')}")
        print(f"  installment_status: '{c.get('installment_status')}'")
        print(f"  status_aprovacao: '{c.get('status_aprovacao')}'")
else:
    print("Nenhuma comissão encontrada")

# Verificar também por lote 323
print("\n\n=== COMISSÕES DO LOTE 323 ===")
result2 = supabase.table('sienge_comissoes').select('*').eq('unit_name', '323').execute()

if result2.data:
    for c in result2.data:
        print(f"\nID: {c.get('id')} | Sienge ID: {c.get('sienge_id')}")
        print(f"  Cliente: {c.get('customer_name')}")
        print(f"  Contrato: {c.get('numero_contrato')}")
        print(f"  Lote: {c.get('unit_name')}")
        print(f"  Empreendimento: {c.get('enterprise_name')}")
        print(f"  installment_status: '{c.get('installment_status')}'")
        print(f"  status_aprovacao: '{c.get('status_aprovacao')}'")
else:
    print("Nenhuma comissão encontrada")
