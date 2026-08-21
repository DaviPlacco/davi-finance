---
name: security_audit
description: Executa auditoria automatizada de segurança OWASP (estática no código e dinâmica em localhost) para aplicações financeiras.
triggers:
  - "auditar segurança"
  - "validar regras de segurança"
  - "rodar security check"
---

# Security Audit Skill

## Quando Executar
Execute esta skill para identificar vulnerabilidades antes de merges, deploys ou após alterações em rotas de autenticação, middlewares, queries de banco e headers HTTP.

## Como Executar
Execute o comando CLI nativo no terminal da máquina:

\`\`\`bash
node scripts/audit-security.mjs --target=http://localhost:3000 --path=src
\`\`\`

## O que a ferramenta avalia:
1. **Dynamic Check (Localhost):**
   - Cabeçalhos de segurança (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
   - Flags em cookies de resposta (`HttpOnly`, `Secure`, `SameSite`).
2. **Static AST/Pattern Scan (Código-Fonte):**
   - Armazenamento indevido de auth tokens em `localStorage` ou `sessionStorage`.
   - Vazamento de segredos em variáveis públicas (`NEXT_PUBLIC_*`, `VITE_*` contendo chaves privadas).
   - Consultas de banco de dados com risco de IDOR (queries sem filtro de tenant/userId).
   - Geração exposta de source maps em builds de produção.