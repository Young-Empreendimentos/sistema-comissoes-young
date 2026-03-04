"""
Verificar contratos que têm múltiplas comissões com status diferentes
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 80)
print("VERIFICANDO CONTRATOS COM MÚLTIPLAS COMISSÕES")
print("=" * 80)

# Buscar todas as comissões
result = supabase.table('sienge_comissoes').select('id, sienge_id, numero_contrato, unit_name, enterprise_name, broker_nome, customer_name, installment_status, commission_value').execute()

comissoes = result.data or []
print(f"\nTotal de comissões no banco: {len(comissoes)}")

# Agrupar por contrato + empreendimento
grupos = {}
for c in comissoes:
    chave = f"{c.get('numero_contrato')}_{c.get('enterprise_name')}"
    if chave not in grupos:
        grupos[chave] = []
    grupos[chave].append(c)

# Encontrar grupos com múltiplas comissões e status diferentes
print("\n" + "-" * 80)
print("CONTRATOS COM MÚLTIPLAS COMISSÕES (possíveis duplicatas):")
print("-" * 80)

problemas = []
for chave, lista in grupos.items():
    if len(lista) > 1:
        # Verificar se têm status diferentes
        status_set = set(c.get('installment_status') for c in lista)
        
        # Se tem cancelado e não cancelado no mesmo contrato
        tem_cancelado = any('CANCEL' in (c.get('installment_status') or '').upper() for c in lista)
        tem_nao_cancelado = any('CANCEL' not in (c.get('installment_status') or '').upper() for c in lista)
        
        if tem_cancelado and tem_nao_cancelado:
            problemas.append({
                'chave': chave,
                'comissoes': lista,
                'status': status_set
            })

print(f"\nEncontrados {len(problemas)} contratos com comissões canceladas E não canceladas:")

for p in problemas:
    print(f"\n=== {p['chave']} ===")
    for c in p['comissoes']:
        status = c.get('installment_status') or 'N/A'
        cancelada = '(CANCELADA)' if 'CANCEL' in status.upper() else ''
        print(f"  ID {c.get('id')} | Sienge {c.get('sienge_id')} | {c.get('broker_nome')} | R$ {c.get('commission_value')} | {status} {cancelada}")

# Mostrar também contratos duplicados (mesmo contrato, múltiplos registros)
print("\n\n" + "=" * 80)
print("TODOS OS CONTRATOS DUPLICADOS (mais de 1 registro por contrato):")
print("=" * 80)

duplicados_count = 0
for chave, lista in sorted(grupos.items(), key=lambda x: -len(x[1])):
    if len(lista) > 1:
        duplicados_count += 1
        if duplicados_count <= 20:  # Mostrar apenas os primeiros 20
            print(f"\n{chave}: {len(lista)} registros")
            for c in lista:
                status = c.get('installment_status') or 'N/A'
                print(f"  ID {c.get('id')} | Sienge {c.get('sienge_id')} | {status} | R$ {c.get('commission_value')}")

print(f"\n\nTotal de contratos duplicados: {duplicados_count}")
