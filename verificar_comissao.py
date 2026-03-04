"""
Verificar status de uma comissão específica
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Buscar comissão 803 ou contrato 323A
result = supabase.table('sienge_comissoes').select('*').eq('sienge_id', '803').execute()

if result.data:
    c = result.data[0]
    print("=== COMISSÃO SIENGE_ID 803 ===")
    for key, value in sorted(c.items()):
        print(f"  {key}: {value}")
else:
    print("Comissão 803 não encontrada, buscando por contrato 323A...")
    result2 = supabase.table('sienge_comissoes').select('*').eq('numero_contrato', '323A').execute()
    if result2.data:
        for c in result2.data:
            print(f"\n=== COMISSÃO ID {c.get('id')} ===")
            for key, value in sorted(c.items()):
                print(f"  {key}: {value}")
    else:
        print("Nenhuma comissão encontrada")
