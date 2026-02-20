"""Script para testar busca de corretores no Supabase"""
from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Testar busca por CPF específico
cpf_teste = "99416549053"  # CPF do Pablo sem formatação
print(f'=== TESTANDO BUSCA POR CPF: {cpf_teste} ===')

result = supabase.table('sienge_corretores').select('sienge_id, cpf, cnpj, nome').execute()

encontrado = None
for c in (result.data or []):
    cpf_banco = (c.get('cpf') or '').replace('.', '').replace('-', '').replace('/', '').strip()
    cnpj_banco = (c.get('cnpj') or '').replace('.', '').replace('-', '').replace('/', '').strip()
    
    print(f"Comparando: '{cpf_banco}' == '{cpf_teste}' ? {cpf_banco == cpf_teste}")
    
    if cpf_banco == cpf_teste or cnpj_banco == cpf_teste:
        encontrado = c
        break

if encontrado:
    print(f"\nCORRETOR ENCONTRADO!")
    print(f"  Nome: {encontrado.get('nome')}")
    print(f"  CPF original: {encontrado.get('cpf')}")
    print(f"  sienge_id: {encontrado.get('sienge_id')}")
else:
    print("\nCORRETOR NAO ENCONTRADO!")
    
# Mostrar alguns CPFs para referência
print('\n=== PRIMEIROS 5 CPFs PARA REFERENCIA ===')
for c in (result.data or [])[:5]:
    cpf = c.get('cpf') or '-'
    cpf_limpo = cpf.replace('.', '').replace('-', '').strip() if cpf != '-' else '-'
    print(f"  Original: '{cpf}' | Limpo: '{cpf_limpo}'")
