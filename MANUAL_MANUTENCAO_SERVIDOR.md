# Manual de Manutenção do Servidor - Sistema de Comissões Young

## Índice
1. [Informações do Servidor](#1-informações-do-servidor)
2. [Como Acessar o Servidor](#2-como-acessar-o-servidor)
3. [Estrutura de Arquivos no Servidor](#3-estrutura-de-arquivos-no-servidor)
4. [Como Atualizar o Código](#4-como-atualizar-o-código)
5. [Como Editar Arquivos Diretamente no Servidor](#5-como-editar-arquivos-diretamente-no-servidor)
6. [Gerenciamento dos Serviços](#6-gerenciamento-dos-serviços)
7. [Como Ver Logs e Erros](#7-como-ver-logs-e-erros)
8. [Backup e Restauração](#8-backup-e-restauração)
9. [Problemas Comuns e Soluções](#9-problemas-comuns-e-soluções)
10. [Comandos Úteis](#10-comandos-úteis)

---

## 1. Informações do Servidor

| Item | Valor |
|------|-------|
| **IP do Servidor** | 46.62.245.62 |
| **Provedor** | Hetzner |
| **Sistema Operacional** | Ubuntu |
| **Usuário Root** | root |
| **Senha Root** | j7jCJt3qkgJwWkWn4hEg |
| **URL da Aplicação** | http://46.62.245.62 |
| **Banco de Dados** | Supabase (externo) |

---

## 2. Como Acessar o Servidor

### Pelo Windows (PowerShell ou CMD)

1. Abra o **PowerShell** ou **Prompt de Comando**
2. Digite o comando:
   ```
   ssh root@46.62.245.62
   ```
3. Se perguntar "Are you sure you want to continue connecting?", digite `yes` e pressione Enter
4. Digite a senha: `j7jCJt3qkgJwWkWn4hEg` (a senha não aparece enquanto digita, é normal)
5. Pressione Enter

### Pelo Mac/Linux (Terminal)

1. Abra o **Terminal**
2. Digite:
   ```
   ssh root@46.62.245.62
   ```
3. Digite a senha quando solicitado

### Usando um Programa (mais fácil para iniciantes)

Recomendo instalar o **PuTTY** (Windows) ou **Termius** (Windows/Mac):

**PuTTY:**
1. Baixe em: https://www.putty.org/
2. Abra o PuTTY
3. Em "Host Name", digite: `46.62.245.62`
4. Clique em "Open"
5. Digite usuário: `root`
6. Digite a senha

---

## 3. Estrutura de Arquivos no Servidor

```
/home/youngapp/sistema-comissoes-young/
├── app.py                    # Aplicação principal (Flask)
├── .env                      # Variáveis de ambiente (senhas, configs)
├── venv/                     # Ambiente virtual Python
├── static/                   # Arquivos CSS, JS, imagens
│   ├── css/style.css
│   ├── js/app.js
│   └── js/direcao.js
├── templates/                # Páginas HTML
│   ├── dashboard.html
│   ├── dashboard_direcao.html
│   └── login_unificado.html
├── gunicorn_config.py        # Configuração do servidor
├── scheduler.py              # Agendador de tarefas
├── sync_sienge_supabase.py   # Sincronização com Sienge
└── aprovacao_comissoes.py    # Lógica de aprovação
```

---

## 4. Como Atualizar o Código

### Método 1: Via Git (Recomendado)

**No seu computador local:**

1. Faça as alterações no código usando o **Cursor** ou **VS Code**
2. Salve os arquivos
3. Abra o terminal no projeto e execute:
   ```bash
   git add .
   git commit -m "Descrição da alteração"
   git push origin main
   ```

**No servidor (via SSH):**

1. Conecte no servidor:
   ```bash
   ssh root@46.62.245.62
   ```

2. Vá para o diretório da aplicação:
   ```bash
   cd /home/youngapp/sistema-comissoes-young
   ```

3. Baixe as atualizações:
   ```bash
   git pull origin main
   ```

4. Reinicie a aplicação:
   ```bash
   systemctl restart sistema-comissoes-young
   systemctl restart sistema-comissoes-young-scheduler
   ```

5. Verifique se está funcionando:
   ```bash
   systemctl status sistema-comissoes-young
   ```

### Método 2: Edição Direta no Servidor

Veja a seção 5 abaixo.

---

## 5. Como Editar Arquivos Diretamente no Servidor

### Usando o Editor Nano (mais fácil)

1. Conecte no servidor
2. Vá para o diretório:
   ```bash
   cd /home/youngapp/sistema-comissoes-young
   ```

3. Abra o arquivo para editar:
   ```bash
   nano nome_do_arquivo.py
   ```
   
   Exemplos:
   ```bash
   nano app.py                    # Editar aplicação principal
   nano templates/dashboard.html  # Editar página do dashboard
   nano static/css/style.css      # Editar estilos
   nano .env                      # Editar configurações
   ```

4. **Comandos do Nano:**
   - `Ctrl + O` = Salvar
   - `Enter` = Confirmar nome do arquivo
   - `Ctrl + X` = Sair
   - `Ctrl + W` = Buscar texto
   - `Ctrl + K` = Recortar linha
   - `Ctrl + U` = Colar linha
   - Setas = Mover cursor

5. Após editar, reinicie a aplicação:
   ```bash
   systemctl restart sistema-comissoes-young
   ```

### Usando o VS Code Remoto (mais confortável)

1. Instale a extensão "Remote - SSH" no VS Code
2. Pressione `Ctrl+Shift+P` e digite "Remote-SSH: Connect to Host"
3. Digite: `root@46.62.245.62`
4. Digite a senha
5. Abra a pasta `/home/youngapp/sistema-comissoes-young`
6. Edite os arquivos normalmente
7. Salve e reinicie o serviço via terminal

---

## 6. Gerenciamento dos Serviços

### Serviços do Sistema

| Serviço | Descrição |
|---------|-----------|
| `sistema-comissoes-young` | Aplicação Flask (site) |
| `sistema-comissoes-young-scheduler` | Agendador (sincronização 6h) |
| `nginx` | Servidor web (proxy) |

### Comandos para Gerenciar Serviços

```bash
# Ver status do serviço
systemctl status sistema-comissoes-young

# Parar o serviço
systemctl stop sistema-comissoes-young

# Iniciar o serviço
systemctl start sistema-comissoes-young

# Reiniciar o serviço (usar após alterações)
systemctl restart sistema-comissoes-young

# Ver se o serviço inicia automaticamente
systemctl is-enabled sistema-comissoes-young
```

### Reiniciar Tudo de Uma Vez

```bash
systemctl restart sistema-comissoes-young
systemctl restart sistema-comissoes-young-scheduler
systemctl restart nginx
```

---

## 7. Como Ver Logs e Erros

### Ver Logs da Aplicação

```bash
# Últimas 50 linhas de log
journalctl -u sistema-comissoes-young -n 50

# Ver logs em tempo real (Ctrl+C para sair)
journalctl -u sistema-comissoes-young -f

# Logs do scheduler
journalctl -u sistema-comissoes-young-scheduler -n 50

# Logs do Nginx
tail -f /var/log/nginx/error.log
```

### Ver Logs de Acesso

```bash
# Quem está acessando o site
tail -f /var/log/nginx/access.log
```

---

## 8. Backup e Restauração

### Fazer Backup dos Arquivos

```bash
# No servidor, criar backup
cd /home/youngapp
tar -czvf backup_$(date +%Y%m%d).tar.gz sistema-comissoes-young/

# Copiar backup para seu computador (execute no seu PC)
scp root@46.62.245.62:/home/youngapp/backup_*.tar.gz C:\Users\SeuUsuario\Desktop\
```

### Fazer Backup do .env (IMPORTANTE!)

```bash
# No servidor
cp /home/youngapp/sistema-comissoes-young/.env /home/youngapp/.env.backup
```

### Restaurar de um Backup

```bash
# No servidor
cd /home/youngapp
tar -xzvf backup_XXXXXXXX.tar.gz
systemctl restart sistema-comissoes-young
```

---

## 9. Problemas Comuns e Soluções

### Problema: Site fora do ar

1. Verificar se o serviço está rodando:
   ```bash
   systemctl status sistema-comissoes-young
   ```

2. Se estiver "failed", reinicie:
   ```bash
   systemctl restart sistema-comissoes-young
   ```

3. Se continuar falhando, veja o log:
   ```bash
   journalctl -u sistema-comissoes-young -n 100
   ```

### Problema: Erro 502 Bad Gateway

O Gunicorn (aplicação) não está respondendo:
```bash
systemctl restart sistema-comissoes-young
systemctl restart nginx
```

### Problema: Erro 500 Internal Server Error

Erro no código Python. Ver logs:
```bash
journalctl -u sistema-comissoes-young -n 100
```

### Problema: Alterações não aparecem no site

1. Certifique-se que salvou o arquivo
2. Reinicie o serviço:
   ```bash
   systemctl restart sistema-comissoes-young
   ```
3. Limpe o cache do navegador (Ctrl+F5)

### Problema: Não consigo conectar via SSH

1. Verifique se digitou o IP correto: `46.62.245.62`
2. Verifique se está usando `root@` antes do IP
3. Verifique sua conexão com a internet
4. Se der erro de "host key", execute no seu PC:
   ```bash
   ssh-keygen -R 46.62.245.62
   ```

### Problema: Sincronização não está funcionando

```bash
# Verificar scheduler
systemctl status sistema-comissoes-young-scheduler

# Se estiver parado
systemctl restart sistema-comissoes-young-scheduler

# Executar sincronização manualmente
cd /home/youngapp/sistema-comissoes-young
source venv/bin/activate
python -c "from sync_sienge_supabase import SiengeSupabaseSync; s = SiengeSupabaseSync(); s.sync_all()"
```

---

## 10. Comandos Úteis

### Navegação

```bash
cd /home/youngapp/sistema-comissoes-young  # Ir para pasta do projeto
ls -la                                      # Listar arquivos
pwd                                         # Ver pasta atual
```

### Arquivos

```bash
cat arquivo.py      # Ver conteúdo do arquivo
nano arquivo.py     # Editar arquivo
rm arquivo.py       # Deletar arquivo (CUIDADO!)
cp arquivo.py copia.py  # Copiar arquivo
mv arquivo.py novo.py   # Renomear/mover arquivo
```

### Sistema

```bash
df -h               # Ver espaço em disco
free -m             # Ver memória RAM
top                 # Ver processos (q para sair)
reboot              # Reiniciar servidor (CUIDADO!)
```

### Rede

```bash
curl http://localhost:5000/health   # Testar se aplicação responde
netstat -tlnp                       # Ver portas em uso
```

---

## Checklist de Atualização

Quando for atualizar o sistema, siga este checklist:

- [ ] Fazer backup do .env
- [ ] Conectar no servidor via SSH
- [ ] Ir para o diretório do projeto
- [ ] Executar `git pull origin main`
- [ ] Se houver novas dependências: `source venv/bin/activate && pip install -r requirements.txt`
- [ ] Reiniciar serviços: `systemctl restart sistema-comissoes-young`
- [ ] Verificar status: `systemctl status sistema-comissoes-young`
- [ ] Testar o site no navegador
- [ ] Verificar logs se houver problemas

---

## Contatos de Emergência

- **Hetzner Console:** https://console.hetzner.cloud/
- **Supabase Dashboard:** https://supabase.com/dashboard

---

*Manual criado em 29/01/2026*
*Última atualização: 29/01/2026*
