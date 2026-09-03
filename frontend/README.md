# Davi Finance

Aplicação de gestão financeira pessoal com dashboard, transações, categorias, orçamentos, investimentos, metas mensais, previsões, simulações, notificações e relatórios exportáveis.

## Arquitetura

- `frontend/`: Next.js 16, React 19, TypeScript, Tailwind CSS 4 e App Router.
- `backend/`: FastAPI, SQLAlchemy e autenticação JWT.
- O frontend comunica com o backend através das rotas BFF em `src/app/api/`. O JWT é guardado num cookie `HttpOnly` e anexado ao proxy no servidor.
- A base de dados padrão é SQLite. PostgreSQL e MySQL também são suportados através de `DATABASE_URL`.

## Requisitos

- Node.js 20 ou superior.
- Python 3.9 ou superior.

## Configuração do backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Antes de produção, defina obrigatoriamente uma `SECRET_KEY` forte, configure `ENVIRONMENT=production` e limite `ALLOWED_ORIGINS` aos domínios autorizados.

## Configuração do frontend

```bash
cd frontend
npm ci
API_URL=http://localhost:8000 npm run dev
```

A aplicação fica disponível em `http://localhost:3000`. `API_URL` é uma variável exclusiva do servidor; `NEXT_PUBLIC_API_URL` continua suportada apenas por compatibilidade.

## Validação

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Para auditar os headers HTTP, inicie o build com `npm start` e execute `npm run audit:security` noutro terminal.

## Regras do projeto

Consulte `../AGENTS.md` e `AGENTS.md` antes de alterar a aplicação. Em especial, não são permitidos `window.alert`, `window.confirm` ou `window.prompt`; confirmações e feedback devem usar os componentes customizados e o Sonner.
