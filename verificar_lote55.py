"""
Verificar comissões do Lote 55 Morada da Coxilha
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Buscar por lote 55 e Morada da Coxilha
result = supabase.table('sienge_comissoes').select('*').eq('unit_name', '55').ilike('enterprise_name', '%Morada%').execute()

print("=== COMISSÕES DO LOTE 55 - MORADA DA COXILHA ===")
if result.data:
    for c in result.data:
        print(f"\nID: {c.get('id')} | Sienge ID: {c.get('sienge_id')}")
        print(f"  Cliente: {c.get('customer_name')}")
        print(f"  Corretor: {c.get('broker_nome')}")
        print(f"  Contrato: {c.get('numero_contrato')}")
        print(f"  Valor: R$ {c.get('commission_value')}")
        print(f"  installment_status: '{c.get('installment_status')}'")
        print(f"  status_aprovacao: '{c.get('status_aprovacao')}'")
else:
    print("Nenhuma comissão encontrada")
