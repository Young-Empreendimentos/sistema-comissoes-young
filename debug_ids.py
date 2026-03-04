"""
Debug: comparar IDs do Supabase com IDs da API
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from sienge_client import sienge_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def main():
    # Buscar um registro errado do Supabase
    result = supabase.table('sienge_comissoes').select('*').eq('id', 878).execute()
    
    if result.data:
        reg = result.data[0]
        print("=== REGISTRO NO SUPABASE (ID 878) ===")
        print(f"sienge_id: {reg.get('sienge_id')}")
        print(f"broker_nome: {reg.get('broker_nome')}")
        print(f"unit_name: {reg.get('unit_name')}")
        print(f"numero_contrato: {reg.get('numero_contrato')}")
        print(f"enterprise_name: {reg.get('enterprise_name')}")
        print(f"customer_name: {reg.get('customer_name')}")
        print(f"commission_value: {reg.get('commission_value')}")
    
    # Buscar na API pelo mesmo corretor/empreendimento
    print("\n=== COMISSÕES DA API (Aurora, Carolini) ===")
    comissoes = sienge_client.get_commissions(limit=50)
    
    for c in comissoes:
        if 'Carolini' in (c.get('brokerName') or ''):
            print(f"\ncommissionID: {c.get('commissionID')}")
            print(f"brokerName: {c.get('brokerName')}")
            print(f"unitName: {c.get('unitName')}")
            print(f"salesContractNumber: {c.get('salesContractNumber')}")
            print(f"billNumber: {c.get('billNumber')}")
            print(f"value: {c.get('value')}")

if __name__ == '__main__':
    main()
