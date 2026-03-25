# 🤖 Agente Orquestrador de IA - WhatsApp

Agente de IA para atendimento automatizado via WhatsApp e gerenciamento de agendamentos.

--- #

## 📁 Estrutura de Arquivos
curl -X POST 'http://localhost:8001/webhook/whatsapp/31d2f2fb7f27022edf14430aeae8dde7' \
  -H 'Content-Type: application/json' \
  -d '{"from": "5511999999999", "message": "prefiro as 14"}'
```
agente_orquestrador/
├── README.md                      # Este arquivo
├── ai_whatsapp_orchestrator.py    # Código principal do agente
├── requirements.orchestrator.txt  # Dependências Python
├── .env.orchestrator.example      # Exemplo de configuração
└── test_orchestrator.py           # Suite de testes
```

**Documentação completa:** Ver `.agents/agente_ia_orquestrador.md`

---

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
cd agente_orquestrador
pip install -r requirements.orchestrator.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
cp .env.orchestrator.example .env.orchestrator
nano .env.orchestrator  # Editar com suas credenciais
```

**Variáveis essenciais:**
```env
API_BASE_URL=http://localhost:8000
XAI_API_KEY=gsk-...  # Sua chave Groq (gratuita)
XAI_MODEL=llama-3.3-70b-versatile
XAI_BASE_URL=https://api.groq.com/openai/v1
LLM_PROVIDER=groq
```

**📖 Guia completo:** Ver `CONFIGURACAO_GROQ.md`

### 3. Executar o Agente

```bash
# Modo desenvolvimento
python ai_whatsapp_orchestrator.py

# Modo produção
uvicorn ai_whatsapp_orchestrator:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## 🧪 Testar Localmente

### Simular Mensagem do WhatsApp

```bash
curl -X POST "http://localhost:8001/webhook/whatsapp/sua_api_key_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5511999999999",
    "message": "Oi, quero marcar um corte amanhã às 14h"
  }'
```

### Executar Testes Automatizados

```bash
pytest test_orchestrator.py -v
```

---

## 🔗 Integração com Backend

O agente consome as seguintes rotas da API FastAPI:

| Rota | Método | Descrição |
|------|--------|-----------|
| `/agendamentos/criar` | POST | Criar agendamento |
| `/agendamentos/cancelar` | POST | Cancelar agendamento |
| `/agendamentos/concluir` | POST | Concluir agendamento |
| `/agendamentos/horarios_ocupados` | GET | Ver horários ocupados |
| `/agendamentos/seus_agendamentos` | GET | Listar agendamentos do cliente |

**Autenticação:** Header `Authorization: Bearer {api_key}` em todas as requisições.

---

## 📊 Fluxo de Funcionamento

```
WhatsApp → Webhook → Orquestrador → LLM (análise) → API Backend → PostgreSQL
                                                                        ↓
                                                    Google Sheets + Calendar
```

**Exemplo de Conversa:**

```
Cliente: "Oi, quero marcar um corte"
Bot: "Para continuar, preciso saber seu nome..."
Cliente: "João Silva"
Bot: "Para qual dia você gostaria de agendar?"
Cliente: "Amanhã às 14h"
Bot: "Confirme os dados... Confirma? (Sim/Não)"
Cliente: "Sim"
Bot: "✅ Agendamento confirmado! ..."
```

---

## 🎯 Recursos Principais

- ✅ **Linguagem Natural:** Entende "amanhã às 14h", "próxima segunda", etc
- ✅ **Contextualização:** Mantém histórico da conversa
- ✅ **Multi-empresa:** Isolamento por API Key
- ✅ **Validação Inteligente:** Coleta dados progressivamente
- ✅ **Integrações:** Google Sheets + Calendar (pós-confirmação),post e get no banco de dados via fastapi

---

## 📖 Documentação Completa

Para arquitetura detalhada, casos de uso e deployment em produção, consulte:

**`.agents/agente_ia_orquestrador.md`**

---

## 🐛 Troubleshooting

### Problema: "Erro ao conectar com API"
**Solução:** Verifique se o backend FastAPI está rodando na porta 8000.

### Problema: "LLM não identifica intenção"
**Solução:** Configure `OPENAI_API_KEY` no `.env.orchestrator` ou use modo mock.

### Problema: "Contexto perdido entre mensagens"
**Solução:** Configure Redis para persistência (ver `.env.orchestrator.example`).

---

## 📞 Suporte

- **Documentação geral:** `/README.md` (raiz do projeto)
- **Workflows do projeto:** `.agents/workflows/`
- **Rotas de agendamento:** `/backend/app/agend_routes.py`

---

**Versão:** 1.0.0  
**Licença:** Proprietária
