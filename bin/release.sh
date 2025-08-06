#!/bin/bash
echo "🚀 Heroku Release Phase - Preparing Knowledge Base"
echo "Current directory: $(pwd)"
echo "Files present:"
ls -la

# Executa o script de inicialização da base de conhecimento
python heroku_init.py

echo "✅ Release phase completed"
