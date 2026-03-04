"""
Debug - verificar detalhes do contrato do Victor Bortoluzzi na API
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
print("BUSCANDO DETALHES DO CONTRATO")
print("=" * 70)

# Primeiro buscar a comissão do Victor
commissions = sienge_client.get_commissions_all_companies()

for c in commissions:
    if 'VICTOR' in (c.get('brokerName') or '').upper() and 'BORTOLUZZI' in (c.get('brokerName') or '').upper():
        print(f"\nComissão encontrada:")
        print(f"  Contrato: {c.get('salesContractNumber')}")
        print(f"  contractBillNumber: {c.get('contractBillNumber')}")
        print(f"  enterpriseID: {c.get('enterpriseID')}")
        print(f"  companyId: {c.get('companyId')}")
        
        # Buscar detalhes do contrato
        sienge_client.company_id = str(c.get('companyId'))
        
        # Tentar buscar o contrato
        print(f"\n  Buscando contrato {c.get('contractBillNumber')}...")
        contract = sienge_client.get_contract_details(c.get('contractBillNumber'))
        
        if contract:
            print("\n  DETALHES DO CONTRATO:")
            print("-" * 70)
            print(json.dumps(contract, indent=2, default=str))
        else:
            print("  Contrato não encontrado")
        
        break
