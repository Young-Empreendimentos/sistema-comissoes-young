-- Migração aplicada em produção (Supabase young-workspace / vvtympzatclvjaqucebr) em 2026-07-03.
-- Objetivo: "validação da diretoria" — toda conta nova fica pendente até liberação
-- de Direção OU Admin. Corretores ganham colunas de aprovação; backfill preserva o
-- acesso de quem já usa o sistema hoje (não trava ninguém).

-- Colunas de aprovação para corretores (gestores já têm 'aprovado' em comissoes_usuarios)
alter table public.comissoes_sienge_corretores
  add column if not exists aprovado boolean not null default false,
  add column if not exists aprovado_por text,
  add column if not exists aprovado_em timestamptz;

-- Backfill: corretores que JÁ têm acesso (senha cadastrada) continuam entrando
update public.comissoes_sienge_corretores
   set aprovado = true,
       aprovado_por = coalesce(aprovado_por, 'backfill (acesso pre-existente)'),
       aprovado_em = coalesce(aprovado_em, now())
 where senha_hash is not null
   and aprovado is distinct from true;

-- Backfill: gestores ativos com senha continuam entrando
-- (fecha o caminho usuario/senha sem travar os atuais)
update public.comissoes_usuarios
   set aprovado = true
 where coalesce(ativo, true) = true
   and password_hash is not null
   and aprovado is distinct from true;
