"""Script para reverter comissões ao estado Pendente"""
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
print("REVERTENDO COMISSÕES PARA STATUS PENDENTE")
print("=" * 70)

# Buscar comissões que não estão pendentes
result = supabase.table('sienge_comissoes')\
    .select('id, status_aprovacao, broker_nome')\
    .neq('status_aprovacao', 'Pendente')\
    .execute()

comissoes = result.data if result.data else []
print(f"\nEncontradas {len(comissoes)} comissões para reverter:")

for c in comissoes:
    print(f"  - ID: {c['id']}, Status: {c.get('status_aprovacao')}, Corretor: {c.get('broker_nome', 'N/A')[:40]}")

if comissoes:
    print(f"\nRevertendo {len(comissoes)} comissões...")
    
    revertidas = 0
    for c in comissoes:
        try:
            supabase.table('sienge_comissoes')\
                .update({
                    'status_aprovacao': 'Pendente',
                    'data_envio_aprovacao': None,
                    'enviado_por': None,
                    'data_aprovacao': None,
                    'aprovado_por': None,
                    'observacoes': None
                })\
                .eq('id', c['id'])\
                .execute()
            revertidas += 1
            print(f"  ✓ Comissão {c['id']} revertida")
        except Exception as e:
            print(f"  ✗ Erro ao reverter {c['id']}: {str(e)}")
    
    print(f"\n{'=' * 70}")
    print(f"RESULTADO: {revertidas}/{len(comissoes)} comissões revertidas com sucesso!")
    print("=" * 70)
else:
    print("\nNenhuma comissão precisa ser revertida. Todas já estão com status 'Pendente'.")

