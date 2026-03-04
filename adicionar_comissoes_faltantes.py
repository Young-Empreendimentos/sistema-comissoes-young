"""
Script para adicionar comissões faltantes (múltiplos corretores por contrato)
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
    print("ADICIONANDO COMISSÕES FALTANTES")
    print("=" * 70)
    
    # 1. Buscar comissões da API
    print("\n[1/3] Buscando comissões da API...")
    commissions = sienge_client.get_commissions_all_companies()
    print(f"      {len(commissions)} comissões encontradas na API")
    
    # 2. Buscar comissões existentes no Supabase
    print("\n[2/3] Verificando comissões existentes no Supabase...")
    result = supabase.table('sienge_comissoes').select('sienge_id, broker_id').execute()
    
    # Criar set de chaves existentes (sienge_id + broker_id)
    existentes = set()
    for item in (result.data or []):
        sienge_id = item.get('sienge_id')
        broker_id = item.get('broker_id')
        if sienge_id and broker_id:
            existentes.add(f"{sienge_id}_{broker_id}")
    
    print(f"      {len(existentes)} comissões únicas no banco")
    
    # 3. Identificar comissões faltantes
    print("\n[3/3] Processando comissões faltantes...")
    
    faltantes = []
    for commission in commissions:
        sienge_id = commission.get('commissionID') or commission.get('id')
        broker_id = commission.get('brokerID') or commission.get('brokerId')
        
        if not sienge_id or not broker_id:
            continue
        
        chave = f"{sienge_id}_{broker_id}"
        if chave not in existentes:
            faltantes.append(commission)
    
    print(f"      {len(faltantes)} comissões faltantes encontradas")
    
    if not faltantes:
        print("\nNenhuma comissão faltante!")
        return
    
    # 4. Inserir comissões faltantes
    # Como há constraint unique em sienge_id, vamos usar um ID único diferente
    # Vamos criar um novo sienge_id combinando o original com broker_id
    
    print("\nInserindo comissões faltantes...")
    inseridos = 0
    erros = 0
    
    for commission in faltantes:
        try:
            sienge_id = commission.get('commissionID') or commission.get('id')
            broker_id = commission.get('brokerID') or commission.get('brokerId')
            
            # Criar ID único: sienge_id original + broker_id separados por underscore
            # Mas para manter compatibilidade, vamos usar um número grande único
            # ID único = sienge_id * 100000 + broker_id (assumindo broker_id < 100000)
            sienge_id_unico = int(sienge_id) * 100000 + int(broker_id)
            
            data = {
                'sienge_id': str(sienge_id_unico),
                'numero_contrato': str(commission.get('salesContractNumber') or commission.get('contractNumber')) if (commission.get('salesContractNumber') or commission.get('contractNumber')) else None,
                'building_id': commission.get('enterpriseID') or commission.get('enterpriseId'),
                'company_id': str(commission.get('companyId')) if commission.get('companyId') else None,
                'broker_id': broker_id,
                'broker_nome': commission.get('brokerName'),
                'customer_name': commission.get('customerName'),
                'enterprise_name': commission.get('enterpriseName'),
                'unit_name': commission.get('unitName'),
                'commission_value': commission.get('value') or commission.get('commissionValue'),
                'installment_status': commission.get('installmentStatus'),
                'customer_situation_type': commission.get('customerSituationType'),
                'commission_date': commission.get('dueDate') or commission.get('commissionDate'),
                'status_aprovacao': 'Pendente',
                'atualizado_em': datetime.now().isoformat()
            }
            
            supabase.table('sienge_comissoes').insert(data).execute()
            inseridos += 1
            print(f"  [INSERIDO] {commission.get('brokerName')} - Contrato {commission.get('salesContractNumber')} - R$ {commission.get('value')}")
            
        except Exception as e:
            erros += 1
            print(f"  [ERRO] {commission.get('brokerName')}: {str(e)[:80]}")
    
    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"Comissões inseridas: {inseridos}")
    print(f"Erros: {erros}")
    print("=" * 70)

if __name__ == '__main__':
    main()
