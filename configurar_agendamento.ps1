# Script para configurar o Agendador de Tarefas do Windows
# Executa a sincronizacao todos os dias as 03:00

$taskName = "Sincronizacao Sistema Comissoes Young"
$taskPath = "\Young\"
$scriptPath = "C:\Users\Rafael\Desktop\Projeto comissoes\executar_sincronizacao.bat"
$workingDir = "C:\Users\Rafael\Desktop\Projeto comissoes"

# Remover tarefa existente se houver
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removendo tarefa existente..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Criar trigger para rodar diariamente as 03:00
$trigger = New-ScheduledTaskTrigger -Daily -At 3:00AM

# Criar acao para executar o script batch
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $workingDir

# Configuracoes da tarefa
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -WakeToRun

# Registrar a tarefa (executar como o usuario atual)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -TaskPath $taskPath `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Sincroniza dados do Sienge com Supabase diariamente as 03:00" `
        -ErrorAction Stop
    
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "TAREFA AGENDADA COM SUCESSO!"
    Write-Host "=============================================="
    Write-Host ""
    Write-Host "Nome: $taskName"
    Write-Host "Horario: Diariamente as 03:00"
    Write-Host "Script: $scriptPath"
    Write-Host ""
    Write-Host "Para verificar, abra o 'Agendador de Tarefas' do Windows"
    Write-Host "e procure pela pasta 'Young'"
    Write-Host ""
    Write-Host "Para testar manualmente, execute:"
    Write-Host "  python sincronizacao_agendada.py"
    Write-Host ""
} catch {
    Write-Host "ERRO ao criar tarefa: $_"
    Write-Host ""
    Write-Host "Tente executar este script como Administrador"
}
