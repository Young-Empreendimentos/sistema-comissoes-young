"""
Script para sincronizar ITBIs FALTANTES dos contratos do Sienge
Busca apenas contratos que NAO possuem ITBI no Supabase
Extrai ITBI do paymentConditions (conditionTypeId='DC')

Executar: python sincronizar_itbis_faltantes.py
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

def sincronizar_itbis_faltantes():
    """Sincroniza apenas ITBIs que NAO existem no Supabase"""
    
    print("=" * 60)
    print("SINCRONIZACAO DE ITBIs FALTANTES")
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Buscar ITBIs existentes no Supabase
        print("\n[1/3] Verificando ITBIs existentes no Supabase...")
        result_itbi = supabase.table('sienge_itbi')\
            .select('numero_contrato, building_id')\
            .execute()
        
        itbi_existentes = set()
        for item in (result_itbi.data or []):
            chave = f"{item.get('numero_contrato')}_{item.get('building_id')}"
            itbi_existentes.add(chave)
        
        print(f"      {len(itbi_existentes)} ITBIs ja cadastrados no banco")
        
        # Buscar contratos do Sienge de TODAS as empresas
        print("\n[2/3] Buscando contratos no Sienge (todas as empresas)...")
        contracts = sienge_client.get_contracts_all_companies()
        total_contratos = len(contracts)
        print(f"      {total_contratos} contratos encontrados no Sienge")
        
        if total_contratos == 0:
            print("\n[AVISO] Nenhum contrato encontrado no Sienge.")
            return {'sucesso': True, 'itbis_novos': 0}
        
        # Estatisticas
        itbis_novos = 0
        itbis_atualizados = 0
        erros = 0
        sem_itbi_sienge = []
        
        print(f"\n[3/3] Processando contratos...")
        print("-" * 60)
        
        for idx, contract in enumerate(contracts, 1):
            numero = contract.get('number')
            bid = contract.get('enterpriseId')
            company_id = contract.get('companyId')
            
            # Pular se campos obrigatórios forem None
            if not numero or not bid or not company_id:
                continue
            
            chave = f"{numero}_{bid}"
            
            # Verificar se já existe
            ja_existe = chave in itbi_existentes
            
            try:
                # Extrair ITBI do paymentConditions
                itbi_data = sienge_client.extract_itbi_from_contract(contract)
                
                if itbi_data and itbi_data.get('valor_itbi', 0) > 0:
                    valor_itbi = itbi_data['valor_itbi']
                    
                    data = {
                        'numero_contrato': str(numero),
                        'building_id': str(bid),
                        'company_id': str(company_id),
                        'valor_itbi': valor_itbi,
                        'documento_sienge': itbi_data.get('documento') or f'ITBI {numero}',
                        'data_vencimento': itbi_data.get('data_vencimento'),
                        'plano_financeiro': '2.04.13',
                        'atualizado_em': datetime.now().isoformat()
                    }
                    
                    if ja_existe:
                        # Atualizar existente
                        supabase.table('sienge_itbi')\
                            .update(data)\
                            .eq('numero_contrato', numero)\
                            .eq('building_id', bid)\
                            .execute()
                        itbis_atualizados += 1
                    else:
                        # Inserir novo
                        supabase.table('sienge_itbi').insert(data).execute()
                        itbis_novos += 1
                        print(f"[{idx}/{total_contratos}] [NOVO] Contrato {numero} (Emp {bid}): R$ {valor_itbi:,.2f}")
                else:
                    if not ja_existe:
                        # Extrair nome do cliente
                        customers = contract.get('salesContractCustomers', [])
                        cliente = customers[0].get('name', '')[:30] if customers else ''
                        
                        sem_itbi_sienge.append({
                            'contrato': numero,
                            'building_id': bid,
                            'cliente': cliente
                        })
                        
            except Exception as e:
                erros += 1
                print(f"[{idx}/{total_contratos}] [ERRO] Contrato {numero}: {str(e)[:50]}")
            
            # Progresso a cada 50 contratos
            if idx % 50 == 0:
                print(f"\n--- Progresso: {idx}/{total_contratos} ({(idx/total_contratos*100):.1f}%) | Novos: {itbis_novos} | Atualizados: {itbis_atualizados} ---\n")
        
        # Relatorio final
        print("\n" + "=" * 60)
        print("RELATORIO FINAL")
        print("=" * 60)
        print(f"Contratos processados:            {total_contratos}")
        print(f"ITBIs novos cadastrados:          {itbis_novos}")
        print(f"ITBIs atualizados:                {itbis_atualizados}")
        print(f"Contratos sem ITBI no Sienge:     {len(sem_itbi_sienge)}")
        print(f"Erros:                            {erros}")
        print("=" * 60)
        
        # Listar contratos sem ITBI (se nao forem muitos)
        if sem_itbi_sienge and len(sem_itbi_sienge) <= 30:
            print("\nContratos SEM ITBI no Sienge:")
            print("-" * 60)
            for item in sem_itbi_sienge:
                print(f"  - Contrato {item['contrato']} (Emp {item['building_id']}) - {item['cliente']}")
        elif sem_itbi_sienge:
            print(f"\n[INFO] {len(sem_itbi_sienge)} contratos sem ITBI no Sienge.")
        
        print(f"\nConcluido em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        return {
            'sucesso': True,
            'total_contratos': total_contratos,
            'itbis_novos': itbis_novos,
            'itbis_atualizados': itbis_atualizados,
            'sem_itbi_sienge': len(sem_itbi_sienge),
            'erros': erros
        }
        
    except Exception as e:
        print(f"\n[ERRO FATAL] {str(e)}")
        import traceback
        traceback.print_exc()
        return {'sucesso': False, 'erro': str(e)}


if __name__ == '__main__':
    resultado = sincronizar_itbis_faltantes()
    
    if resultado and resultado.get('sucesso'):
        print("\n[OK] Sincronizacao concluida com sucesso!")
    else:
        print(f"\n[FALHA] Erro na sincronizacao: {resultado.get('erro') if resultado else 'Desconhecido'}")
        sys.exit(1)
