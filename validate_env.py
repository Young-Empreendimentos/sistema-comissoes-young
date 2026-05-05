#!/usr/bin/env python3
"""
Validador de Variáveis de Ambiente - Sistema de Comissões Young
Execute antes do deploy: python validate_env.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("  VALIDAÇÃO DE VARIÁVEIS DE AMBIENTE")
print("  Sistema de Comissões - Young Empreendimentos")
print("=" * 60)
print()

# Variáveis obrigatórias com descrição
REQUIRED_VARS = {
    'SUPABASE_URL': 'URL do projeto Supabase (https://xxx.supabase.co)',
    'SUPABASE_KEY': 'Chave de API do Supabase (service_role key)',
    'SECRET_KEY': 'Chave secreta do Flask (mínimo 32 caracteres)',
    'SIENGE_USERNAME': 'Usuário da API Sienge',
    'SIENGE_PASSWORD': 'Senha da API Sienge',
}

# Variáveis opcionais (mas recomendadas)
OPTIONAL_VARS = {
    'SIENGE_BASE_URL': ('URL base da API Sienge', 'https://api.sienge.com.br/youngemp/public/api'),
    'SIENGE_COMPANY_ID': ('ID da empresa no Sienge', '5'),
    'SMTP_HOST': ('Servidor SMTP para e-mails', 'smtp.gmail.com'),
    'SMTP_PORT': ('Porta SMTP', '587'),
    'SMTP_USER': ('Usuário SMTP', None),
    'SMTP_PASSWORD': ('Senha SMTP (App Password)', None),
    'EMAIL_FROM': ('E-mail de origem', None),
    'FLASK_PORT': ('Porta do servidor', '5000'),
    'FLASK_DEBUG': ('Modo debug (False em produção)', 'False'),
    'PRODUCTION_URL': ('URL de produção para CORS', 'http://localhost:5000'),
}

errors = []
warnings = []

# Verificar obrigatórias
print("📋 Verificando variáveis OBRIGATÓRIAS:")
print("-" * 40)
for var, desc in REQUIRED_VARS.items():
    value = os.getenv(var)
    if not value:
        print(f"  ❌ {var}")
        print(f"     → {desc}")
        errors.append(var)
    else:
        # Mascarar valor sensível
        masked = value[:5] + "..." + value[-5:] if len(value) > 15 else "***"
        print(f"  ✅ {var} = {masked}")

print()

# Validações específicas
print("🔐 Verificando SEGURANÇA:")
print("-" * 40)

# SECRET_KEY
secret_key = os.getenv('SECRET_KEY', '')
if secret_key == 'young-empreendimentos-comissoes-2024':
    print("  ❌ SECRET_KEY está usando valor padrão INSEGURO!")
    print("     → Gere uma nova: python -c \"import secrets; print(secrets.token_hex(32))\"")
    errors.append('SECRET_KEY_INSECURE')
elif len(secret_key) < 32:
    print(f"  ⚠️  SECRET_KEY muito curta ({len(secret_key)} chars, recomendado: 64)")
    warnings.append('SECRET_KEY_SHORT')
else:
    print(f"  ✅ SECRET_KEY OK ({len(secret_key)} caracteres)")

# FLASK_DEBUG
flask_debug = os.getenv('FLASK_DEBUG', 'False').lower()
if flask_debug == 'true':
    print("  ⚠️  FLASK_DEBUG=True (desabilite para produção!)")
    warnings.append('DEBUG_ENABLED')
else:
    print("  ✅ FLASK_DEBUG=False (modo produção)")

# SUPABASE_KEY
supabase_key = os.getenv('SUPABASE_KEY', '')
if supabase_key and not supabase_key.startswith('eyJ'):
    print("  ⚠️  SUPABASE_KEY não parece ser uma chave JWT válida")
    warnings.append('SUPABASE_KEY_FORMAT')
elif supabase_key:
    print("  ✅ SUPABASE_KEY parece válida (formato JWT)")

print()

# Verificar opcionais
print("📝 Variáveis OPCIONAIS:")
print("-" * 40)
for var, (desc, default) in OPTIONAL_VARS.items():
    value = os.getenv(var)
    if value:
        print(f"  ✅ {var} configurada")
    elif default:
        print(f"  ℹ️  {var} usando padrão: {default}")
    else:
        print(f"  ⚠️  {var} não configurada ({desc})")
        if var in ['SMTP_USER', 'SMTP_PASSWORD']:
            warnings.append(f'{var}_MISSING')

print()

# Testar conexões (opcional)
print("🔌 Testando CONEXÕES:")
print("-" * 40)

# Testar Supabase
try:
    from supabase import create_client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if url and key:
        supabase = create_client(url, key)
        # Testar query simples
        result = supabase.table('comissoes_usuarios').select('id').limit(1).execute()
        print("  ✅ Conexão Supabase OK")
    else:
        print("  ⏭️  Supabase não testado (credenciais faltando)")
except Exception as e:
    print(f"  ❌ Erro Supabase: {str(e)[:50]}")
    errors.append('SUPABASE_CONNECTION')

# Testar Sienge
try:
    import requests
    from requests.auth import HTTPBasicAuth
    base_url = os.getenv('SIENGE_BASE_URL', 'https://api.sienge.com.br/youngemp/public/api')
    username = os.getenv('SIENGE_USERNAME')
    password = os.getenv('SIENGE_PASSWORD')
    if username and password:
        # Testar conexão
        response = requests.get(
            f"{base_url}/buildings",
            auth=HTTPBasicAuth(username, password),
            params={'companyId': os.getenv('SIENGE_COMPANY_ID', '5')},
            timeout=10
        )
        if response.status_code == 200:
            print("  ✅ Conexão Sienge OK")
        else:
            print(f"  ⚠️  Sienge respondeu com status {response.status_code}")
            warnings.append('SIENGE_STATUS')
    else:
        print("  ⏭️  Sienge não testado (credenciais faltando)")
except Exception as e:
    print(f"  ❌ Erro Sienge: {str(e)[:50]}")
    errors.append('SIENGE_CONNECTION')

print()

# Resumo
print("=" * 60)
if errors:
    print(f"❌ FALHA: {len(errors)} erro(s) encontrado(s)")
    print(f"   Erros: {', '.join(errors)}")
    print()
    print("Corrija os erros antes de fazer deploy!")
    sys.exit(1)
elif warnings:
    print(f"⚠️  ATENÇÃO: {len(warnings)} aviso(s)")
    print(f"   Avisos: {', '.join(warnings)}")
    print()
    print("Recomendado corrigir antes do deploy.")
    sys.exit(0)
else:
    print("✅ SUCESSO: Todas as validações passaram!")
    print()
    print("Pronto para deploy.")
    sys.exit(0)
