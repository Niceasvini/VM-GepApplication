@echo off
set HOST=31.97.172.228
set USER=root
set REMOTE_SCRIPT=/opt/apps/vianaemoura/deploy.sh
 
echo 🚀 Iniciando deploy app na Hostinger (%HOST%)...
 
ssh %USER%@%HOST% "bash %REMOTE_SCRIPT%"
 
echo ✅ Deploy finalizado!
pause