# 📅 API de Agendamentos

> Backend para sistema de agendamentos, pronto para deploy no Railway e consumo via Lovable/Frontend.

## 🏗️ Stack
- Python 3.11 + FastAPI + SQLAlchemy
- PostgreSQL 15

## 📁 Estrutura do Repositório

```
.
├── app/               # Lógica do FastAPI
│   ├── routers/       # Endpoints da API (services, availability, appointments, users, auth)
│   ├── models.py      # ORM
│   ├── schemas.py     # Pydantic (validação)
│   └── main.py        # Entrypoint
├── database/          # Scripts SQL (migrations)
├── requirements.txt   # Dependências
├── Procfile           # Config de boot para Railway
└── railway.json       # Configurações do Railway (Healthcheck)
```

## 🚀 Deploy Rápido no Railway

1. Conecte este repositório no Railway (como um serviço normal, a raiz do projeto já é o backend)
2. Adicione um banco PostgreSQL pelo Railway
3. Configure as variáveis de ambiente (`DATABASE_URL`, `SECRET_KEY`, `ADMIN_PASSWORD`, etc)
4. Execute o script `database/migrations/001_initial_schema.sql` no banco
5. Acesse `https://seu-app.up.railway.app/docs` para gerenciar os dados via Swagger
