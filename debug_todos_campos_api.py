"""
Debug - mostrar TODOS os campos da API de comissões do Sienge
"""
import os
import sys
import json
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from sienge_client import sienge_client

print("=" * 70)
print("TODOS OS CAMPOS DA API DE COMISSÕES")
print("=" * 70)

commissions = sienge_client.get_commissions_all_companies()

# Encontrar a comissão do Victor Bortoluzzi (do print do usuário)
for c in commissions:
    if 'VICTOR' in (c.get('brokerName') or '').upper() or 'BORTOLUZZI' in (c.get('brokerName') or '').upper():
        print(f"\nComissão de {c.get('brokerName')}:")
        print("-" * 70)
        print(json.dumps(c, indent=2, default=str))
        break

# Mostrar os primeiros 3 como exemplo
print("\n\nPrimeiras 3 comissões (JSON completo):")
for i, c in enumerate(commissions[:3]):
    print(f"\n--- Comissão {i+1} ---")
    print(json.dumps(c, indent=2, default=str))
