"""
Script para limpar duplicados e manter apenas a comissão mais relevante por contrato
Regra: Se tem uma PAGA ou LIBERADA, manter essa e remover as canceladas
       Se todas são canceladas, manter a mais recente
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

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def prioridade_status(status):
    """Retorna prioridade do status (menor = mais importante)"""
    status = (status or '').upper()
    if 'PAID' in status:
        return 1
    if 'RELEASED' in status:
        return 2
    if 'AWAITING' in status:
        return 3
    if 'CANCEL' in status:
        return 99  # Cancelado tem menor prioridade
    return 50

def main():
    print("=" * 80)
    print("LIMPANDO DUPLICADOS - MANTENDO COMISSÕES MAIS RELEVANTES")
    print("=" * 80)

    # Buscar todas as comissões
    result = supabase.table('sienge_comissoes').select('*').execute()
    comissoes = result.data or []
    print(f"\nTotal de comissões no banco: {len(comissoes)}")

    # Agrupar por contrato + empreendimento
    grupos = {}
    for c in comissoes:
        chave = f"{c.get('numero_contrato')}_{c.get('enterprise_name')}"
        if chave not in grupos:
            grupos[chave] = []
        grupos[chave].append(c)

    # Processar duplicados
    removidos = 0
    erros = 0
    
    for chave, lista in grupos.items():
        if len(lista) <= 1:
            continue
        
        # Ordenar por prioridade de status (PAID > RELEASED > AWAITING > CANCELLED)
        # Em caso de empate, manter o com maior sienge_id (mais recente)
        lista.sort(key=lambda x: (
            prioridade_status(x.get('installment_status')),
            -int(x.get('sienge_id') or 0)
        ))
        
        # Manter o primeiro (mais importante), remover os outros
        manter = lista[0]
        remover = lista[1:]
        
        if remover:
            print(f"\n{chave}:")
            print(f"  MANTER: ID {manter.get('id')} | Sienge {manter.get('sienge_id')} | {manter.get('installment_status')} | R$ {manter.get('commission_value')}")
            
            for c in remover:
                try:
                    supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
                    print(f"  REMOVER: ID {c.get('id')} | Sienge {c.get('sienge_id')} | {c.get('installment_status')} | R$ {c.get('commission_value')}")
                    removidos += 1
                except Exception as e:
                    print(f"  ERRO ao remover ID {c.get('id')}: {str(e)[:50]}")
                    erros += 1

    print("\n" + "=" * 80)
    print("RESULTADO")
    print("=" * 80)
    print(f"Comissões removidas: {removidos}")
    print(f"Erros: {erros}")
    print(f"Comissões restantes: {len(comissoes) - removidos}")
    print("=" * 80)

if __name__ == '__main__':
    main()
