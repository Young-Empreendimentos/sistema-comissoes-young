# 📧 Configuração de E-mail - Sistema de Comissões Young

## Passo a Passo Completo

### 1️⃣ Criar o arquivo `.env`

Na pasta `C:\Users\Rafael\Desktop\Projeto comissões`, crie um arquivo chamado `.env` (sem extensão) com o seguinte conteúdo:

```env
# ==================== SUPABASE ====================
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-ou-service-role

# ==================== SIENGE API ====================
SIENGE_BASE_URL=https://api.sienge.com.br/youngemp/public/api
SIENGE_USERNAME=seu-usuario-sienge
SIENGE_PASSWORD=sua-senha-sienge
SIENGE_COMPANY_ID=5

# ==================== E-MAIL (SMTP) ====================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
EMAIL_FROM=sistema@youngempreendimentos.com.br

# ==================== FLASK ====================
FLASK_PORT=5000
FLASK_SECRET_KEY=chave-secreta-aleatoria
```

---

### 2️⃣ Configurar Gmail para Envio de E-mails

O Gmail não aceita mais senhas normais para aplicativos. Você precisa criar uma **Senha de App**.

#### Passo 2.1 - Ativar Verificação em 2 Etapas
1. Acesse: https://myaccount.google.com/security
2. Clique em "Verificação em duas etapas"
3. Siga as instruções para ativar

#### Passo 2.2 - Criar Senha de App
1. Acesse: https://myaccount.google.com/apppasswords
2. Em "Selecionar app", escolha "Outro (nome personalizado)"
3. Digite: `Sistema Comissões Young`
4. Clique em "Gerar"
5. **COPIE a senha de 16 caracteres** (ex: `abcd efgh ijkl mnop`)
6. Use essa senha no `SMTP_PASSWORD` (sem espaços)

---

### 3️⃣ Exemplo de `.env` Preenchido

```env
# SUPABASE
SUPABASE_URL=https://xyzabc123.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# SIENGE
SIENGE_BASE_URL=https://api.sienge.com.br/youngemp/public/api
SIENGE_USERNAME=usuario_api
SIENGE_PASSWORD=senha_api
SIENGE_COMPANY_ID=5

# E-MAIL
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=sistema@youngempreendimentos.com.br
SMTP_PASSWORD=abcdefghijklmnop
EMAIL_FROM=sistema@youngempreendimentos.com.br

# FLASK
FLASK_PORT=5000
FLASK_SECRET_KEY=minha-chave-super-secreta-123
```

---

### 4️⃣ Configurar E-mails no Supabase

No Supabase, você precisa ter a tabela `configuracoes_emails` com os e-mails de destino.

Execute este SQL no Supabase:

```sql
-- Criar tabela se não existir
CREATE TABLE IF NOT EXISTS configuracoes_emails (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    descricao VARCHAR(200),
    emails TEXT[] NOT NULL,
    ativo BOOLEAN DEFAULT true,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Inserir configurações de e-mail
INSERT INTO configuracoes_emails (tipo, descricao, emails, ativo) VALUES
('direcao', 'E-mails da Direção para aprovação', ARRAY['eduardo@youngempreendimentos.com.br'], true),
('financeiro', 'E-mails do Financeiro para pagamento', ARRAY['suelen@youngempreendimentos.com.br', 'lais@youngempreendimentos.com.br'], true)
ON CONFLICT DO NOTHING;
```

---

### 5️⃣ Testar Envio de E-mail

Após configurar, você pode testar executando no Python:

```python
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

# Configurações
smtp_host = os.getenv('SMTP_HOST')
smtp_port = int(os.getenv('SMTP_PORT'))
smtp_user = os.getenv('SMTP_USER')
smtp_password = os.getenv('SMTP_PASSWORD')
email_from = os.getenv('EMAIL_FROM')

# Teste
msg = MIMEText('Este é um teste do Sistema de Comissões Young!')
msg['Subject'] = 'Teste de E-mail - Sistema Comissões'
msg['From'] = email_from
msg['To'] = 'seu-email@teste.com'  # Altere para seu e-mail

try:
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    print('✅ E-mail enviado com sucesso!')
except Exception as e:
    print(f'❌ Erro: {e}')
```

---

### 6️⃣ Alternativas ao Gmail

Se preferir não usar Gmail, outras opções:

#### Outlook/Hotmail
```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=seu-email@outlook.com
SMTP_PASSWORD=sua-senha
```

#### Servidor SMTP Próprio
```env
SMTP_HOST=mail.youngempreendimentos.com.br
SMTP_PORT=587
SMTP_USER=sistema@youngempreendimentos.com.br
SMTP_PASSWORD=senha-do-email
```

#### SendGrid (Serviço de E-mail)
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=sua-api-key-sendgrid
```

---

### 7️⃣ Verificar se está funcionando

Após configurar, reinicie o servidor e:

1. Faça login como gestor
2. Vá em "Visualizar Comissões"
3. Selecione algumas comissões
4. Clique em "Enviar para Aprovação"
5. Verifique se o e-mail chegou para a direção

---

## ⚠️ Problemas Comuns

### "Authentication failed"
- Verifique se a senha de app está correta (sem espaços)
- Verifique se a verificação em 2 etapas está ativa

### "Connection refused"
- Verifique se o SMTP_HOST e SMTP_PORT estão corretos
- Verifique se seu firewall não está bloqueando

### "Less secure apps"
- O Gmail não aceita mais "apps menos seguros"
- Use sempre Senha de App

---

## 📞 Suporte

Se precisar de ajuda:
1. Verifique os logs do servidor (terminal)
2. Teste o envio manual com o script Python acima
3. Verifique as configurações no Supabase

