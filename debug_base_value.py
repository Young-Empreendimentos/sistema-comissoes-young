"""
Debug - verificar se o campo baseValue existe na API de comissões
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
print("VERIFICANDO CAMPO baseValue NA API DE COMISSÕES")
print("=" * 70)

commissions = sienge_client.get_commissions_all_companies()

# Mostrar todos os campos de algumas comissões
print("\nPrimeiras 3 comissões (todos os campos):")
for i, c in enumerate(commissions[:3]):
    print(f"\n--- Comissão {i+1} (ID {c.get('commissionID')}) ---")
    for key in sorted(c.keys()):
        print(f"  {key}: {c[key]}")

# Verificar se baseValue existe
print("\n" + "=" * 70)
print("PROCURANDO CAMPO baseValue ou similar:")
print("=" * 70)

campos_encontrados = set()
for c in commissions:
    for key in c.keys():
        if 'base' in key.lower() or 'value' in key.lower():
            campos_encontrados.add(key)

print(f"\nCampos com 'base' ou 'value' no nome:")
for campo in sorted(campos_encontrados):
    exemplo = commissions[0].get(campo)
    print(f"  {campo}: {exemplo}")
