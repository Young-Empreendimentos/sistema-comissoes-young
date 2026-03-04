from sienge_client import sienge_client

# Testar busca de contratos
contracts = sienge_client.get_contracts(limit=2)
print(f"Contratos encontrados: {len(contracts)}")

if contracts:
    c = contracts[0]
    print(f"Numero: {c.get('number')}")
    print(f"Enterprise ID: {c.get('enterpriseId')}")
    
    # Testar extração de ITBI
    itbi = sienge_client.extract_itbi_from_contract(c)
    print(f"ITBI: {itbi}")
    
    # Testar extração de valor pago
    valor_pago = sienge_client.extract_valor_pago_from_contract(c)
    print(f"Valor Pago Total: {valor_pago}")
