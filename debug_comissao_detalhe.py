"""
Debug - testar endpoint de detalhes de uma comissão específica
"""
import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

base_url = os.getenv('SIENGE_BASE_URL', 'https://api.sienge.com.br/youngemp/public/api/v1')
username = os.getenv('SIENGE_USERNAME')
password = os.getenv('SIENGE_PASSWORD')
auth = HTTPBasicAuth(username, password)

print("=" * 70)
print("TESTANDO ENDPOINTS DE COMISSÃO")
print("=" * 70)

# Testar endpoint de detalhes de uma comissão específica
commission_id = 876  # Comissão do contrato 161

# Tentar GET /commissions/{id}
print(f"\n1. Testando GET /commissions/{commission_id}...")
try:
    url = f"{base_url}/commissions/{commission_id}"
    response = requests.get(url, auth=auth, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("   Campos retornados:")
        for key in sorted(data.keys()):
            print(f"     {key}: {data[key]}")
    else:
        print(f"   Erro: {response.text[:200]}")
except Exception as e:
    print(f"   Exceção: {e}")

# Testar listagem com expand ou campos adicionais
print(f"\n2. Testando GET /commissions com parâmetros extras...")
try:
    url = f"{base_url}/commissions"
    params = {
        'companyId': '5',
        'limit': 1,
        'expand': 'all'  # Tentar expandir todos os campos
    }
    response = requests.get(url, auth=auth, params=params, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            print("   Campos da primeira comissão:")
            for key in sorted(data['results'][0].keys()):
                print(f"     {key}: {data['results'][0][key]}")
except Exception as e:
    print(f"   Exceção: {e}")

# Testar com fields parameter
print(f"\n3. Testando GET /commissions com fields=baseValue...")
try:
    url = f"{base_url}/commissions"
    params = {
        'companyId': '5',
        'limit': 1,
        'fields': 'baseValue,value,installmentPercentage'
    }
    response = requests.get(url, auth=auth, params=params, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            print("   Campos retornados:")
            for key in sorted(data['results'][0].keys()):
                print(f"     {key}: {data['results'][0][key]}")
except Exception as e:
    print(f"   Exceção: {e}")
