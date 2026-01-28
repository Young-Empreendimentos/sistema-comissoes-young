"""Script para reverter comissões ao estado Pendente - V3"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Conectar ao Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Buscar TODAS as comissões
result = supabase.table('sienge_comissoes')\
    .select('id, status_aprovacao, broker_nome')\
    .execute()

comissoes = result.data if result.data else []

# Filtrar as que não estão com status 'Pendente'
comissoes_para_reverter = [c for c in comissoes if c.get('status_aprovacao') != 'Pendente']

with open('resultado_reversao.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total de comissoes: {len(comissoes)}\n")
    f.write(f"Comissoes para reverter: {len(comissoes_para_reverter)}\n\n")
    
    for c in comissoes_para_reverter:
        f.write(f"ID: {c['id']}, Status: {c.get('status_aprovacao')}, Corretor: {c.get('broker_nome', 'N/A')[:40]}\n")
    
    if comissoes_para_reverter:
        f.write(f"\nRevertendo {len(comissoes_para_reverter)} comissoes...\n")
        
        revertidas = 0
        for c in comissoes_para_reverter:
            try:
                supabase.table('sienge_comissoes')\
                    .update({
                        'status_aprovacao': 'Pendente',
                        'data_envio_aprovacao': None,
                        'enviado_por': None,
                        'data_aprovacao': None,
                        'aprovado_por': None,
                        'observacoes': None
                    })\
                    .eq('id', c['id'])\
                    .execute()
                revertidas += 1
                f.write(f"  OK - Comissao {c['id']} revertida\n")
            except Exception as e:
                f.write(f"  ERRO - Comissao {c['id']}: {str(e)}\n")
        
        f.write(f"\nRESULTADO: {revertidas}/{len(comissoes_para_reverter)} comissoes revertidas\n")
    else:
        f.write("\nTodas as comissoes ja estao com status 'Pendente'\n")

print("Resultado salvo em resultado_reversao.txt")

