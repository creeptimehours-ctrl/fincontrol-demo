@echo off
chcp 65001 >nul
title FinControl - Sistema Financeiro
cd /d "%~dp0"
echo.
echo  FinControl - iniciando o servidor...
echo  Depois de abrir, acesse: http://localhost:8501
echo  Para fechar, feche esta janela ou pressione Ctrl+C
echo.
streamlit run app.py
pause
