---
description: Procedimento seguro para criar e aplicar migrations no Banco de Dados (Alembic)
---

# Workflow: Manutenção de Banco de Dados (PostgreSQL / Alembic)

A base do sistema SaaS de agendamento se apoia num banco de dados PostgreSQL estruturado. Ao adicionar, remover ou modificar propriedades nos arquivos `models.py`, você deve gerar as migrações de forma correta e segura.

## Passo a Passo Seguro para Migrations

1. **Alteração no Código**
   Sempre modifique primeiro os modelos declarativos SQLAlchemy no arquivo `models.py` correspondente.

2. **Geração Automática (Autogenerate)**
   Ao gerar a migration, rode o comando abaixo no terminal:
   ```bash
   alembic revision --autogenerate -m "Descreva de forma clara a alteração, Ex: adicao de campo x na tabela y"
   ```

3. **Revisão Manual do Script (Obrigatório)**
   O autogenerate do Alembic às vezes comete erros gravíssimos:
   - Ele pode tentar realizar um drop tables não intercional caso perca o escopo de metadados.
   - Ele pode criar constrains com nomes difíceis de manutenir caso não estejam parametrizadas na Base.
   > **AÇÃO:** Sempre abra o arquivo criado na pasta `alembic/versions/` e confira a integridade das funções `upgrade()` e `downgrade()`.

4. **Aplicação (Upgrade)**
   Após ter CERTEZA que o script não tem instruções destrutivas não desejadas, aplique a migração no banco de desenvolvimento:
   ```bash
   alembic upgrade head
   ```

5. **Acompanhamento no Backend**
   Lembre-se de refletir quaisquer novidades de colunas/modelos nos devidos arquivos `schemas.py` de resposta/validação (Pydantic), caso contrário a API omitirá essas novas informações.
