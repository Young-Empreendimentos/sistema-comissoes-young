"""Script para verificar os dados no Supabase"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Conectar ao Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

print("=" * 70)
print("VERIFICANDO DADOS NO SUPABASE")
print("=" * 70)

# Buscar algumas comissões
result = supabase.table('sienge_comissoes').select('*').limit(5).execute()

if result.data:
    print(f"\nTotal de registros retornados: {len(result.data)}")
    
    for i, c in enumerate(result.data):
        print(f"\n--- Comissão {i+1} ---")
        for key, value in c.items():
            print(f"  {key}: {value}")
else:
    print("Nenhum registro encontrado")

# Verificar se há algum registro com commission_value preenchido
print("\n" + "=" * 70)
print("VERIFICANDO REGISTROS COM commission_value PREENCHIDO")
print("=" * 70)

result2 = supabase.table('sienge_comissoes')\
    .select('id, broker_nome, commission_value')\
    .not_.is_('commission_value', 'null')\
    .limit(5)\
    .execute()

if result2.data:
    print(f"Encontrados {len(result2.data)} registros com commission_value preenchido")
    for c in result2.data:
        print(f"  ID: {c.get('id')}, Valor: {c.get('commission_value')}, Corretor: {c.get('broker_nome')}")
else:
    print("Nenhum registro com commission_value preenchido encontrado")

