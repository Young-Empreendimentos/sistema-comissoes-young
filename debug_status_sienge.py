"""
Script para debug: verificar o que vem no campo installmentStatus da API Sienge
"""
import os
from dotenv import load_dotenv
from sienge_client import SiengeClient

load_dotenv()

def main():
    client = SiengeClient()
    
    print("=" * 80)
    print("VERIFICANDO CAMPOS DE STATUS NAS COMISSÕES DO SIENGE")
    print("=" * 80)
    
    # Buscar algumas comissões
    comissoes = client.get_commissions(limit=20)
    
    if not comissoes:
        print("Nenhuma comissão encontrada!")
        return
    
    print(f"\nTotal de comissões retornadas: {len(comissoes)}")
    print("\n" + "-" * 80)
    
    for i, c in enumerate(comissoes[:10], 1):
        print(f"\n=== Comissão {i} ===")
        print(f"ID: {c.get('id')}")
        print(f"Contrato: {c.get('contractNumber')}")
        print(f"Corretor: {c.get('brokerName')}")
        print(f"Cliente: {c.get('customerName')}")
        print(f"Empreendimento: {c.get('enterpriseName') or c.get('buildingName')}")
        print(f"Unidade: {c.get('unitName')}")
        print(f"Valor: {c.get('commissionValue') or c.get('value')}")
        
        # Mostrar TODOS os campos relacionados a status
        print(f"\n--- Campos de Status ---")
        print(f"installmentStatus: {c.get('installmentStatus')}")
        print(f"status: {c.get('status')}")
        print(f"paymentStatus: {c.get('paymentStatus')}")
        print(f"situacao: {c.get('situacao')}")
        
        # Mostrar todos os campos que contém 'status' no nome
        print(f"\n--- Todos os campos da comissão ---")
        for key, value in sorted(c.items()):
            print(f"  {key}: {value}")
        
        print("-" * 80)
    
    # Mostrar estatísticas de status
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS DE STATUS")
    print("=" * 80)
    
    status_count = {}
    for c in comissoes:
        status = c.get('installmentStatus') or c.get('status') or 'N/A'
        status_count[status] = status_count.get(status, 0) + 1
    
    print("\nContagem por installmentStatus/status:")
    for status, count in sorted(status_count.items()):
        print(f"  {status}: {count}")

if __name__ == '__main__':
    main()
