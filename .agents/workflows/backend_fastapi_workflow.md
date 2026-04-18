---
description: Workflow para criar novas rotas no FastAPI (Backend SaaS)
---

# Workflow: Desenvolvimento de Backend (FastAPI)

Este workflow define as regras e diretrizes estritas que **DEVEM** ser seguidas ao criar, modificar ou manter rotas e lógicas do backend no projeto de Agendamentos.

## 1. Regra de Atualização Restrita (`update_model_strict`)
Sempre que você for atualizar os dados de um modelo recebidos via Pydantic (especialmente em rotas `PUT` ou `PATCH`), utilize a função utilitária `update_model_strict`.
- **Por quê?** Ela impede que valores considerados "sujos" ou padrões indesejados originados do front-end (como `0`, `0.0`, ou strings vazias `""`) sobrescrevam campos íntegros já existentes no banco de dados.

## 2. Tratamento e Normalização de Timezone
- **Erro Evitado:** `TypeError: can't compare offset-naive and offset-aware times`.
- **Diretriz:** Todas as rotas devem normalizar os objetos de tempo (datetime/time) para "naive" usando `.replace(tzinfo=None)` ANTES de salvá-los no banco em colunas de tempo.

## 3. Validação de Propriedade (Ownership) Rigorosa
Nunca permita que uma entidade acesse dados de outra sem comprovação de vínculo.
- **Ao associar registros (Ex: Serviço <-> Profissional):** Garanta que ambos os `IDs` existam no banco e pertençam à MESMA corporação (`empresa_id` associada ao usuário em sessão).
- Isso vale para criar, alterar ou listar.

## 4. O Agente de IA e o Backend
Lembre-se que certas rotas do backend (como em `agend_routes.py`) são consumidas pelo **Agente de IA customizado** que cuida do WhatsApp.
- Nessas rotas, o parâmetro de autenticação não é baseado em login de usuário padrão, mas sim através de uma `API_KEY` injetada via Header (`Authorization: Bearer <API_KEY>`).
- Não quebre essa dependência caso for refatorar auth.

## // turbo
1. Em caso de linting e validação formal, rode `pytest` localmente se aplicável para garantir a estabilidade antes do commit.
