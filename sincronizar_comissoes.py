"""
Script para sincronizar TODAS as comissoes do Sienge para o Supabase
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

def sincronizar_comissoes():
    print("=" * 60)
    print("SINCRONIZACAO DE COMISSOES - INICIO")
    print("=" * 60)
    
    # 1. Buscar comissoes da API principal
    print("\n[1/3] Buscando comissoes da API...")
    commissions = sienge_client.get_commissions_all_companies()
    print(f"      {len(commissions)} comissoes encontradas na API")
    
    # 2. Buscar comissoes existentes no Supabase
    print("\n[2/3] Verificando comissoes existentes no Supabase...")
    result = supabase.table('sienge_comissoes').select('sienge_id').execute()
    # sienge_id no Supabase e string, entao convertemos para int para comparacao
    existentes = set(int(item['sienge_id']) for item in (result.data or []) if item['sienge_id'])
    print(f"      {len(existentes)} comissoes ja cadastradas")
    
    # 3. Processar e inserir/atualizar
    print("\n[3/3] Processando comissoes...")
    
    ids_processados = set()
    novos = 0
    atualizados = 0
    erros = 0
    
    for commission in commissions:
        try:
            # O campo correto e commissionID
            sienge_id = commission.get('commissionID') or commission.get('id') or commission.get('commissionId')
            if not sienge_id:
                continue
            
            if sienge_id in ids_processados:
                continue
            
            ids_processados.add(sienge_id)
            
            data = {
                'sienge_id': str(sienge_id),
                'numero_contrato': str(commission.get('salesContractNumber') or commission.get('contractNumber')) if (commission.get('salesContractNumber') or commission.get('contractNumber')) else None,
                'building_id': commission.get('enterpriseID') or commission.get('enterpriseId'),
                'company_id': str(commission.get('companyId')) if commission.get('companyId') else None,
                'broker_id': commission.get('brokerID') or commission.get('brokerId'),
                'broker_nome': commission.get('brokerName'),
                'customer_name': commission.get('customerName'),
                'enterprise_name': commission.get('enterpriseName'),
                'unit_name': commission.get('unitName'),
                'commission_value': commission.get('value') or commission.get('commissionValue'),
                'installment_status': commission.get('installmentStatus'),
                'customer_situation_type': commission.get('customerSituationType'),
                'commission_date': commission.get('dueDate') or commission.get('commissionDate'),
                'atualizado_em': datetime.now().isoformat()
            }
            
            if sienge_id in existentes:
                supabase.table('sienge_comissoes').update(data).eq('sienge_id', str(sienge_id)).execute()
                atualizados += 1
            else:
                data['status_aprovacao'] = 'Pendente'
                supabase.table('sienge_comissoes').insert(data).execute()
                novos += 1
                print(f"      [NOVO] ID {sienge_id} - {commission.get('brokerName')} - Contrato {commission.get('salesContractNumber')} - R$ {commission.get('value')}")
                
        except Exception as e:
            erros += 1
            if erros <= 10:
                print(f"      [ERRO] ID {commission.get('commissionID')}: {str(e)[:80]}")
    
    print("\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"Total processado: {len(ids_processados)} comissoes unicas")
    print(f"Novas inseridas:  {novos}")
    print(f"Atualizadas:      {atualizados}")
    print(f"Erros:            {erros}")
    print("=" * 60)
    
    return {'novos': novos, 'atualizados': atualizados, 'erros': erros}


if __name__ == '__main__':
    sincronizar_comissoes()
