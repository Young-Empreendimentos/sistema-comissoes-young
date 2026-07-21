-- Migração aplicada em produção (Supabase young-workspace / vvtympzatclvjaqucebr) em 2026-07-21.
-- Regra de negócio: a partir de MAIO/2026 o gatilho é 10% SEM ITBI (regra id 2).
--
-- Parte 1 (feita à mão junto desta migração): as 9 comissões de contratos de maio+
-- que ainda estavam como "10% + ITBI" (regra_gatilho_id null) foram setadas para id 2.
--
-- Parte 2 (esta migração): trigger que mantém isso automático — toda comissão de um
-- contrato com data_contrato >= 2026-05-01 que entrar/atualizar SEM regra definida
-- recebe a regra 10% (id 2). Não sobrescreve regra já definida manualmente.
-- Contratos anteriores a maio ficam como estão (o padrão histórico é "10% + ITBI").

create or replace function public.comissoes_set_regra_padrao_maio()
returns trigger
language plpgsql
as $$
begin
  if new.regra_gatilho_id is null then
    if exists (
      select 1 from public.comissoes_sienge_contratos ct
      where ct.numero_contrato::text = new.numero_contrato::text
        and ct.building_id::text   = new.building_id::text
        and ct.data_contrato >= date '2026-05-01'
    ) then
      new.regra_gatilho_id := 2;      -- "10%" (sem ITBI)
      new.regra_gatilho    := '10.0%';
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_comissoes_regra_padrao_maio on public.comissoes_sienge_comissoes;
create trigger trg_comissoes_regra_padrao_maio
before insert or update on public.comissoes_sienge_comissoes
for each row execute function public.comissoes_set_regra_padrao_maio();

-- Correção pontual dos registros já existentes (equivalente ao que foi rodado à mão):
-- update public.comissoes_sienge_comissoes co
--    set regra_gatilho_id = 2, regra_gatilho = '10.0%'
--   from public.comissoes_sienge_contratos ct
--  where ct.numero_contrato::text = co.numero_contrato::text
--    and ct.building_id::text = co.building_id::text
--    and ct.data_contrato >= date '2026-05-01'
--    and co.regra_gatilho_id is null;
