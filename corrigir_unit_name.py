"""
Script para corrigir os unit_name errados no Supabase
Busca o unitName correto da API do Sienge e atualiza os registros
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
    print("CORRIGINDO unit_name NO SUPABASE")
    print("=" * 70)
    
    # 1. Buscar todas as comissões da API do Sienge
    print("\n[1/3] Buscando comissões da API do Sienge...")
    comissoes_api = sienge_client.get_commissions_all_companies()
    print(f"      {len(comissoes_api)} comissões encontradas na API")
    
    # Criar mapa sienge_id -> unitName
    mapa_unit_name = {}
    for c in comissoes_api:
        sienge_id = c.get('commissionID') or c.get('id')
        unit_name = c.get('unitName')
        if sienge_id and unit_name:
            mapa_unit_name[str(sienge_id)] = unit_name
    
    print(f"      {len(mapa_unit_name)} comissões com unitName mapeadas")
    
    # 2. Buscar registros no Supabase que precisam correção
    print("\n[2/3] Buscando registros no Supabase...")
    result = supabase.table('sienge_comissoes').select('id, sienge_id, unit_name').execute()
    
    registros = result.data or []
    print(f"      {len(registros)} registros no banco")
    
    # 3. Corrigir registros
    print("\n[3/3] Corrigindo registros...")
    corrigidos = 0
    erros = 0
    
    for reg in registros:
        sienge_id = str(reg.get('sienge_id'))
        unit_name_atual = reg.get('unit_name')
        unit_name_correto = mapa_unit_name.get(sienge_id)
        
        if not unit_name_correto:
            continue
        
        # Verificar se precisa correção
        precisa_corrigir = False
        
        # Se unit_name está vazio
        if not unit_name_atual:
            precisa_corrigir = True
        # Se unit_name é um número > 1000 (provavelmente billNumber errado)
        elif unit_name_atual:
            try:
                if int(unit_name_atual) > 1000:
                    precisa_corrigir = True
            except:
                pass
        
        if precisa_corrigir:
            try:
                supabase.table('sienge_comissoes').update({
                    'unit_name': unit_name_correto,
                    'atualizado_em': datetime.now().isoformat()
                }).eq('id', reg['id']).execute()
                
                print(f"  [OK] ID {reg['id']} (Sienge {sienge_id}): '{unit_name_atual}' -> '{unit_name_correto}'")
                corrigidos += 1
            except Exception as e:
                print(f"  [ERRO] ID {reg['id']}: {str(e)[:50]}")
                erros += 1
    
    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"Registros corrigidos: {corrigidos}")
    print(f"Erros: {erros}")
    print("=" * 70)

if __name__ == '__main__':
    main()
