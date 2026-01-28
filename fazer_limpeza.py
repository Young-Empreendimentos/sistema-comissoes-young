# -*- coding: utf-8 -*-
"""
Script de limpeza que salva resultado em JSON
"""
import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def main():
    resultado = {
        'status': 'iniciando',
        'canceladas_antes': 0,
        'canceladas_deletadas': 0,
        'duplicatas_antes': 0,
        'duplicatas_deletadas': 0,
        'erro': None
    }
    
    try:
        sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
        
        # 1. Contar e deletar canceladas
        result = sb.table('sienge_comissoes').select('id, installment_status').execute()
        canceladas = [c for c in (result.data or []) if 'CANCEL' in (c.get('installment_status') or '').upper()]
        resultado['canceladas_antes'] = len(canceladas)
        
        for c in canceladas:
            try:
                sb.table('sienge_comissoes').delete().eq('id', c['id']).execute()
                resultado['canceladas_deletadas'] += 1
            except:
                pass
        
        # 2. Buscar duplicatas
        result2 = sb.table('sienge_comissoes').select('*').execute()
        grupos = {}
        for c in (result2.data or []):
            chave = f"{c.get('numero_contrato')}_{c.get('unit_name')}_{c.get('building_id')}"
            if chave not in grupos:
                grupos[chave] = []
            grupos[chave].append(c)
        
        duplicatas = {k: v for k, v in grupos.items() if len(v) > 1}
        resultado['duplicatas_antes'] = len(duplicatas)
        
        for chave, comissoes in duplicatas.items():
            comissoes.sort(key=lambda x: ('CANCEL' in (x.get('installment_status') or '').upper(), x.get('id', 0)))
            for c in comissoes[1:]:
                try:
                    sb.table('sienge_comissoes').delete().eq('id', c['id']).execute()
                    resultado['duplicatas_deletadas'] += 1
                except:
                    pass
        
        resultado['status'] = 'concluido'
        
    except Exception as e:
        resultado['status'] = 'erro'
        resultado['erro'] = str(e)
    
    # Salvar resultado
    with open('resultado_limpeza.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    return resultado

if __name__ == '__main__':
    main()

