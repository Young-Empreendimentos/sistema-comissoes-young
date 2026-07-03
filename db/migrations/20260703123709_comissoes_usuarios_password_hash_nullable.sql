-- Migração aplicada em produção (Supabase young-workspace / vvtympzatclvjaqucebr) em 2026-07-03.
-- Corrige bug: gestores que entram via Google (Supabase Auth) não têm senha própria.
-- O fluxo de cadastro pendente (registrar_pendente) insere sem password_hash;
-- com a coluna NOT NULL, o INSERT falhava e o pedido de acesso nunca era gravado
-- (sintoma: "não aparece quando a pessoa pede autorização").

alter table public.comissoes_usuarios
  alter column password_hash drop not null;
