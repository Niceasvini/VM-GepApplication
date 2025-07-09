#!/bin/bash
# Script para reiniciar o servidor com configurações otimizadas
pkill -f gunicorn
sleep 2
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload --timeout 120 --workers 1 main:app