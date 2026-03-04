"""
Debug - verificar todos os campos de uma comissão na API do Sienge
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
print("CAMPOS DISPONÍVEIS NA API DE COMISSÕES DO SIENGE")
print("=" * 70)

# Buscar comissões
commissions = sienge_client.get_commissions_all_companies()

if commissions:
    # Pegar a primeira comissão como exemplo
    c = commissions[0]
    
    print(f"\nExemplo de comissão (ID {c.get('commissionID')}):")
    print("-" * 70)
    
    # Mostrar todos os campos
    for key, value in sorted(c.items()):
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("CAMPOS QUE PODEM SER 'VALOR BASE DO CONTRATO':")
    print("=" * 70)
    
    # Procurar campos que podem ser o valor base
    for key, value in c.items():
        key_lower = key.lower()
        if any(x in key_lower for x in ['value', 'valor', 'base', 'contract', 'contrato', 'total', 'amount']):
            print(f"  {key}: {value}")
