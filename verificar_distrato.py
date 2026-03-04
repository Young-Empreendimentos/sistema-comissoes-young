"""
Verificar campos de distrato nas comissões do Sienge
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from sienge_client import sienge_client

print("=" * 80)
print("VERIFICANDO CAMPOS DE DISTRATO NAS COMISSÕES DO SIENGE")
print("=" * 80)

# Buscar comissões
comissoes = sienge_client.get_commissions(limit=50)

print(f"\nTotal de comissões retornadas: {len(comissoes)}")

# Procurar campos que podem indicar distrato
print("\n--- Procurando campos relacionados a distrato/situação ---")

for i, c in enumerate(comissoes[:10], 1):
    print(f"\n=== Comissão {i} (ID {c.get('commissionID')}) ===")
    print(f"Cliente: {c.get('customerName')}")
    print(f"Contrato: {c.get('salesContractNumber')}")
    print(f"Status Parcela: {c.get('installmentStatus')}")
    print(f"customerSituationType: {c.get('customerSituationType')}")
    
    # Mostrar todos os campos
    print("\nTodos os campos:")
    for key, value in sorted(c.items()):
        if value is not None:
            print(f"  {key}: {value}")

# Verificar especificamente os que têm customerSituationType diferente
print("\n\n" + "=" * 80)
print("TIPOS DE customerSituationType ENCONTRADOS:")
print("=" * 80)

tipos = {}
for c in comissoes:
    tipo = c.get('customerSituationType') or 'N/A'
    if tipo not in tipos:
        tipos[tipo] = []
    tipos[tipo].append({
        'id': c.get('commissionID'),
        'cliente': c.get('customerName'),
        'contrato': c.get('salesContractNumber'),
        'status': c.get('installmentStatus')
    })

for tipo, lista in tipos.items():
    print(f"\n{tipo}: {len(lista)} comissões")
    for item in lista[:3]:
        print(f"  ID {item['id']} | {item['cliente']} | Contrato {item['contrato']} | {item['status']}")
