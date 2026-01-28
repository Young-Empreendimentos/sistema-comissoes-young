"""Script para investigar os campos retornados pela API de comissões do Sienge"""
import os
import json
from dotenv import load_dotenv
from sienge_client import sienge_client
from supabase import create_client

load_dotenv()

# Conectar ao Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

print("=" * 60)
print("INVESTIGAÇÃO DOS CAMPOS DE COMISSÕES")
print("=" * 60)

# 1. Buscar comissões da API do Sienge
print("\n1. DADOS DA API DO SIENGE:")
print("-" * 40)
comissoes_sienge = sienge_client.get_commissions(building_id=2003, limit=3)
if comissoes_sienge:
    print(f"Total de comissões retornadas: {len(comissoes_sienge)}")
    print("\nExemplo de comissão (primeira):")
    print(json.dumps(comissoes_sienge[0], indent=2, default=str))
    
    print("\n\nCAMPOS DISPONÍVEIS NA API:")
    for key in comissoes_sienge[0].keys():
        print(f"  - {key}: {comissoes_sienge[0].get(key)}")
else:
    print("Nenhuma comissão retornada da API")

# 2. Buscar comissões do Supabase
print("\n\n2. DADOS DO SUPABASE:")
print("-" * 40)
result = supabase.table('sienge_comissoes').select('*').limit(3).execute()
if result.data:
    print(f"Total de comissões no banco: {len(result.data)}")
    print("\nExemplo de comissão (primeira):")
    print(json.dumps(result.data[0], indent=2, default=str))
    
    print("\n\nCAMPOS DISPONÍVEIS NO SUPABASE:")
    for key in result.data[0].keys():
        valor = result.data[0].get(key)
        print(f"  - {key}: {valor}")
else:
    print("Nenhuma comissão no banco")

# 3. Verificar se commission_value está preenchido
print("\n\n3. VERIFICAÇÃO DO CAMPO commission_value:")
print("-" * 40)
result_values = supabase.table('sienge_comissoes').select('id, commission_value, broker_nome, enterprise_name').limit(10).execute()
if result_values.data:
    for c in result_values.data:
        valor = c.get('commission_value')
        print(f"ID: {c.get('id')}, Valor: {valor}, Corretor: {c.get('broker_nome')[:30] if c.get('broker_nome') else 'N/A'}")

