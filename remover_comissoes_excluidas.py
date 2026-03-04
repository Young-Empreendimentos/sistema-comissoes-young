"""
Remove comissões do banco que não existem mais na API do Sienge
"""
import os
import sys
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
    print("REMOVENDO COMISSÕES EXCLUÍDAS DO SIENGE")
    print("=" * 70)
    
    # 1. Buscar todas comissões da API do Sienge
    print("\n[1/3] Buscando comissões da API do Sienge...")
    commissions = sienge_client.get_commissions_all_companies()
    
    # Criar set de IDs que existem na API (commission_id + broker_id)
    ids_api = set()
    for c in commissions:
        commission_id = c.get('commissionID')
        broker_id = c.get('brokerID') or c.get('brokerId')
        if commission_id:
            ids_api.add(str(commission_id))
            # Também adicionar chave composta para IDs únicos criados
            if broker_id:
                id_composto = int(commission_id) * 100000 + int(broker_id)
                ids_api.add(str(id_composto))
    
    print(f"      {len(commissions)} comissões na API")
    
    # 2. Buscar todas comissões do banco
    print("\n[2/3] Buscando comissões do banco...")
    result = supabase.table('sienge_comissoes').select('id, sienge_id, numero_contrato, broker_nome, installment_status, commission_value').execute()
    comissoes_banco = result.data or []
    print(f"      {len(comissoes_banco)} comissões no banco")
    
    # 3. Identificar comissões que não existem mais na API
    print("\n[3/3] Identificando comissões excluídas...")
    
    excluidas = []
    for c in comissoes_banco:
        sienge_id = c.get('sienge_id')
        if sienge_id and sienge_id not in ids_api:
            excluidas.append(c)
    
    print(f"      {len(excluidas)} comissões não existem mais na API")
    
    if not excluidas:
        print("\nNenhuma comissão para remover!")
        return
    
    print("\nComissões a serem removidas:")
    for c in excluidas:
        print(f"  - ID {c.get('id')} | Sienge {c.get('sienge_id')} | Contrato {c.get('numero_contrato')} | {c.get('broker_nome')[:30] if c.get('broker_nome') else 'N/A'} | {c.get('installment_status')}")
    
    # Confirmar antes de remover
    print(f"\n*** ATENÇÃO: Serão removidas {len(excluidas)} comissões ***")
    confirma = input("Digite 'SIM' para confirmar a remoção: ")
    
    if confirma.upper() != 'SIM':
        print("Operação cancelada.")
        return
    
    # 4. Remover comissões
    print("\nRemovendo comissões...")
    removidas = 0
    erros = 0
    
    for c in excluidas:
        try:
            # Primeiro remover do histórico de aprovações
            supabase.table('historico_aprovacoes').delete().eq('comissao_id', c['id']).execute()
            # Depois remover a comissão
            supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
            removidas += 1
            print(f"  [OK] Removida: Contrato {c.get('numero_contrato')} | {c.get('broker_nome')}")
        except Exception as e:
            erros += 1
            print(f"  [ERRO] ID {c.get('id')}: {str(e)[:60]}")
    
    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"Comissões removidas: {removidas}")
    print(f"Erros: {erros}")

if __name__ == '__main__':
    main()
