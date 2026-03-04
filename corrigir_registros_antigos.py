"""
Script para corrigir registros antigos com mapeamento errado
Usa corretor + contrato + valor para fazer o match
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
    print("CORRIGINDO REGISTROS ANTIGOS")
    print("=" * 70)
    
    # 1. Buscar todas as comissões da API do Sienge
    print("\n[1/4] Buscando comissões da API do Sienge...")
    comissoes_api = sienge_client.get_commissions_all_companies()
    print(f"      {len(comissoes_api)} comissões encontradas na API")
    
    # Criar mapa por chave única: broker_id + contrato + valor (arredondado)
    mapa_api = {}
    for c in comissoes_api:
        broker_id = c.get('brokerID') or c.get('brokerId')
        contrato = c.get('salesContractNumber') or c.get('contractNumber')
        valor = c.get('value') or c.get('commissionValue')
        
        if broker_id and contrato and valor:
            # Arredondar valor para evitar problemas de precisão
            valor_arred = round(float(valor), 2)
            chave = f"{broker_id}_{contrato}_{valor_arred}"
            mapa_api[chave] = {
                'commissionID': c.get('commissionID'),
                'unitName': c.get('unitName'),
                'installmentStatus': c.get('installmentStatus'),
                'enterpriseName': c.get('enterpriseName'),
                'dueDate': c.get('dueDate'),
            }
    
    print(f"      {len(mapa_api)} comissões mapeadas por chave única")
    
    # 2. Buscar registros no Supabase que precisam correção
    print("\n[2/4] Buscando registros problemáticos no Supabase...")
    result = supabase.table('sienge_comissoes').select('*').execute()
    
    registros = result.data or []
    print(f"      {len(registros)} registros no banco")
    
    # Filtrar só os que têm unit_name errado (> 1000)
    registros_errados = []
    for reg in registros:
        unit = reg.get('unit_name')
        if unit:
            try:
                if int(unit) > 1000:
                    registros_errados.append(reg)
            except:
                pass
    
    print(f"      {len(registros_errados)} registros com unit_name > 1000")
    
    # 3. Corrigir registros
    print("\n[3/4] Corrigindo registros...")
    corrigidos = 0
    nao_encontrados = 0
    erros = 0
    
    for reg in registros_errados:
        broker_id = reg.get('broker_id')
        contrato = reg.get('numero_contrato')
        valor = reg.get('commission_value')
        
        if not broker_id or not contrato or not valor:
            nao_encontrados += 1
            continue
        
        valor_arred = round(float(valor), 2)
        chave = f"{broker_id}_{contrato}_{valor_arred}"
        
        dados_api = mapa_api.get(chave)
        
        if dados_api:
            try:
                update_data = {
                    'sienge_id': dados_api['commissionID'],
                    'unit_name': dados_api['unitName'],
                    'installment_status': dados_api['installmentStatus'],
                    'atualizado_em': datetime.now().isoformat()
                }
                
                supabase.table('sienge_comissoes').update(update_data).eq('id', reg['id']).execute()
                
                print(f"  [OK] ID {reg['id']}: unit_name '{reg.get('unit_name')}' -> '{dados_api['unitName']}'")
                corrigidos += 1
            except Exception as e:
                print(f"  [ERRO] ID {reg['id']}: {str(e)[:50]}")
                erros += 1
        else:
            nao_encontrados += 1
            if nao_encontrados <= 5:
                print(f"  [NAO ENCONTRADO] ID {reg['id']}: broker={broker_id}, contrato={contrato}, valor={valor}")
    
    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"Registros corrigidos: {corrigidos}")
    print(f"Não encontrados na API: {nao_encontrados}")
    print(f"Erros: {erros}")
    print("=" * 70)

if __name__ == '__main__':
    main()
