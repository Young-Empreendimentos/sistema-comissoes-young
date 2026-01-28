"""Script para reverter comissões ao estado Pendente - V2"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Conectar ao Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Buscar comissões que não estão pendentes
result = supabase.table('sienge_comissoes')\
    .select('id, status_aprovacao, broker_nome')\
    .neq('status_aprovacao', 'Pendente')\
    .execute()

comissoes = result.data if result.data else []

if not comissoes:
    print("OK - Todas as comissoes ja estao com status Pendente")
    sys.exit(0)

print(f"Encontradas {len(comissoes)} comissoes para reverter")

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
    except Exception as e:
        print(f"Erro: {e}")

print(f"RESULTADO: {revertidas} comissoes revertidas com sucesso")

