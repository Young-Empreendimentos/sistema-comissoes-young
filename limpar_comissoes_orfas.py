"""
Remove comissoes orfas do Supabase:
linhas cujo sienge_id nao existe mais na API Sienge (IDs antigos/cancelados).
Mantem comissoes manuais (origem='manual' ou numero_contrato iniciando com 'MANUAL-').

Uso:
    python limpar_comissoes_orfas.py           # modo dry-run (apenas lista)
    python limpar_comissoes_orfas.py --apply   # aplica as exclusoes
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from sienge_client import sienge_client

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

load_dotenv()
APPLY = '--apply' in sys.argv

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 70)
print("LIMPEZA DE COMISSOES ORFAS (DRY-RUN)" if not APPLY else "LIMPEZA DE COMISSOES ORFAS (APLICANDO)")
print("=" * 70)

print("\n[1/3] Buscando comissoes atuais no Sienge...")
commissions = sienge_client.get_commissions_all_companies()
ids_sienge = set()
for c in commissions:
    sid = c.get('commissionID') or c.get('id') or c.get('commissionId')
    if sid is not None:
        ids_sienge.add(str(sid))
print(f"      {len(ids_sienge)} ids unicos no Sienge")

print("\n[2/3] Buscando comissoes no Supabase...")
rows = sb.table('sienge_comissoes').select(
    'id,sienge_id,numero_contrato,building_id,broker_nome,unit_name,installment_status,commission_value'
).execute().data or []
print(f"      {len(rows)} linhas no Supabase")

def is_manual(row):
    numero_contrato = (row.get('numero_contrato') or '')
    if numero_contrato.startswith('MANUAL-'):
        return True
    try:
        if int(str(row.get('sienge_id') or '0')) < 0:
            return True
    except ValueError:
        pass
    return False

orfas = []
for r in rows:
    if is_manual(r):
        continue
    sid = str(r.get('sienge_id') or '')
    if not sid:
        continue
    if sid not in ids_sienge:
        orfas.append(r)

print(f"\n[3/3] Encontradas {len(orfas)} comissoes orfas (nao existem mais no Sienge):")
for r in orfas:
    print(
        f"  id_db={r.get('id')} sienge_id={r.get('sienge_id')} "
        f"contrato={r.get('numero_contrato')} bid={r.get('building_id')} "
        f"unidade={r.get('unit_name')} corretor={r.get('broker_nome')} "
        f"status={r.get('installment_status')} valor={r.get('commission_value')}"
    )

if not orfas:
    print("\nNada a fazer.")
    sys.exit(0)

if not APPLY:
    print("\n[DRY-RUN] Nada foi apagado. Rode novamente com --apply para excluir.")
    sys.exit(0)

print(f"\nExcluindo {len(orfas)} registros...")
ok = 0
err = 0
for r in orfas:
    try:
        sb.table('sienge_comissoes').delete().eq('id', r['id']).execute()
        ok += 1
    except Exception as e:
        err += 1
        print(f"  ERRO id={r['id']}: {str(e)[:120]}")

print(f"\nConcluido. Excluidas: {ok} | Erros: {err}")
