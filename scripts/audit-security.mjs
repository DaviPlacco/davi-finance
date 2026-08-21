import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2).reduce((acc, arg) => {
    const [k, v] = arg.replace(/^--/, '').split('=');
    acc[k] = v || true;
    return acc;
}, {});

const TARGET_URL = args.target || 'http://localhost:3000';
const SOURCE_DIR = args.path || 'src';

const results = { passed: [], warnings: [], errors: [] };

function log(level, message, detail = '') {
    results[level].push({ message, detail });
}

// ----------------------------------------------------
// 1. Static Code Analysis (RegEx / Pattern Matching)
// ----------------------------------------------------
function scanCodebase(dir) {
    if (!fs.existsSync(dir)) return;

    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            if (!['node_modules', '.next', '.git', 'dist', 'build'].includes(entry.name)) {
                scanCodebase(fullPath);
            }
            continue;
        }

        if (!/\.(ts|tsx|js|jsx|mjs|cjs)$/.test(entry.name)) continue;

        const content = fs.readFileSync(fullPath, 'utf8');
        const relativePath = path.relative(process.cwd(), fullPath);

        // Teste 1: Armazenamento de Tokens no LocalStorage / SessionStorage
        if (/localStorage\.(setItem|getItem)\s*\(\s*['"`](token|auth|jwt|access_token|refreshToken)['"`]/i.test(content)) {
            log('errors', `Uso inseguro de LocalStorage para tokens de autenticação`, `${relativePath} (Vulnerabilidade XSS -> Token Theft)`);
        }

        // Teste 2: Vazamento de Secrets em variáveis expostas
        if (/(NEXT_PUBLIC|VITE|REACT_APP)_(PRIVATE|SECRET|API_SECRET|DATABASE|KEY_SECRET)/i.test(content)) {
            log('errors', `Possível vazamento de segredo em variável de ambiente pública`, relativePath);
        }

        // Teste 3: Potencial IDOR / Falta de Scoping em Queries comuns
        const idorPatterns = [
            /\.(findUnique|findById|findOne)\s*\(\s*\{\s*where:\s*\{\s*id\s*\}|params\.id\s*\}\s*\)/g,
            /SELECT\s+\*\s+FROM\s+\w+\s+WHERE\s+id\s*=\s*\$?[1-9]/i
        ];
        for (const pattern of idorPatterns) {
            if (pattern.test(content) && !content.includes('userId') && !content.includes('tenantId') && !content.includes('accountId')) {
                log('warnings', `Alerta de IDOR: Query por ID sem validação aparente de userId/tenantId`, relativePath);
            }
        }
    }
}

// ----------------------------------------------------
// 2. Dynamic HTTP Headers & Cookie Analysis
// ----------------------------------------------------
async function scanLocalhost(url) {
    try {
        const response = await fetch(url, { method: 'HEAD' });
        const headers = response.headers;

        // Headers Obrigatórios
        const checks = [
            { name: 'x-frame-options', valid: (v) => ['DENY', 'SAMEORIGIN'].includes(v?.toUpperCase()), label: 'X-Frame-Options (Clickjacking)' },
            { name: 'x-content-type-options', valid: (v) => v?.toLowerCase() === 'nosniff', label: 'X-Content-Type-Options' },
            { name: 'strict-transport-security', valid: (v) => v?.includes('max-age'), label: 'HSTS (Strict-Transport-Security)', warnOnly: true },
            { name: 'content-security-policy', valid: (v) => !!v, label: 'Content-Security-Policy (CSP)' },
            { name: 'referrer-policy', valid: (v) => !!v, label: 'Referrer-Policy' }
        ];

        for (const check of checks) {
            const val = headers.get(check.name);
            if (check.valid(val)) {
                log('passed', `Header OK: ${check.label}`);
            } else {
                const targetList = check.warnOnly ? 'warnings' : 'errors';
                log(targetList, `Header ausente ou incorreto: ${check.label}`, `Valor atual: ${val || 'Não configurado'}`);
            }
        }

        // Validação de Cookies (se existirem)
        const setCookie = headers.get('set-cookie');
        if (setCookie) {
            if (!/httponly/i.test(setCookie)) log('errors', `Cookie sem flag HttpOnly configurada`);
            if (!/samesite=(strict|lax)/i.test(setCookie)) log('warnings', `Cookie sem SameSite=Strict ou Lax`);
        }

    } catch (err) {
        log('warnings', `Não foi possível conectar a ${url}. Certifique-se de que o servidor local está rodando.`);
    }
}

// ----------------------------------------------------
// Runner & Report Output
// ----------------------------------------------------
async function main() {
    console.log(`\n🛡️  Iniciando Auditoria de Segurança Local...`);
    console.log(`📂 Código-Fonte: ./${SOURCE_DIR}`);
    console.log(`🌐 Alvo HTTP:   ${TARGET_URL}\n`);

    scanCodebase(SOURCE_DIR);
    await scanLocalhost(TARGET_URL);

    console.log(`\n================ RELATÓRIO DE AUDITORIA ================`);

    if (results.passed.length > 0) {
        console.log(`\n\x1b[32m✔ PASSOU (${results.passed.length})\x1b[0m`);
        results.passed.forEach(p => console.log(`  • ${p.message}`));
    }

    if (results.warnings.length > 0) {
        console.log(`\n\x1b[33m▲ AVISOS (${results.warnings.length})\x1b[0m`);
        results.warnings.forEach(w => console.log(`  • ${w.message} ${w.detail ? `-> \x1b[90m${w.detail}\x1b[0m` : ''}`));
    }

    if (results.errors.length > 0) {
        console.log(`\n\x1b[31m✖ FALHAS CRÍTICAS (${results.errors.length})\x1b[0m`);
        results.errors.forEach(e => console.log(`  • ${e.message} ${e.detail ? `-> \x1b[90m${e.detail}\x1b[0m` : ''}`));
    }

    console.log(`\n========================================================\n`);

    if (results.errors.length > 0) {
        process.exit(1);
    }
}

main();