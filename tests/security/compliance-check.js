const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

async function runComplianceCheck() {
  console.log('Iniciando verificação de compliance...\n');

  const results = {
    timestamp: new Date().toISOString(),
    compliance_checks: [],
    summary: {
      passed: 0,
      failed: 0,
      warnings: 0
    }
  };

  try {
    // 1. GDPR Compliance
    console.log('Verificando conformidade com GDPR...');
    await checkGDPRCompliance(results);

    // 2. LGPD Compliance
    console.log('\nVerificando conformidade com LGPD...');
    await checkLGPDCompliance(results);

    // 3. Security Standards
    console.log('\nVerificando padrões de segurança...');
    await checkSecurityStandards(results);

    // 4. Data Protection
    console.log('\nVerificando proteção de dados...');
    await checkDataProtection(results);

    // 5. Access Control
    console.log('\nVerificando controle de acesso...');
    await checkAccessControl(results);

    // Gerar relatório
    const reportPath = './compliance-report.json';
    await fs.writeFile(reportPath, JSON.stringify(results, null, 2));
    
    // Exibir sumário
    console.log('\n=== Sumário da Verificação de Compliance ===');
    console.log(`Verificações passadas: ${results.summary.passed}`);
    console.log(`Verificações falhas: ${results.summary.failed}`);
    console.log(`Avisos: ${results.summary.warnings}`);
    console.log(`\nRelatório detalhado salvo em: ${reportPath}`);

    return results;

  } catch (error) {
    console.error('Erro durante a verificação de compliance:', error);
    throw error;
  }
}

async function checkGDPRCompliance(results) {
  const gdprChecks = [
    {
      name: 'Política de Privacidade',
      check: async () => {
        try {
          await fs.access('frontend/src/pages/privacy-policy.tsx');
          return { passed: true };
        } catch {
          return {
            passed: false,
            message: 'Política de Privacidade não encontrada'
          };
        }
      }
    },
    {
      name: 'Consentimento do Usuário',
      check: async () => {
        try {
          const files = await fs.readdir('frontend/src/components');
          const hasConsent = files.some(f => f.toLowerCase().includes('consent'));
          return {
            passed: hasConsent,
            message: hasConsent ? null : 'Componente de consentimento não encontrado'
          };
        } catch {
          return {
            passed: false,
            message: 'Não foi possível verificar componentes de consentimento'
          };
        }
      }
    },
    {
      name: 'Direito ao Esquecimento',
      check: async () => {
        try {
          const apiFiles = await fs.readdir('backend/app/api');
          const hasDeleteEndpoint = apiFiles.some(f => 
            f.includes('user') && f.includes('delete')
          );
          return {
            passed: hasDeleteEndpoint,
            message: hasDeleteEndpoint ? null : 'Endpoint de deleção de usuário não encontrado'
          };
        } catch {
          return {
            passed: false,
            message: 'Não foi possível verificar endpoints de deleção'
          };
        }
      }
    }
  ];

  for (const check of gdprChecks) {
    const result = await check.check();
    results.compliance_checks.push({
      standard: 'GDPR',
      check: check.name,
      status: result.passed ? 'passed' : 'failed',
      message: result.message
    });

    if (result.passed) {
      results.summary.passed++;
    } else {
      results.summary.failed++;
    }
  }
}

async function checkLGPDCompliance(results) {
  const lgpdChecks = [
    {
      name: 'Termos de Uso',
      check: async () => {
        try {
          await fs.access('frontend/src/pages/terms.tsx');
          return { passed: true };
        } catch {
          return {
            passed: false,
            message: 'Termos de Uso não encontrados'
          };
        }
      }
    },
    {
      name: 'Registro de Consentimento',
      check: async () => {
        try {
          const hasConsentLog = await fs.access('backend/app/models/consent_log.py');
          return { passed: true };
        } catch {
          return {
            passed: false,
            message: 'Sistema de registro de consentimento não encontrado'
          };
        }
      }
    },
    {
      name: 'Relatório de Impacto',
      check: async () => {
        try {
          await fs.access('docs/privacy-impact-assessment.md');
          return { passed: true };
        } catch {
          return {
            passed: false,
            message: 'Relatório de Impacto à Proteção de Dados não encontrado'
          };
        }
      }
    }
  ];

  for (const check of lgpdChecks) {
    const result = await check.check();
    results.compliance_checks.push({
      standard: 'LGPD',
      check: check.name,
      status: result.passed ? 'passed' : 'failed',
      message: result.message
    });

    if (result.passed) {
      results.summary.passed++;
    } else {
      results.summary.failed++;
    }
  }
}

async function checkSecurityStandards(results) {
  const securityChecks = [
    {
      name: 'HTTPS',
      check: async () => {
        try {
          const nginxConfig = await fs.readFile('nginx/nginx.conf', 'utf8');
          const hasSSL = nginxConfig.includes('ssl_certificate');
          return {
            passed: hasSSL,
            message: hasSSL ? null : 'Configuração SSL não encontrada'
          };
        } catch {
          return {
            passed: false,
            message: 'Configuração NGINX não encontrada'
          };
        }
      }
    },
    {
      name: 'Password Hashing',
      check: async () => {
        try {
          const authFile = await fs.readFile('backend/app/core/security.py', 'utf8');
          const hasSecureHash = authFile.includes('bcrypt') || authFile.includes('argon2');
          return {
            passed: hasSecureHash,
            message: hasSecureHash ? null : 'Algoritmo seguro de hash não encontrado'
          };
        } catch {
          return {
            passed: false,
            message: 'Arquivo de segurança não encontrado'
          };
        }
      }
    },
    {
      name: 'Rate Limiting',
      check: async () => {
        try {
          const middlewareFiles = await fs.readdir('backend/app/middleware');
          const hasRateLimit = middlewareFiles.some(f => f.includes('rate_limit'));
          return {
            passed: hasRateLimit,
            message: hasRateLimit ? null : 'Rate limiting não implementado'
          };
        } catch {
          return {
            passed: false,
            message: 'Não foi possível verificar middlewares'
          };
        }
      }
    }
  ];

  for (const check of securityChecks) {
    const result = await check.check();
    results.compliance_checks.push({
      standard: 'Security',
      check: check.name,
      status: result.passed ? 'passed' : 'failed',
      message: result.message
    });

    if (result.passed) {
      results.summary.passed++;
    } else {
      results.summary.failed++;
    }
  }
}

async function checkDataProtection(results) {
  const dataChecks = [
    {
      name: 'Encryption at Rest',
      check: async () => {
        try {
          const dbConfig = await fs.readFile('backend/app/core/database.py', 'utf8');
          const hasEncryption = dbConfig.includes('ssl_mode') || dbConfig.includes('encrypt');
          return {
            passed: hasEncryption,
            message: hasEncryption ? null : 'Encriptação em repouso não configurada'
          };
        } catch {
          return {
            passed: false,
            message: 'Configuração de banco de dados não encontrada'
          };
        }
      }
    },
    {
      name: 'Data Backup',
      check: async () => {
        try {
          const dockerCompose = await fs.readFile('docker-compose.yml', 'utf8');
          const hasBackup = dockerCompose.includes('backup') || dockerCompose.includes('volume');
          return {
            passed: hasBackup,
            message: hasBackup ? null : 'Sistema de backup não configurado'
          };
        } catch {
          return {
            passed: false,
            message: 'docker-compose.yml não encontrado'
          };
        }
      }
    },
    {
      name: 'Data Retention',
      check: async () => {
        try {
          const models = await fs.readdir('backend/app/models');
          const hasRetention = models.some(f => f.includes('retention'));
          return {
            passed: hasRetention,
            message: hasRetention ? null : 'Política de retenção de dados não implementada'
          };
        } catch {
          return {
            passed: false,
            message: 'Não foi possível verificar modelos de dados'
          };
        }
      }
    }
  ];

  for (const check of dataChecks) {
    const result = await check.check();
    results.compliance_checks.push({
      standard: 'Data Protection',
      check: check.name,
      status: result.passed ? 'passed' : 'failed',
      message: result.message
    });

    if (result.passed) {
      results.summary.passed++;
    } else {
      results.summary.failed++;
    }
  }
}

async function checkAccessControl(results) {
  const accessChecks = [
    {
      name: 'Role-Based Access',
      check: async () => {
        try {
          const authFiles = await fs.readdir('backend/app/auth');
          const hasRBAC = authFiles.some(f => f.includes('role') || f.includes('permission'));
          return {
            passed: hasRBAC,
            message: hasRBAC ? null : 'RBAC não implementado'
          };
        } catch {
          return {
            passed: false,
            message: 'Não foi possível verificar sistema de autenticação'
          };
        }
      }
    },
    {
      name: 'Session Management',
      check: async () => {
        try {
          const middlewareFiles = await fs.readdir('backend/app/middleware');
          const hasSession = middlewareFiles.some(f => f.includes('session'));
          return {
            passed: hasSession,
            message: hasSession ? null : 'Gerenciamento de sessão não implementado'
          };
        } catch {
          return {
            passed: false,
            message: 'Não foi possível verificar middlewares'
          };
        }
      }
    },
    {
      name: 'API Authentication',
      check: async () => {
        try {
          const response = await axios.get('http://localhost:8000/api/protected');
          return {
            passed: false,
            message: 'Endpoint protegido acessível sem autenticação'
          };
        } catch (error) {
          if (error.response?.status === 401) {
            return { passed: true };
          }
          return {
            passed: false,
            message: 'Não foi possível verificar autenticação da API'
          };
        }
      }
    }
  ];

  for (const check of accessChecks) {
    const result = await check.check();
    results.compliance_checks.push({
      standard: 'Access Control',
      check: check.name,
      status: result.passed ? 'passed' : 'failed',
      message: result.message
    });

    if (result.passed) {
      results.summary.passed++;
    } else {
      results.summary.failed++;
    }
  }
}

// Executar verificação se chamado diretamente
if (require.main === module) {
  runComplianceCheck().catch(console.error);
}

module.exports = { runComplianceCheck }; 