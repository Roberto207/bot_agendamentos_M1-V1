---
description: Workflow de Desenvolvimento e Manutenção do SaaS de Agendamentos
---

Sempre que atuar neste projeto, o Agente de IA deve seguir as orientações abaixo devido ao contexto da arquitetura atual.

- **Estado Atual**:
  - **Backend (`/backend/app`)**: Desenvolvido em FastAPI, SQLAlchemy e PostgreSQL. Estão prontas as rotas de Auth, Empresas, Serviços, Vínculos, Agendamentos (inclusive para IA) e um avançado **Dashboard de Métricas** (`dashboard_routes.py`).
  - **Frontend (`/frontend`)**: O diretório encontra-se VAZIO.
  - **Agente IA (Bot)**: Depende das rotas no formato POST `/agendamentos_whatssap/...`.

1. Compreensão do Contexto:
   - Sempre verifique o arquivo `explicacoes_projeto.txt` e `README.md` antes de codificar.
   - Atente-se à regra do `update_model_strict` (ignorar valores booleanos vazios/zeroes não intencionais vindos do front) e trate sempre os datetimes como naive timezone.
   - Os endpoints agora validam Ownership, ou seja, cheque sempre se a Entidade pertence ao `empresa_id` do usuário da sessão atual.

2. Execução Local do Backend:
   - Ative o `venv`.
   - Execute o Uvicorn a partir do diretório `/backend`: `uvicorn app.main:app --reload`.
   - Se alterar `models.py`, não se esqueça de rodar o Alembic: `alembic revision --autogenerate -m "sua alteracao"`.

3. Inicialização e Construção do Frontend (Prioridade):
   // turbo
   - Se instruído, use ferramentas modernas (ex: `npx create-vite@latest ./frontend --template react-ts`) para começar o painel SaaS.
   - Em seguida, garanta que todas as chamadas `fetch` ou `axios` incluam o token JWT gerado pelo `/auth_site/login_formula`. O frontend deve consumir o módulo de Dashboard já pronto e exibir gráficos de uso.

4. Interação Autônoma da IA com o Git:
   - O Agente de IA nunca deve forçar comandos Git autonomamente sem instruir o Desenvolvedor previamente sobre o que será salvo em commits. Solicite anuência e/ou repasse os comandos.
