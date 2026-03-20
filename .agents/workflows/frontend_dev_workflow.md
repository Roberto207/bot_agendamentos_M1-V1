---
description: Como desenvolver componentes para o portal SaaS (Frontend)
---

# Workflow: Desenvolvimento de Frontend SaaS

O frontend do sistema SaaS de Agendamentos será o painel pelo qual empreendedores vão gerenciar suas companhias. Todas as adições devem seguir um alto padrão de UI/UX e boas práticas de integração.

## 1. Conexão e APIs (Backend FastAPI)
Você deve consumir as rotas REST do backend. Lembre-se que:
- O dashboard principal usa `dashboard_routes.py`.
- O login usa `auth_site_router.py`.
- Todas as rotas (exceto autenticação e algumas públicas) exigem o Token JWT no header.

## 2. Padrões de Design de Alta Qualidade (Premium)
- **Cores e Temas:** Não use cores brutas como `red` ou `blue`. O sistema pede **Dark Mode** limpo e moderno, usando gradientes ou "glassmorphism" e coloração via HSL para dar um ar profissional.
- **Micro-animações:** Botões e cards devem ter efeitos de `hover` e transição orgânicos, gerando sensação de vida à tela.
- **Tipografia:** Use fontes da família Google Fonts como `Inter` ou `Outfit`, descartando o fallback horroroso do navegador.

## 3. SEO e Acessibilidade (Opcional Painel, Obrigatório se Páginas de Venda)
Como regra geral de SEO e qualidade sistêmica:
- Mantenha hierarquia (`<h1>`, `<h2>`).
- Nunca deixe imagens ou cards vitais sem descrição ou ID, pois facilita também a automação de testes UI no futuro.
