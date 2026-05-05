"""
Script para adicionar coluna updated_at nas tabelas do Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

print("=" * 60)
print("ADICIONANDO COLUNA updated_at NAS TABELAS")
print("=" * 60)
print()

tabelas = [
    'comissoes_sienge_contratos',
    'comissoes_sienge_comissoes',
    'comissoes_sienge_itbi',
    'comissoes_sienge_valor_pago',
    'comissoes_sienge_empreendimentos',
    'comissoes_sienge_corretores',
    'comissoes_log_sincronizacoes',
    'comissoes_usuarios',
    'comissoes_regras_gatilho',
    'comissoes_configuracoes_emails',
    'comissoes_lotes_aprovacao',
    'comissoes_historico_aprovacoes',
]

for tabela in tabelas:
    try:
        sql = f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();"
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print(f"✓ {tabela}: coluna updated_at adicionada")
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
            print(f"✓ {tabela}: coluna já existe")
        elif 'does not exist' in error_msg.lower() or 'relation' in error_msg.lower():
            print(f"- {tabela}: tabela não existe (ignorado)")
        else:
            print(f"✗ {tabela}: {error_msg[:80]}")

print()
print("Processo concluído!")
