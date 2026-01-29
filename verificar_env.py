"""
Verifica configuração do arquivo .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("VERIFICAÇÃO DO ARQUIVO .env")
print("="*60)

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"\n1. SUPABASE_URL:")
if url:
    print(f"   ✓ Configurada: {url}")
else:
    print("   ✗ NÃO ENCONTRADA!")

print(f"\n2. SUPABASE_KEY:")
if key:
    print(f"   ✓ Configurada")
    print(f"   - Tamanho: {len(key)} caracteres")
    print(f"   - Início: {key[:30]}...")
    print(f"   - Fim: ...{key[-30:]}")
    
    # Validação básica
    if len(key) < 100:
        print(f"   ⚠ AVISO: A chave parece muito curta ({len(key)} caracteres)")
        print("   - Chaves do Supabase geralmente têm mais de 100 caracteres")
        print("   - Verifique se copiou a chave completa")
    
    if not key.startswith('eyJ'):
        print(f"   ⚠ AVISO: A chave não parece ser uma chave JWT válida")
        print("   - Chaves do Supabase geralmente começam com 'eyJ'")
        print("   - Verifique se copiou a 'service_role' key correta")
else:
    print("   ✗ NÃO ENCONTRADA!")

print("\n" + "="*60)

if not url or not key:
    print("ERRO: Arquivo .env está incompleto!")
    print("\nO arquivo .env deve conter:")
    print("SUPABASE_URL=https://seu-projeto.supabase.co")
    print("SUPABASE_KEY=eyJhbGc...")
    print("="*60)
else:
    print("Arquivo .env parece estar configurado.")
    print("Execute 'python testar_supabase.py' para testar a conexão.")
    print("="*60)
