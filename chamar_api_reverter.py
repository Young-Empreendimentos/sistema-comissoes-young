"""Script para chamar a API de reverter status via requests"""
import requests

# Primeiro fazer login
session = requests.Session()

# Login
login_response = session.post(
    'http://127.0.0.1:5000/login',
    data={'username': 'antonioalves', 'password': '123456'}
)

print(f"Login: {login_response.status_code}")

# Chamar API de reverter
response = session.post('http://127.0.0.1:5000/api/comissoes/reverter-status')

print(f"Reverter: {response.status_code}")
print(f"Resposta: {response.text}")

