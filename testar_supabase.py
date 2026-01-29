"""
Script para testar conexão com Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

print("="*60)
print("TESTE DE CONEXÃO COM SUPABASE")
print("="*60)

# Verificar variáveis de ambiente
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"\nSUPABASE_URL configurada: {'✓ Sim' if url else '✗ Não'}")
if url:
    print(f"URL: {url[:30]}...")

print(f"\nSUPABASE_KEY configurada: {'✓ Sim' if key else '✗ Não'}")
if key:
    print(f"Key (primeiros 20 caracteres): {key[:20]}...")
    print(f"Tamanho da key: {len(key)} caracteres")

if not url or not key:
    print("\n❌ ERRO: Variáveis de ambiente não configuradas!")
    print("\nVerifique se o arquivo .env existe e contém:")
    print("SUPABASE_URL=sua_url_aqui")
    print("SUPABASE_KEY=sua_chave_aqui")
    exit(1)

# Testar conexão
print("\n" + "="*60)
print("TESTANDO CONEXÃO...")
print("="*60)

try:
    supabase = create_client(url, key)
    print("✓ Cliente Supabase criado com sucesso")
    
    # Testar consulta simples
    print("\nTestando consulta na tabela 'usuarios'...")
    result = supabase.table('usuarios').select('id, username, nome_completo').limit(5).execute()
    
    if result.data:
        print(f"✓ Conexão bem-sucedida! {len(result.data)} usuário(s) encontrado(s):")
        for user in result.data:
            print(f"  - ID: {user.get('id')}, Username: {user.get('username')}, Nome: {user.get('nome_completo')}")
    else:
        print("⚠ Conexão OK, mas nenhum usuário encontrado")
    
    print("\n" + "="*60)
    print("✓ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERRO na conexão: {str(e)}")
    print("\nPossíveis causas:")
    print("1. SUPABASE_KEY está incorreta ou expirada")
    print("2. SUPABASE_URL está incorreta")
    print("3. Permissões da API key não permitem acesso à tabela")
    print("\nPara corrigir:")
    print("1. Acesse seu projeto no Supabase (https://supabase.com)")
    print("2. Vá em Settings > API")
    print("3. Copie a 'service_role' key (não a 'anon' key)")
    print("4. Atualize o arquivo .env com a chave correta")
    print("\n" + "="*60)
    exit(1)
