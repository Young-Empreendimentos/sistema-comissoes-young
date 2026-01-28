# -*- coding: utf-8 -*-
"""
Script para limpar contratos e comissões cancelados do Supabase
Sistema de Comissões Young Empreendimentos
"""

import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


def conectar_supabase():
    """Conecta ao Supabase"""
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )


def listar_contratos_cancelados(supabase):
    """
    Lista todos os contratos que devem ser removidos.
    Um contrato é considerado cancelado se TODAS as suas comissões estão com status CANCELLED.
    """
    print("\n" + "="*60)
    print("BUSCANDO CONTRATOS CANCELADOS...")
    print("="*60)
    
    try:
        # Buscar todas as comissões
        result_comissoes = supabase.table('sienge_comissoes').select('numero_contrato, building_id, installment_status').execute()
        
        # Agrupar comissões por contrato
        contratos_comissoes = {}
        for c in (result_comissoes.data or []):
            chave = f"{c.get('numero_contrato')}_{c.get('building_id')}"
            if chave not in contratos_comissoes:
                contratos_comissoes[chave] = {'statuses': [], 'numero_contrato': c.get('numero_contrato'), 'building_id': c.get('building_id')}
            contratos_comissoes[chave]['statuses'].append(c.get('installment_status') or '')
        
        # Identificar contratos onde TODAS as comissões estão canceladas
        contratos_cancelados_ids = []
        for chave, dados in contratos_comissoes.items():
            todos_cancelados = all('CANCEL' in s.upper() for s in dados['statuses'])
            if todos_cancelados and dados['statuses']:
                contratos_cancelados_ids.append({
                    'numero_contrato': dados['numero_contrato'],
                    'building_id': dados['building_id']
                })
        
        # Buscar dados completos dos contratos cancelados
        contratos_cancelados = []
        for c_id in contratos_cancelados_ids:
            result = supabase.table('sienge_contratos')\
                .select('*')\
                .eq('numero_contrato', c_id['numero_contrato'])\
                .eq('building_id', c_id['building_id'])\
                .execute()
            if result.data:
                contratos_cancelados.extend(result.data)
        
        print(f"\nEncontrados {len(contratos_cancelados)} contratos com TODAS as comissões canceladas:")
        for c in contratos_cancelados:
            print(f"  - Contrato {c.get('numero_contrato')} | Building {c.get('building_id')} | Cliente: {c.get('nome_cliente')}")
        
        return contratos_cancelados
    except Exception as e:
        print(f"Erro ao buscar contratos: {str(e)}")
        return []


def listar_comissoes_canceladas(supabase):
    """Lista todas as comissões com status cancelado (pagas devem permanecer)"""
    print("\n" + "="*60)
    print("BUSCANDO COMISSÕES CANCELADAS...")
    print("="*60)
    
    try:
        result = supabase.table('sienge_comissoes').select('*').execute()
        
        comissoes_canceladas = []
        comissoes_pagas = []
        for c in (result.data or []):
            status = (c.get('installment_status') or '').lower()
            if any(x in status for x in ['cancel', 'distrat', 'rescind']):
                comissoes_canceladas.append(c)
            elif any(x in status for x in ['paid', 'pago']):
                comissoes_pagas.append(c)
        
        print(f"\nEncontradas {len(comissoes_canceladas)} comissões canceladas (serão removidas):")
        for c in comissoes_canceladas:
            print(f"  - ID {c.get('id')} | Contrato {c.get('numero_contrato')} | Corretor: {c.get('broker_nome')} | Status: {c.get('installment_status')}")
        
        print(f"\nEncontradas {len(comissoes_pagas)} comissões pagas (serão marcadas como Aprovadas):")
        for c in comissoes_pagas:
            print(f"  - ID {c.get('id')} | Contrato {c.get('numero_contrato')} | Corretor: {c.get('broker_nome')} | Status: {c.get('installment_status')}")
        
        # Atualizar comissões pagas para status Aprovada
        for c in comissoes_pagas:
            try:
                supabase.table('sienge_comissoes').update({'status_aprovacao': 'Aprovada'}).eq('id', c['id']).execute()
                print(f"  ✓ Comissão {c.get('id')} atualizada para Aprovada")
            except Exception as e:
                print(f"  ✗ Erro ao atualizar comissão {c.get('id')}: {str(e)}")
        
        # Retorna apenas as canceladas para remoção
        return comissoes_canceladas
    except Exception as e:
        print(f"Erro ao buscar comissões: {str(e)}")
        return []


def buscar_duplicatas_comissoes(supabase):
    """Busca comissões duplicadas (mesmo contrato e corretor)"""
    print("\n" + "="*60)
    print("BUSCANDO COMISSÕES DUPLICADAS...")
    print("="*60)
    
    try:
        result = supabase.table('sienge_comissoes').select('*').execute()
        
        # Agrupar por numero_contrato + unit_name
        grupos = {}
        for c in (result.data or []):
            chave = f"{c.get('numero_contrato')}_{c.get('unit_name')}_{c.get('building_id')}"
            if chave not in grupos:
                grupos[chave] = []
            grupos[chave].append(c)
        
        # Encontrar duplicatas
        duplicatas = {k: v for k, v in grupos.items() if len(v) > 1}
        
        print(f"\nEncontrados {len(duplicatas)} grupos de comissões duplicadas:")
        for chave, comissoes in duplicatas.items():
            print(f"\n  Grupo: {chave}")
            for c in comissoes:
                status = c.get('installment_status') or 'N/A'
                print(f"    - ID {c.get('id')} | Corretor: {c.get('broker_nome')} | Status: {status} | Valor: R$ {c.get('commission_value', 0):.2f}")
        
        return duplicatas
    except Exception as e:
        print(f"Erro ao buscar duplicatas: {str(e)}")
        return {}


def deletar_contratos_cancelados(supabase, contratos):
    """Deleta contratos cancelados e suas comissões relacionadas"""
    if not contratos:
        print("Nenhum contrato cancelado para deletar.")
        return 0
    
    count = 0
    for c in contratos:
        try:
            # Primeiro deletar as comissões relacionadas
            supabase.table('sienge_comissoes').delete()\
                .eq('numero_contrato', c.get('numero_contrato'))\
                .eq('building_id', c.get('building_id')).execute()
            print(f"  Deletadas comissões do contrato {c.get('numero_contrato')}")
            
            # Depois deletar o contrato
            supabase.table('sienge_contratos').delete().eq('id', c['id']).execute()
            print(f"  Deletado contrato ID {c['id']} (Contrato {c.get('numero_contrato')})")
            count += 1
        except Exception as e:
            print(f"  Erro ao deletar contrato {c.get('id')}: {str(e)}")
    
    return count


def deletar_comissoes_canceladas(supabase, comissoes):
    """Deleta comissões canceladas"""
    if not comissoes:
        print("Nenhuma comissão cancelada para deletar.")
        return 0
    
    count = 0
    for c in comissoes:
        try:
            supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
            print(f"  Deletada comissão ID {c['id']} (Contrato {c.get('numero_contrato')})")
            count += 1
        except Exception as e:
            print(f"  Erro ao deletar comissão {c['id']}: {str(e)}")
    
    return count


def limpar_duplicatas_comissoes(supabase, duplicatas):
    """
    Remove comissões duplicadas mantendo a mais relevante.
    Critério: Manter a que NÃO está cancelada. Se todas iguais, manter a primeira.
    """
    if not duplicatas:
        print("Nenhuma duplicata para limpar.")
        return 0
    
    count = 0
    for chave, comissoes in duplicatas.items():
        # Ordenar: não-canceladas primeiro, depois por ID
        def prioridade(c):
            status = (c.get('installment_status') or '').lower()
            is_cancelada = any(x in status for x in ['cancel', 'distrat', 'rescind'])
            return (is_cancelada, c.get('id', 0))
        
        comissoes_ordenadas = sorted(comissoes, key=prioridade)
        
        # Manter a primeira, deletar as outras
        manter = comissoes_ordenadas[0]
        deletar = comissoes_ordenadas[1:]
        
        print(f"\n  Grupo {chave}:")
        print(f"    Mantendo: ID {manter['id']} | Corretor: {manter.get('broker_nome')} | Status: {manter.get('installment_status')}")
        
        for c in deletar:
            try:
                supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
                print(f"    Deletada: ID {c['id']} | Corretor: {c.get('broker_nome')} | Status: {c.get('installment_status')}")
                count += 1
            except Exception as e:
                print(f"    Erro ao deletar {c['id']}: {str(e)}")
    
    return count


def main():
    print("\n" + "="*60)
    print("  LIMPEZA DE CONTRATOS E COMISSÕES CANCELADOS")
    print("  Sistema de Comissões Young Empreendimentos")
    print("="*60)
    
    supabase = conectar_supabase()
    
    # 1. Listar contratos cancelados
    contratos_cancelados = listar_contratos_cancelados(supabase)
    
    # 2. Listar comissões canceladas
    comissoes_canceladas = listar_comissoes_canceladas(supabase)
    
    # 3. Buscar duplicatas
    duplicatas = buscar_duplicatas_comissoes(supabase)
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print(f"  Contratos cancelados: {len(contratos_cancelados)}")
    print(f"  Comissões canceladas: {len(comissoes_canceladas)}")
    print(f"  Grupos de duplicatas: {len(duplicatas)}")
    
    # Perguntar se deseja deletar
    if contratos_cancelados or comissoes_canceladas or duplicatas:
        print("\n" + "-"*60)
        resposta = input("Deseja DELETAR os registros cancelados e duplicados? (s/N): ").strip().lower()
        
        if resposta == 's':
            print("\n" + "="*60)
            print("DELETANDO REGISTROS...")
            print("="*60)
            
            # Deletar contratos cancelados
            if contratos_cancelados:
                print("\nDeletando contratos cancelados...")
                count_contratos = deletar_contratos_cancelados(supabase, contratos_cancelados)
                print(f"Total de contratos deletados: {count_contratos}")
            
            # Deletar comissões canceladas
            if comissoes_canceladas:
                print("\nDeletando comissões canceladas...")
                count_comissoes = deletar_comissoes_canceladas(supabase, comissoes_canceladas)
                print(f"Total de comissões canceladas deletadas: {count_comissoes}")
            
            # Limpar duplicatas
            if duplicatas:
                print("\nLimpando duplicatas...")
                count_duplicatas = limpar_duplicatas_comissoes(supabase, duplicatas)
                print(f"Total de duplicatas removidas: {count_duplicatas}")
            
            print("\n" + "="*60)
            print("LIMPEZA CONCLUÍDA!")
            print("="*60)
        else:
            print("\nOperação cancelada. Nenhum registro foi deletado.")
    else:
        print("\nNenhum registro para limpar!")


if __name__ == '__main__':
    main()

