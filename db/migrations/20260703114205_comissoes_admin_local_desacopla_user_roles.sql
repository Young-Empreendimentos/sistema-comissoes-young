-- Migração aplicada em produção (Supabase young-workspace / vvtympzatclvjaqucebr) em 2026-07-03.
-- Objetivo: desacoplar o sistema de Comissões da tabela global `user_roles`.
-- A permissão de admin passa a vir da própria tabela do sistema (comissoes_usuarios).

-- Função local de admin do sistema de Comissões (não depende do user_roles global).
-- Mapeia auth.uid() -> auth.users.email -> comissoes_usuarios.email
create or replace function public.comissoes_is_admin(uid uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.comissoes_usuarios cu
    join auth.users u on lower(u.email) = lower(cu.email)
    where u.id = uid
      and cu.is_admin = true
      and coalesce(cu.ativo, true) = true
  );
$$;

comment on function public.comissoes_is_admin(uuid) is
  'Admin do sistema de Comissões via comissoes_usuarios (is_admin+ativo). Substitui o uso do user_roles global na RLS de comissoes_*.';

-- Trocar a política de DELETE de corretores para usar a checagem local
drop policy if exists corretores_delete on public.comissoes_sienge_corretores;
create policy corretores_delete on public.comissoes_sienge_corretores
  for delete
  using ( public.comissoes_is_admin() );
