@echo off
echo ============================================================
echo   Reiniciando Servidor - Sistema de Comissoes Young
echo ============================================================
echo.
echo Conectando ao servidor 46.62.245.62...
echo Senha: j7jCJt3qkgJwWkWn4hEg
echo.
echo Apos conectar, execute estes comandos:
echo.
echo   systemctl restart nginx
echo   systemctl restart sistema-comissoes-young
echo   systemctl restart sistema-comissoes-young-scheduler
echo   systemctl status sistema-comissoes-young
echo.
echo ============================================================
echo.
ssh root@46.62.245.62
pause
