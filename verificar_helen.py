"""
Testa a sincronização corrigida
"""
from sync_sienge_supabase import SiengeSupabaseSync
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("TESTANDO SINCRONIZAÇÃO CORRIGIDA")
print("=" * 60)
print()

# Executar sincronização de comissões
print("Executando sincronização de comissões...")
sync = SiengeSupabaseSync()
resultado = sync.sync_comissoes()
print(f"Resultado: {resultado}")
print()

# Verificar comissões da Helen no Itaqui
print("-" * 60)
print("VERIFICANDO COMISSÕES DA HELEN NO ITAQUI:")
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

result = supabase.table('comissoes_sienge_comissoes').select('*').eq('building_id', 2019).ilike('broker_nome', '%Helen%').execute()
print(f"Total: {len(result.data)}")
print()

for c in result.data:
    print(f"ID: {c.get('id')} - Contrato: {c.get('numero_contrato')}")
    print(f"  sienge_id: {c.get('sienge_id')}")
    print(f"  broker_nome: {c.get('broker_nome')}")
    print(f"  installment_status: {c.get('installment_status')}")
    print(f"  customer_situation_type: {c.get('customer_situation_type')}")
    print()
