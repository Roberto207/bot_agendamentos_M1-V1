# Sistema de Agendamentos com I.A. via WhatsApp (SaaS)

## Descrição
Uma plataforma SaaS de agendamentos automatizados via WhatsApp usando **Agente de IA customizado**, FastAPI, PostgreSQL, SQLAlchemy e Alembic.

Diferente de sistemas convencionais (como n8n), nosso sistema conta com um **Agente de IA** próprio, focado em entender as solicitações do cliente via WhatsApp, em linguagem natural, verificando disponibilidade e realizando agendamentos, remarcações e cancelamentos através da nossa API.

Além disso, a plataforma inclui uma interface **Frontend (Site SaaS)**, onde empreendedores poderão se cadastrar, registrar suas empresas e ter acesso à sua própria integração com o Agente de IA de WhatsApp. O painel administrativo já conta com rotas de **Dashboard** no backend para acompanhamento completo de métricas (taxa de ocupação, mapas de calor, perfil de cancelamentos, etc).

O Agente de IA também se encarregará de sincronizar todos os agendamentos registrados no banco de dados e repassados à API, integrando os dados diretamente com o **Google Sheets** e marcando horários no **Google Calendar**.

---

## Principais Modelos / Estrutura de Banco de Dados
Com base no modelo em SQLAlchemy:
- **Usuario (`usuarios_site`)**: Usuários cadastrados pelo painel SaaS (Empreendedores / Donos de conta).
- **Empresa (`empresas`)**: Empresas vinculadas aos usuários. Cada empresa possui uma `api_key` única que permite ao Agente de IA interagir com seus dados livremente e de forma segura.
- **HorarioFuncionamento (`horarios_funcionamento`)**: Parametrização dos dias da semana em que a empresa trabalha e os horários de abertura e fechamento.
- **Servicos (`servicos`)**: Catálogo de serviços da empresa. Contém campos para duração de atendimentos, buffer de tempo extra (limpeza) e precificação.
- **Profissional (`profissionais`)**: Profissionais liberais na empresa.
- **Cliente (`clientes`)**: Dados do cliente final que interage no WhatsApp.
- **Agendamento (`agendamentos`)**: Histórico com os dados relatórios (Cliente, Empresa, Serviço, Profissional, status de confirmação, horários de início e fim).
- **UsuarioEmpresa (`usuarios_empresas`)**: Tabela de vínculo para o sistema multi-usuário (Vínculos), permitindo múltiplos colaboradores (Operador, Gerenciador, Admin) por empresa.
- **HorarioProfissional (`horarios_profissionais`)**: Horários específicos de cada profissional, validados contra os horários da empresa.

---

## Estrutura de Rotas da API e Tarefas
A API (FastAPI) orquestra todas as requisições em uma arquitetura modular por rotas:
- **`auth_site_router.py`**: Gerencia a autenticação e administração dos donos de empresas no portal SaaS (Cadastro, Login).
- **`empresas_routes.py`**: CRUD e registro de empresas ligadas ao usuário autenticado, mantendo dados isolados.
- **`vinculos_routes.py`**: Gerencia o sistema multi-usuário via convites e níveis de acesso.
- **`servicos_routes.py`**: CRUD de serviços de cada organização e gestão detalhada de profissionais e horários específicos.
- **`agend_routes.py`**: Rotas vitais consumidas pelo **Agente de IA**:
  - GET `/agendamentos/ver_horarios_disponiveis`
  - POST `/agendamentos_whatssap/criar_agendamento`
  - POST `/agendamentos_whatssap/cancelar_agendamento`
  - POST `/agendamentos_whatssap/concluir_agendamento`

---

## Refinamentos Técnicos Recentes
- **Strict Update Utility**: Implementação da função `update_model_strict` para evitar que valores padrão indesejados (como `0` ou strings vazias) de formulários inconsistentes sobrescrevam dados reais no banco.
- **Timezone Normalization**: Padronização de todos os objetos de tempo para o formato "naive" (sem timezone) em nível de API para evitar erros de comparação (`TypeError`).
- **Validação de Propriedade**: Checagem rigorosa de `empresa_id` em todas as relações entre serviços e profissionais, impedindo associações indevidas.

O Agente IA injeta no Header da chamada: `Authorization: Bearer <API_KEY>` fornecida pela empresa, autenticando instantaneamente para validar vagas no PostgreSQL sem risco de duplicidade.

---

## Tecnologias
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic (Migrations), Pydantic
- **Banco de Dados:** PostgreSQL (psycopg2)
- **Infra:** Docker
- **Automação IA:** Agente Customizado de Linguagem Natural, WhatsApp Webhooks 
- **Outras Integrações:** Google Sheets, Google Calendar API
