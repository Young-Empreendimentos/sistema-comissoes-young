"""
Script para sincronizar VALORES PAGOS dos contratos do Sienge
Extrai do paymentConditions (campo amountPaid)

Executar: python sincronizar_valores_pagos.py
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

def sincronizar_valores_pagos():
    """Sincroniza valores pagos de todos os contratos"""
    
    print("=" * 60)
    print("SINCRONIZACAO DE VALORES PAGOS")
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Buscar valores pagos existentes no Supabase
        print("\n[1/3] Verificando valores pagos existentes no Supabase...")
        result_vp = supabase.table('sienge_valor_pago')\
            .select('numero_contrato, building_id')\
            .execute()
        
        vp_existentes = set()
        for item in (result_vp.data or []):
            chave = f"{item.get('numero_contrato')}_{item.get('building_id')}"
            vp_existentes.add(chave)
        
        print(f"      {len(vp_existentes)} valores pagos ja cadastrados no banco")
        
        # Buscar contratos do Sienge de TODAS as empresas
        print("\n[2/3] Buscando contratos no Sienge (todas as empresas)...")
        contracts = sienge_client.get_contracts_all_companies()
        total_contratos = len(contracts)
        print(f"      {total_contratos} contratos encontrados no Sienge")
        
        if total_contratos == 0:
            print("\n[AVISO] Nenhum contrato encontrado no Sienge.")
            return {'sucesso': True, 'novos': 0}
        
        # Estatisticas
        novos = 0
        atualizados = 0
        erros = 0
        sem_valor_pago = 0
        
        print(f"\n[3/3] Processando contratos...")
        print("-" * 60)
        
        for idx, contract in enumerate(contracts, 1):
            numero = contract.get('number')
            bid = contract.get('enterpriseId')
            company_id = contract.get('companyId')
            
            # Pular se campos obrigatorios forem None
            if not numero or not bid or not company_id:
                continue
            
            chave = f"{numero}_{bid}"
            ja_existe = chave in vp_existentes
            
            try:
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
                    
                    if ja_existe:
                        # Atualizar existente
                        supabase.table('sienge_valor_pago')\
                            .update(data)\
                            .eq('numero_contrato', str(numero))\
                            .eq('building_id', str(bid))\
                            .execute()
                        atualizados += 1
                    else:
                        # Inserir novo
                        supabase.table('sienge_valor_pago').insert(data).execute()
                        novos += 1
                        print(f"[{idx}/{total_contratos}] [NOVO] Contrato {numero} (Emp {bid}): R$ {valor_pago:,.2f}")
                else:
                    sem_valor_pago += 1
                        
            except Exception as e:
                erros += 1
                print(f"[{idx}/{total_contratos}] [ERRO] Contrato {numero}: {str(e)[:50]}")
            
            # Progresso a cada 50 contratos
            if idx % 50 == 0:
                print(f"\n--- Progresso: {idx}/{total_contratos} ({(idx/total_contratos*100):.1f}%) | Novos: {novos} | Atualizados: {atualizados} ---\n")
        
        # Relatorio final
        print("\n" + "=" * 60)
        print("RELATORIO FINAL")
        print("=" * 60)
        print(f"Contratos processados:            {total_contratos}")
        print(f"Valores pagos novos:              {novos}")
        print(f"Valores pagos atualizados:        {atualizados}")
        print(f"Contratos sem valor pago:         {sem_valor_pago}")
        print(f"Erros:                            {erros}")
        print("=" * 60)
        
        print(f"\nConcluido em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        return {
            'sucesso': True,
            'total_contratos': total_contratos,
            'novos': novos,
            'atualizados': atualizados,
            'sem_valor_pago': sem_valor_pago,
            'erros': erros
        }
        
    except Exception as e:
        print(f"\n[ERRO FATAL] {str(e)}")
        import traceback
        traceback.print_exc()
        return {'sucesso': False, 'erro': str(e)}


if __name__ == '__main__':
    resultado = sincronizar_valores_pagos()
    
    if resultado and resultado.get('sucesso'):
        print("\n[OK] Sincronizacao concluida com sucesso!")
    else:
        print(f"\n[FALHA] Erro na sincronizacao: {resultado.get('erro') if resultado else 'Desconhecido'}")
        sys.exit(1)
