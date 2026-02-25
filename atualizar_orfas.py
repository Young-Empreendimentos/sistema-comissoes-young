"""
Script para identificar e atualizar comissões órfãs
(que estão no banco mas não estão mais na API do Sienge)
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from supabase import create_client
from sienge_client import sienge_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def main():
    print("=" * 70)
    print("IDENTIFICANDO COMISSÕES ÓRFÃS")
    print("=" * 70)
    
    # 1. Buscar todas as comissões da API do Sienge
    print("\n[1/3] Buscando comissões da API do Sienge...")
    comissoes_api = sienge_client.get_commissions_all_companies()
    
    # Criar set de IDs da API
    ids_api = set()
    for c in comissoes_api:
        sienge_id = c.get('commissionID') or c.get('id')
        if sienge_id:
            ids_api.add(str(sienge_id))
    
    print(f"      {len(ids_api)} IDs únicos na API")
    
    # 2. Buscar todas as comissões do banco
    print("\n[2/3] Buscando comissões do Supabase...")
    result = supabase.table('sienge_comissoes').select('id, sienge_id, broker_nome, numero_contrato, enterprise_name, installment_status').execute()
    
    comissoes_banco = result.data or []
    print(f"      {len(comissoes_banco)} comissões no banco")
    
    # 3. Identificar órfãs
    print("\n[3/3] Identificando e atualizando órfãs...")
    orfas = []
    
    for c in comissoes_banco:
        sienge_id = str(c.get('sienge_id'))
        if sienge_id not in ids_api:
            orfas.append(c)
    
    print(f"\n      {len(orfas)} comissões órfãs encontradas")
    
    if not orfas:
        print("\nNenhuma comissão órfã!")
        return
    
    # Mostrar detalhes e atualizar
    print("\n" + "-" * 70)
    print("COMISSÕES ÓRFÃS (não existem mais na API):")
    print("-" * 70)
    
    atualizadas = 0
    erros = 0
    
    for c in orfas:
        status_atual = c.get('installment_status')
        print(f"  ID {c.get('id')} | Sienge {c.get('sienge_id')} | {c.get('broker_nome')} | {c.get('numero_contrato')} | {c.get('enterprise_name')} | Status: {status_atual}")
        
        # Se não está cancelada, marcar como cancelada
        if status_atual != 'CANCELLED':
            try:
                supabase.table('sienge_comissoes').update({
                    'installment_status': 'CANCELLED',
                    'atualizado_em': datetime.now().isoformat()
                }).eq('id', c['id']).execute()
                print(f"      -> Marcada como CANCELLED")
                atualizadas += 1
            except Exception as e:
                print(f"      -> ERRO: {str(e)[:50]}")
                erros += 1
    
    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"Total de órfãs: {len(orfas)}")
    print(f"Atualizadas para CANCELLED: {atualizadas}")
    print(f"Já estavam canceladas: {len(orfas) - atualizadas - erros}")
    print(f"Erros: {erros}")
    print("=" * 70)

if __name__ == '__main__':
    main()
