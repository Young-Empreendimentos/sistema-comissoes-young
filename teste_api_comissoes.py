"""Teste direto da API de comissões para verificar cálculo de gatilho"""
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

from sync_sienge_supabase import SiengeSupabaseSync
sync = SiengeSupabaseSync()

print("=== Teste: Simulando o que a API deveria retornar ===")
print("Contrato 198 | Building 2010 (Erico Verissimo)\n")

numero_contrato = '198'
building_id = '2010'

# Buscar a comissão do banco
comissao_result = supabase.table('sienge_comissoes').select('*').eq('numero_contrato', '198').eq('building_id', 2010).execute()

if comissao_result.data:
    c = comissao_result.data[0]
    print("Dados ANTES do recálculo (do banco):")
    print(f"  valor_gatilho: {c.get('valor_gatilho')}")
    print(f"  atingiu_gatilho: {c.get('atingiu_gatilho')}")
    
    # Agora simular exatamente o que o código faz
    print("\nRecalculando usando as mesmas funções da API...")
    
    contrato = sync.get_contrato_por_numero(str(numero_contrato), building_id)
    valor_itbi = sync.get_itbi_por_contrato(str(numero_contrato), building_id) or 0
    valor_pago = sync.get_valor_pago_por_contrato(str(numero_contrato), building_id) or 0
    
    if contrato:
        valor_a_vista = float(contrato.get('valor_a_vista') or contrato.get('valor_total') or 0)
    else:
        valor_a_vista = 0
        print("  AVISO: Contrato não encontrado!")
    
    regra_gatilho = c.get('regra_gatilho') or '10% + ITBI'
    
    # Calcular usando a função calcular_valor_gatilho
    import re
    def calcular_valor_gatilho(valor_a_vista, valor_itbi, regra):
        if not regra:
            regra = '10% + ITBI'
        regra_lower = regra.lower().strip()
        if '10%' in regra_lower and 'itbi' in regra_lower:
            return (valor_a_vista * 0.10) + valor_itbi
        elif '10%' in regra_lower:
            return valor_a_vista * 0.10
        elif '5%' in regra_lower:
            return valor_a_vista * 0.05
        elif '6%' in regra_lower:
            return valor_a_vista * 0.06
        else:
            match = re.search(r'(\d+[,.]?\d*)\s*%', regra)
            if match:
                percentual = float(match.group(1).replace(',', '.')) / 100
                if 'itbi' in regra_lower:
                    return (valor_a_vista * percentual) + valor_itbi
                return valor_a_vista * percentual
            return (valor_a_vista * 0.10) + valor_itbi
    
    valor_gatilho = calcular_valor_gatilho(valor_a_vista, float(valor_itbi), regra_gatilho)
    atingiu_gatilho = float(valor_pago) >= valor_gatilho if valor_gatilho > 0 else False
    
    print("\nDados DEPOIS do recálculo (o que a API deveria retornar):")
    print(f"  valor_a_vista: R$ {valor_a_vista:,.2f}")
    print(f"  valor_itbi: R$ {valor_itbi:,.2f}")
    print(f"  valor_pago: R$ {valor_pago:,.2f}")
    print(f"  regra_gatilho: {regra_gatilho}")
    print(f"  valor_gatilho: R$ {valor_gatilho:,.2f}")
    print(f"  atingiu_gatilho: {atingiu_gatilho}")
else:
    print("Comissão não encontrada no banco!")
