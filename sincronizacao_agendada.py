"""
Script de Sincronizacao Agendada - Sistema de Comissoes Young
Executa sincronizacao completa: contratos, comissoes, ITBIs e valores pagos

Pode ser executado manualmente ou agendado via Task Scheduler do Windows
Executar: python sincronizacao_agendada.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

# Verificar variaveis de ambiente
if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
    print("[ERRO] Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas!")
    sys.exit(1)

from supabase import create_client
from sienge_client import sienge_client

# Conectar ao Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Arquivo de log
LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'sincronizacao.log')

def log(mensagem):
    """Registra mensagem no console e no arquivo de log"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linha = f"[{timestamp}] {mensagem}"
    print(linha)
    
    # Criar pasta de logs se nao existir
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(linha + '\n')


def sincronizar_contratos():
    """Sincroniza contratos de todas as empresas"""
    log("Iniciando sincronizacao de CONTRATOS...")
    
    try:
        contracts = sienge_client.get_contracts_all_companies()
        total = len(contracts)
        sincronizados = 0
        erros = 0
        
        for contract in contracts:
            try:
                sienge_id = contract.get('id')
                if not sienge_id:
                    continue
                
                # Extrair nome do cliente
                customers = contract.get('salesContractCustomers', [])
                nome_cliente = customers[0].get('name') if customers else None
                
                # Extrair unidade
                units = contract.get('salesContractUnits', [])
                unidade = units[0].get('name') if units else None
                
                data = {
                    'sienge_id': sienge_id,
                    'numero_contrato': str(contract.get('number')) if contract.get('number') else None,
                    'building_id': contract.get('enterpriseId'),
                    'company_id': str(contract.get('companyId')) if contract.get('companyId') else None,
                    'nome_cliente': nome_cliente,
                    'data_contrato': contract.get('contractDate'),
                    'valor_total': contract.get('value') or contract.get('totalSellingValue'),
                    'valor_a_vista': contract.get('value'),
                    'status': contract.get('situation'),
                    'unidade': unidade,
                    'atualizado_em': datetime.now().isoformat()
                }
                
                # Usar upsert para inserir ou atualizar
                supabase.table('sienge_contratos').upsert(data, on_conflict='sienge_id').execute()
                sincronizados += 1
                    
            except Exception as e:
                erros += 1
                if erros <= 5:
                    log(f"  Erro contrato {contract.get('id')}: {str(e)[:100]}")
        
        log(f"CONTRATOS: {total} processados | {sincronizados} sincronizados | {erros} erros")
        return {'sucesso': True, 'total': total, 'sincronizados': sincronizados, 'erros': erros}
        
    except Exception as e:
        log(f"ERRO em contratos: {str(e)}")
        return {'sucesso': False, 'erro': str(e)}


def sincronizar_comissoes():
    """Sincroniza comissoes de todas as empresas"""
    log("Iniciando sincronizacao de COMISSOES...")
    
    try:
        # Buscar comissoes da API
        commissions = sienge_client.get_commissions_all_companies()
        total_api = len(commissions)
        log(f"  {total_api} comissoes encontradas na API")
        
        # Buscar comissoes existentes no Supabase
        result = supabase.table('sienge_comissoes').select('sienge_id').execute()
        existentes = set(int(item['sienge_id']) for item in (result.data or []) if item['sienge_id'])
        log(f"  {len(existentes)} comissoes ja cadastradas")
        
        ids_processados = set()
        novos = 0
        atualizados = 0
        erros = 0
        
        for commission in commissions:
            try:
                # O campo correto e commissionID
                sienge_id = commission.get('commissionID') or commission.get('id') or commission.get('commissionId')
                if not sienge_id or sienge_id in ids_processados:
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
                    
            except Exception as e:
                erros += 1
                if erros <= 5:
                    log(f"  Erro comissao {commission.get('commissionID')}: {str(e)[:100]}")
        
        log(f"COMISSOES: {len(ids_processados)} processadas | {novos} novas | {atualizados} atualizadas | {erros} erros")
        return {'sucesso': True, 'total': len(ids_processados), 'sincronizados': novos + atualizados, 'novos': novos, 'atualizados': atualizados, 'erros': erros}
        
    except Exception as e:
        log(f"ERRO em comissoes: {str(e)}")
        return {'sucesso': False, 'erro': str(e)}


def sincronizar_itbis():
    """Sincroniza ITBIs de todos os contratos"""
    log("Iniciando sincronizacao de ITBIs...")
    
    try:
        contracts = sienge_client.get_contracts_all_companies()
        total = len(contracts)
        sincronizados = 0
        erros = 0
        
        for contract in contracts:
            try:
                numero = contract.get('number')
                bid = contract.get('enterpriseId')
                company_id = contract.get('companyId')
                
                if not numero or not bid or not company_id:
                    continue
                
                # Extrair ITBI do paymentConditions
                itbi_data = sienge_client.extract_itbi_from_contract(contract)
                
                if itbi_data and itbi_data.get('valor_itbi', 0) > 0:
                    data = {
                        'numero_contrato': str(numero),
                        'building_id': str(bid),
                        'company_id': str(company_id),
                        'valor_itbi': itbi_data['valor_itbi'],
                        'documento_sienge': itbi_data.get('documento') or f'ITBI {numero}',
                        'data_vencimento': itbi_data.get('data_vencimento'),
                        'plano_financeiro': '2.04.13',
                        'atualizado_em': datetime.now().isoformat()
                    }
                    
                    # Verificar se existe
                    existing = supabase.table('sienge_itbi').select('id').eq('numero_contrato', str(numero)).eq('building_id', str(bid)).execute()
                    
                    if existing.data:
                        supabase.table('sienge_itbi').update(data).eq('numero_contrato', str(numero)).eq('building_id', str(bid)).execute()
                    else:
                        supabase.table('sienge_itbi').insert(data).execute()
                    
                    sincronizados += 1
                        
            except Exception as e:
                erros += 1
                if erros <= 5:
                    log(f"  Erro ITBI contrato {contract.get('number')}: {str(e)[:100]}")
        
        log(f"ITBIs: {total} contratos verificados | {sincronizados} sincronizados | {erros} erros")
        return {'sucesso': True, 'total': total, 'sincronizados': sincronizados, 'erros': erros}
        
    except Exception as e:
        log(f"ERRO em ITBIs: {str(e)}")
        return {'sucesso': False, 'erro': str(e)}


def sincronizar_valores_pagos():
    """Sincroniza valores pagos de todos os contratos"""
    log("Iniciando sincronizacao de VALORES PAGOS...")
    
    try:
        contracts = sienge_client.get_contracts_all_companies()
        total = len(contracts)
        sincronizados = 0
        erros = 0
        
        for contract in contracts:
            try:
                numero = contract.get('number')
                bid = contract.get('enterpriseId')
                company_id = contract.get('companyId')
                
                if not numero or not bid or not company_id:
                    continue
                
                # Extrair valor pago do paymentConditions
                valor_pago = sienge_client.extract_valor_pago_from_contract(contract)
                
                if valor_pago > 0:
                    data = {
                        'numero_contrato': str(numero),
                        'building_id': str(bid),
                        'company_id': str(company_id),
                        'valor_pago': valor_pago,
                        'atualizado_em': datetime.now().isoformat()
                    }
                    
                    # Verificar se existe
                    existing = supabase.table('sienge_valor_pago').select('id').eq('numero_contrato', str(numero)).eq('building_id', str(bid)).execute()
                    
                    if existing.data:
                        supabase.table('sienge_valor_pago').update(data).eq('numero_contrato', str(numero)).eq('building_id', str(bid)).execute()
                    else:
                        supabase.table('sienge_valor_pago').insert(data).execute()
                    
                    sincronizados += 1
                        
            except Exception as e:
                erros += 1
                if erros <= 5:
                    log(f"  Erro valor pago contrato {contract.get('number')}: {str(e)[:100]}")
        
        log(f"VALORES PAGOS: {total} contratos verificados | {sincronizados} sincronizados | {erros} erros")
        return {'sucesso': True, 'total': total, 'sincronizados': sincronizados, 'erros': erros}
        
    except Exception as e:
        log(f"ERRO em valores pagos: {str(e)}")
        return {'sucesso': False, 'erro': str(e)}


def executar_sincronizacao_completa():
    """Executa sincronizacao completa de todos os dados"""
    
    log("=" * 60)
    log("SINCRONIZACAO AGENDADA - INICIO")
    log("=" * 60)
    
    inicio = datetime.now()
    resultados = {}
    
    # 1. Sincronizar contratos primeiro (base para os outros)
    resultados['contratos'] = sincronizar_contratos()
    
    # 2. Sincronizar comissoes (incluindo canceladas)
    resultados['comissoes'] = sincronizar_comissoes()
    
    # 3. Sincronizar ITBIs
    resultados['itbis'] = sincronizar_itbis()
    
    # 4. Sincronizar valores pagos
    resultados['valores_pagos'] = sincronizar_valores_pagos()
    
    fim = datetime.now()
    duracao = (fim - inicio).total_seconds() / 60
    
    log("=" * 60)
    log("RESUMO DA SINCRONIZACAO")
    log("=" * 60)
    
    total_sincronizados = 0
    total_erros = 0
    
    for tipo, res in resultados.items():
        if res.get('sucesso'):
            total_sincronizados += res.get('sincronizados', 0)
            total_erros += res.get('erros', 0)
            log(f"  {tipo.upper()}: {res.get('sincronizados', 0)} sincronizados, {res.get('erros', 0)} erros")
        else:
            log(f"  {tipo.upper()}: ERRO - {res.get('erro')}")
    
    log("-" * 60)
    log(f"TOTAL: {total_sincronizados} sincronizados | {total_erros} erros")
    log(f"Duracao: {duracao:.1f} minutos")
    log("=" * 60)
    log("SINCRONIZACAO AGENDADA - FIM")
    log("=" * 60)
    
    return resultados


if __name__ == '__main__':
    executar_sincronizacao_completa()
