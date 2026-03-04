"""
Debug - calcular valor base a partir da comissão e percentual
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from sienge_client import sienge_client

print("=" * 70)
print("CALCULANDO VALOR BASE DO CONTRATO")
print("=" * 70)

commissions = sienge_client.get_commissions_all_companies()

print("\nExemplos de comissões com cálculo do valor base:")
print("-" * 70)

for c in commissions[:10]:
    valor_comissao = c.get('value') or 0
    percentual = c.get('installmentPercentage') or 0
    
    # Calcular valor base: valor_comissao / (percentual / 100)
    if percentual > 0:
        valor_base_calculado = valor_comissao / (percentual / 100)
    else:
        valor_base_calculado = 0
    
    print(f"  Contrato: {c.get('salesContractNumber')}")
    print(f"    Valor Comissão: R$ {valor_comissao:,.2f}")
    print(f"    Percentual: {percentual}%")
    print(f"    Valor Base Calculado: R$ {valor_base_calculado:,.2f}")
    print()
