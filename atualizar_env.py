"""
Script para atualizar o arquivo .env com a chave correta
"""
import os

# Ler o arquivo .env atual
env_path = '.env'
linhas = []

if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

# Nova chave
nova_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZoYWhhZWJ0enRub25maXRobGd5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODIyNjMzMSwiZXhwIjoyMDgzODAyMzMxfQ.3HztCotTHrWYjjPUndWp0EIe1WJ6R9rr2nD7fBHIVdY"

# Atualizar ou adicionar SUPABASE_KEY
key_atualizada = False
novas_linhas = []

for linha in linhas:
    if linha.startswith('SUPABASE_KEY='):
        novas_linhas.append(f'SUPABASE_KEY={nova_key}\n')
        key_atualizada = True
        print(f"✓ SUPABASE_KEY atualizada")
    else:
        novas_linhas.append(linha)

# Se não encontrou, adicionar no final
if not key_atualizada:
    novas_linhas.append(f'SUPABASE_KEY={nova_key}\n')
    print(f"✓ SUPABASE_KEY adicionada")

# Salvar arquivo
with open(env_path, 'w', encoding='utf-8') as f:
    f.writelines(novas_linhas)

print("\n" + "="*60)
print("✓ Arquivo .env atualizado com sucesso!")
print("="*60)
print("\nPróximos passos:")
print("1. Execute: python testar_supabase.py")
print("2. Se o teste passar, reinicie o servidor")
print("="*60)
