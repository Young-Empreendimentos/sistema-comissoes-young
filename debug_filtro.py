"""
Debug - simular filtro do frontend
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Simular: Status Aprovação = "Aprovada" + Status Sienge != "Pago"
result = supabase.table('sienge_comissoes').select('*').execute()
comissoes = result.data or []

print(f"Total no banco: {len(comissoes)}")

# 1. Filtrar canceladas (como o backend faz)
comissoes = [c for c in comissoes if 'CANCEL' not in (c.get('installment_status') or '').upper()]
print(f"Após remover CANCELLED: {len(comissoes)}")

# 2. Filtrar por status_aprovacao = "Aprovada"
aprovadas = [c for c in comissoes if c.get('status_aprovacao') == 'Aprovada']
print(f"Com status_aprovacao='Aprovada': {len(aprovadas)}")

# 3. Filtrar removendo as que tem status Sienge "Pago"
# O mapa do backend para "pago" é: ['paidout', 'paid out', 'paid', 'pago']
def is_pago(status):
    status = (status or '').lower()
    return any(v in status for v in ['paidout', 'paid out', 'paid', 'pago'])

nao_pagas = [c for c in aprovadas if not is_pago(c.get('installment_status'))]
print(f"Aprovadas e NÃO pagas: {len(nao_pagas)}")

print("\nLista das aprovadas e não pagas:")
for c in nao_pagas:
    print(f"  - Contrato {c.get('numero_contrato')} | {c.get('broker_nome')[:30] if c.get('broker_nome') else 'N/A'} | Sienge: {c.get('installment_status')} | R$ {c.get('commission_value')}")

# Agora vamos ver o que o filtro multi-select faz quando você seleciona status_parcela
# Quando você NÃO seleciona "Pago", o filtro funciona como: mostrar TODOS exceto... nada, pois é inclusivo
# Mas se você selecionar Pendente, Vencido, etc, vai mostrar apenas esses

print("\n" + "=" * 60)
print("SIMULANDO: Aprovada + Liberado + Aguardando Autorização")
print("=" * 60)

mapa = {
    'liberado': ['released', 'liberado'],
    'aguardando autorização': ['awaiting authorization', 'awaiting_authorization', 'aguardando autorização'],
    'aguardando liberação': ['awaiting_release', 'awaiting release']
}

def match_status(status, filtros):
    status = (status or '').lower()
    for filtro in filtros:
        valores = mapa.get(filtro.lower(), [filtro.lower()])
        if any(v in status for v in valores):
            return True
    return False

# Simular: filtrar por Liberado
filtro_selecionado = ['Liberado', 'Aguardando Autorização']
filtradas = [c for c in aprovadas if match_status(c.get('installment_status'), filtro_selecionado)]
print(f"Aprovadas + {filtro_selecionado}: {len(filtradas)}")

for c in filtradas:
    print(f"  - Contrato {c.get('numero_contrato')} | Sienge: {c.get('installment_status')}")
