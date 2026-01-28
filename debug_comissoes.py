"""Script para debug dos campos de comissões"""
import os
import json
from dotenv import load_dotenv
from sienge_client import sienge_client

load_dotenv()

print("=" * 70)
print("DEBUG: CAMPOS DE COMISSÕES DA API SIENGE")
print("=" * 70)

# Buscar comissões diretamente da API
comissoes = sienge_client.get_commissions(building_id=2003, limit=5)

if comissoes:
    print(f"\nTotal retornado: {len(comissoes)}")
    
    # Mostrar todos os campos da primeira comissão
    primeira = comissoes[0]
    print("\n" + "=" * 70)
    print("CAMPOS DISPONÍVEIS NA PRIMEIRA COMISSÃO:")
    print("=" * 70)
    
    for key, value in primeira.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("VERIFICANDO CAMPOS DE VALOR:")
    print("=" * 70)
    
    campos_valor = ['commissionValue', 'installmentValue', 'value', 'totalValue', 
                    'netValue', 'grossValue', 'amount', 'commission_value']
    
    for campo in campos_valor:
        valor = primeira.get(campo)
        print(f"  {campo}: {valor}")
        
else:
    print("Nenhuma comissão retornada da API")

