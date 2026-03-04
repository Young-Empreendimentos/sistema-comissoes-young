"""
Debug - buscar contrato pelo número
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
print("BUSCANDO CONTRATO PELO NÚMERO")
print("=" * 70)

# Buscar todos os contratos da empresa 10
sienge_client.company_id = '10'

print("\nBuscando contratos da empresa 10...")
contracts = sienge_client.get_all_contracts_paginated()
print(f"Encontrados {len(contracts)} contratos")

# Buscar contrato 227
for ct in contracts:
    if str(ct.get('number')) == '227':
        print("\nContrato 227 encontrado:")
        print(json.dumps(ct, indent=2, default=str))
        
        # Buscar detalhes completos
        contract_id = ct.get('id')
        if contract_id:
            print(f"\nBuscando detalhes do contrato ID {contract_id}...")
            details = sienge_client.get_contract_details(contract_id)
            if details:
                print("\nDETALHES COMPLETOS:")
                print(json.dumps(details, indent=2, default=str))
        break
