"""
Debug: verificar campos de lote/unidade nas comissões do Sienge
"""
import os
from dotenv import load_dotenv
from sienge_client import SiengeClient

load_dotenv()

def main():
    client = SiengeClient()
    
    print("=" * 80)
    print("VERIFICANDO CAMPOS DE LOTE/UNIDADE NAS COMISSÕES")
    print("=" * 80)
    
    comissoes = client.get_commissions(limit=10)
    
    if not comissoes:
        print("Nenhuma comissão encontrada!")
        return
    
    for i, c in enumerate(comissoes[:5], 1):
        print(f"\n=== Comissão {i} ===")
        print(f"Corretor: {c.get('brokerName')}")
        print(f"Cliente: {c.get('customerName')}")
        print(f"Empreendimento: {c.get('enterpriseName')}")
        
        # Mostrar TODOS os campos que podem ser lote/unidade
        print(f"\n--- Campos de Lote/Unidade ---")
        print(f"unitName: {c.get('unitName')}")
        print(f"unit: {c.get('unit')}")
        print(f"unitId: {c.get('unitId')}")
        print(f"unitID: {c.get('unitID')}")
        print(f"salesContractNumber: {c.get('salesContractNumber')}")
        print(f"contractNumber: {c.get('contractNumber')}")
        print(f"billNumber: {c.get('billNumber')}")
        print(f"contractBillNumber: {c.get('contractBillNumber')}")
        
        print(f"\n--- Todos os campos ---")
        for key, value in sorted(c.items()):
            print(f"  {key}: {value}")
        print("-" * 80)

if __name__ == '__main__':
    main()
