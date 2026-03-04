"""
Verificar se commissionID 749 existe na API do Sienge
"""
import os
from dotenv import load_dotenv
from sienge_client import sienge_client

load_dotenv()

print("Buscando comissões da empresa 4 (Ilha dos Açores)...")
sienge_client.company_id = '4'
comissoes = sienge_client.get_all_commissions_paginated()

print(f"Total: {len(comissoes)} comissões")

# Procurar IDs 749, 750, 803
ids_busca = [749, 750, 803]

print("\nProcurando IDs 749, 750, 803:")
for c in comissoes:
    cid = c.get('commissionID')
    if cid in ids_busca:
        print(f"\n  ID {cid} encontrado!")
        print(f"    Cliente: {c.get('customerName')}")
        print(f"    Contrato: {c.get('salesContractNumber')}")
        print(f"    Lote: {c.get('unitName')}")
        print(f"    Status: {c.get('installmentStatus')}")

print("\n\nComissões do contrato 323A:")
for c in comissoes:
    if '323' in str(c.get('salesContractNumber', '')):
        print(f"\n  ID {c.get('commissionID')}")
        print(f"    Cliente: {c.get('customerName')}")
        print(f"    Contrato: {c.get('salesContractNumber')}")
        print(f"    Lote: {c.get('unitName')}")
        print(f"    Status: {c.get('installmentStatus')}")
