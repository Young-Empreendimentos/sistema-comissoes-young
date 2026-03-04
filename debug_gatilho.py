import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print('Buscando dados do contrato 198 Erico Verissimo...')

# Contrato
contrato = supabase.table('sienge_contratos').select('*').eq('numero_contrato', '198').eq('building_id', 2010).execute()
if contrato.data:
    c = contrato.data[0]
    print(f"Contrato: {c.get('numero_contrato')}")
    print(f"  valor_a_vista: {c.get('valor_a_vista')}")
    print(f"  valor_total: {c.get('valor_total')}")

# ITBI
itbi = supabase.table('sienge_itbi').select('*').eq('numero_contrato', '198').eq('building_id', '2010').execute()
print(f"ITBI encontrado: {len(itbi.data or [])}")
if itbi.data:
    print(f"  valor_itbi: {itbi.data[0].get('valor_itbi')}")

# Valor pago
vp = supabase.table('sienge_valor_pago').select('*').eq('numero_contrato', '198').eq('building_id', '2010').execute()
print(f"Valor pago encontrado: {len(vp.data or [])}")
if vp.data:
    print(f"  valor_pago: {vp.data[0].get('valor_pago')}")

# Comissao
comissao = supabase.table('sienge_comissoes').select('*').eq('numero_contrato', '198').eq('building_id', 2010).execute()
print(f"Comissoes encontradas: {len(comissao.data or [])}")
if comissao.data:
    for cm in comissao.data:
        print(f"  ID: {cm.get('sienge_id')} - regra: {cm.get('regra_gatilho')} - valor_gatilho_banco: {cm.get('valor_gatilho')} - atingiu_banco: {cm.get('atingiu_gatilho')}")

# Calcular gatilho CORRETO
if contrato.data:
    valor_a_vista = float(contrato.data[0].get('valor_a_vista') or contrato.data[0].get('valor_total') or 0)
    valor_itbi = float(itbi.data[0].get('valor_itbi') if itbi.data else 0)
    valor_pago = float(vp.data[0].get('valor_pago') if vp.data else 0)
    
    # Regra 10% + ITBI
    valor_gatilho = (valor_a_vista * 0.10) + valor_itbi
    atingiu = valor_pago >= valor_gatilho
    
    print(f"\n=== CALCULO CORRETO ===")
    print(f"valor_a_vista: R$ {valor_a_vista:,.2f}")
    print(f"valor_itbi: R$ {valor_itbi:,.2f}")
    print(f"valor_pago: R$ {valor_pago:,.2f}")
    print(f"valor_gatilho (10% + ITBI): R$ {valor_gatilho:,.2f}")
    print(f"atingiu_gatilho: {atingiu}")
