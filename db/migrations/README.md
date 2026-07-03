# Migrações do banco (Supabase)

Estas migrações **já foram aplicadas em produção** no projeto Supabase
`young-workspace` (`vvtympzatclvjaqucebr`) via ferramenta administrativa (MCP),
e estão registradas em `supabase_migrations.schema_migrations`.

Os arquivos aqui servem para **rastreabilidade/histórico** — para que mudanças de
banco não fiquem "invisíveis" no código. O projeto **não** usa o Supabase CLI
(`supabase db push`) hoje; portanto **não rode** essas migrações de novo sem
verificar antes o que já está aplicado.

| Versão | Descrição |
|---|---|
| `20260703114205` | Desacopla o Comissões do `user_roles` global (função `comissoes_is_admin` + policy de DELETE de corretores) |
| `20260703120555` | "Validação da diretoria": colunas `aprovado`/`aprovado_por`/`aprovado_em` em corretores + backfill dos acessos atuais |

> A **regra de acesso** (exigir aprovação em todos os logins) é aplicada no
> código Flask (`auth_manager.py` / `app.py`), porque o app conecta com a
> `service_role` e ignora o RLS.
