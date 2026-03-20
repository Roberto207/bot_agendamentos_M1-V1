---
description: Atualização e depuração do comportamento do Agente IA (Integrações e WhatsApp)
---

# Workflow: Agente de IA e WhatsApp (Testes e Ajustes)

Nosso diferencial competitivo contra o n8n ou fluxos chatos robóticos engessados é o `Agente de IA customizado`. Portanto, modificar esse comportamento deve seguir diretrizes restritas.

## 1. Tratamento de API Keys da Empresa
- Lembre-se da arquitetura fundamental: o Agente IA se comunica em nome do cliente enviando a respectiva `API_KEY` da empresa no Header (`Authorization: Bearer <API_KEY>`) para rotas chaves `agend_routes.py`.
- Verifique constantemente se a passagem do payload de teste não deixou essa Key descoberta no código.

## 2. Responsabilidades do Agente
O Agente realiza a ponte entre o WhatsApp e a confirmação em banco. 
1. Interpreta linguagem natural.
2. Encontra a vaga livre no banco de dados através da rota `/ver_horarios_disponiveis`.
3. Tenta processar a reserva enviando na rota `/criar_agendamento`.
4. Apenas DEPOIS DE VALIDADO NO BACKEND (Retorno HTTP 200/201), ele invoca a API do Google Sheets e marca o horário no Google Calendar.
- **Nunca autorize o agente a marcar no Sheets antes da API do PostgreSQL confirmar a vaga.**

## 3. Comandos e Testes Locais
O Agente NUNCA DEVE rodar comandos de git no terminal (user global rule). Se houver que mudar versionamento para a IA, peça para o humano rodar os comandos no shell.
Para iniciar o ambiente virtual, execute: `.\.venv\Scripts\activate.ps1` ou `source venv/bin/activate`.
