"""
Script para rodar a sincronização do baseValue
"""
import os
import sys
import time
from datetime import datetime

# Mudar para o diretório do projeto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
from sienge_client import sienge_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 60)
print("SINCRONIZAÇÃO DE BASE VALUE (VALOR À VISTA)")
print("=" * 60)

# Buscar todas as comissões do banco
print("\n[1/2] Buscando comissões...")
result = supabase.table('sienge_comissoes').select('id,sienge_id,numero_contrato,broker_nome').execute()

comissoes = result.data or []
print(f"      {len(comissoes)} comissões encontradas")

# Para cada comissão, buscar o detalhe e pegar o baseValue
print("\n[2/2] Buscando baseValue de cada comissão...")

atualizados = 0
erros = 0

for i, c in enumerate(comissoes):
    sienge_id = c.get('sienge_id')
    if not sienge_id:
        continue
    
    try:
        # Buscar detalhes da comissão
        detalhe = sienge_client.get_commission_details(int(sienge_id))
        
        if detalhe and 'baseValue' in detalhe:
            base_value = detalhe.get('baseValue')
            
            # Atualizar no banco
            supabase.table('sienge_comissoes').update({
                'valor_comissao': base_value,
                'atualizado_em': datetime.now().isoformat()
            }).eq('id', c['id']).execute()
            
            atualizados += 1
            
            if atualizados % 50 == 0:
                print(f"      Progresso: {atualizados}/{len(comissoes)} atualizados")
        else:
            erros += 1
            if erros <= 5:
                print(f"      [AVISO] Comissão {sienge_id} - baseValue não encontrado")
        
        # Pequeno delay para não sobrecarregar a API
        if i % 10 == 0:
            time.sleep(0.2)
            
    except Exception as e:
        erros += 1
        if erros <= 10:
            print(f"      [ERRO] ID {sienge_id}: {str(e)[:60]}")

print("\n" + "=" * 60)
print("RESULTADO")
print("=" * 60)
print(f"Total processado: {len(comissoes)}")
print(f"Atualizados:      {atualizados}")
print(f"Erros/Avisos:     {erros}")
print("=" * 60)
