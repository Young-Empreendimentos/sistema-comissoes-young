"""Script para testar se as variáveis de ambiente estão sendo carregadas"""
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Verificar variáveis SMTP
smtp_user = os.getenv('SMTP_USER')
smtp_password = os.getenv('SMTP_PASSWORD')
smtp_host = os.getenv('SMTP_HOST')
email_from = os.getenv('EMAIL_FROM')

print("=" * 50)
print("TESTE DE VARIÁVEIS DE AMBIENTE")
print("=" * 50)
print(f"SMTP_HOST: {smtp_host}")
print(f"SMTP_USER: {smtp_user}")
print(f"SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else 'NÃO DEFINIDO'}")
print(f"EMAIL_FROM: {email_from}")
print("=" * 50)

if smtp_user and smtp_password:
    print("✅ Configurações de e-mail OK!")
else:
    print("❌ Configurações de e-mail NÃO definidas!")
    print("\nVerifique se o arquivo .env existe e contém:")
    print("SMTP_USER=seu_email@gmail.com")
    print("SMTP_PASSWORD=sua_senha_de_app")

