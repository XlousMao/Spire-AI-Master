@echo off
:: 切換到專案根目錄
cd /d "%~dp0.."

:: 这里的 python 应该指向你的 Python 环境
:: 如果有虚拟环境，请取消注释下一行并修改路径
:: call .venv\Scripts\activate.bat

:: 启动 AI 后端
python main.py
