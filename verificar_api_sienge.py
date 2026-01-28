"""Script para verificar os campos da API do Sienge"""
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

# Configurações
base_url = os.getenv('SIENGE_BASE_URL')
username = os.getenv('SIENGE_USERNAME')
password = os.getenv('SIENGE_PASSWORD')
company_id = os.getenv('SIENGE_COMPANY_ID')

print("=" * 70)
print("VERIFICANDO API DO SIENGE")
print("=" * 70)
print(f"URL Base: {base_url}")
print(f"Usuario: {username}")
print(f"Company ID: {company_id}")

# Testar endpoint de comissões
url = f"{base_url}/broker-commissions"
params = {
    'companyId': company_id,
    'limit': 3
}

print(f"\nURL: {url}")
print(f"Params: {params}")

try:
    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(username, password),
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nResposta:")
        
        if 'results' in data:
            results = data['results']
            print(f"Total de resultados: {len(results)}")
            
            if results:
                print("\n" + "=" * 70)
                print("CAMPOS DO PRIMEIRO RESULTADO:")
                print("=" * 70)
                
                for key, value in results[0].items():
                    print(f"  {key}: {value}")
        else:
            print(f"Dados: {data}")
    else:
        print(f"Erro: {response.text}")
        
except Exception as e:
    print(f"Erro: {str(e)}")

