const { execSync } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

async function runSecurityAudit() {
  console.log('Iniciando auditoria de segurança...\n');

  const results = {
    timestamp: new Date().toISOString(),
    findings: [],
    summary: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    }
  };

  try {
    // 1. Auditoria de dependências
    console.log('Verificando dependências...');
    
    // Frontend
    try {
      console.log('\nAuditando dependências do frontend...');
      const frontendAudit = JSON.parse(
        execSync('cd frontend && npm audit --json', { encoding: 'utf8' })
      );
      
      if (frontendAudit.vulnerabilities) {
        Object.entries(frontendAudit.vulnerabilities).forEach(([severity, count]) => {
          if (count > 0) {
            results.findings.push({
              type: 'dependency_vulnerability',
              component: 'frontend',
              severity,
              count,
              description: `${count} vulnerabilidades ${severity} encontradas nas dependências do frontend`,
              recommendation: 'Atualizar dependências afetadas'
            });
            results.summary[severity] += count;
          }
        });
      }
    } catch (error) {
      console.error('Erro ao auditar dependências do frontend:', error.message);
    }

    // Backend
    try {
      console.log('\nAuditando dependências do backend...');
      const backendAudit = JSON.parse(
        execSync('cd backend && pip-audit --format=json', { encoding: 'utf8' })
      );
      
      if (backendAudit.vulnerabilities) {
        backendAudit.vulnerabilities.forEach(vuln => {
          results.findings.push({
            type: 'dependency_vulnerability',
            component: 'backend',
            severity: vuln.severity.toLowerCase(),
            package: vuln.package_name,
            description: vuln.description,
            recommendation: `Atualizar ${vuln.package_name} para versão ${vuln.fixed_version || 'mais recente'}`
          });
          results.summary[vuln.severity.toLowerCase()]++;
        });
      }
    } catch (error) {
      console.error('Erro ao auditar dependências do backend:', error.message);
    }

    // 2. Verificar configurações sensíveis
    console.log('\nVerificando configurações sensíveis...');
    
    // Verificar arquivos de ambiente
    const envFiles = [
      'frontend/.env',
      'backend/.env',
      '.env',
      'docker-compose.yml',
      'docker-compose.override.yml'
    ];

    for (const file of envFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        
        // Procurar por chaves API e secrets
        const sensitivePatterns = [
          /api[_-]?key/i,
          /secret[_-]?key/i,
          /password/i,
          /token/i,
          /credential/i
        ];

        for (const pattern of sensitivePatterns) {
          if (pattern.test(content)) {
            results.findings.push({
              type: 'sensitive_data',
              severity: 'high',
              file,
              description: `Possível exposição de dados sensíveis em ${file}`,
              recommendation: 'Mover dados sensíveis para variáveis de ambiente ou secrets'
            });
            results.summary.high++;
          }
        }
      } catch (error) {
        // Arquivo não existe
      }
    }

    // 3. Verificar permissões de arquivos
    console.log('\nVerificando permissões de arquivos...');
    const criticalDirs = ['backend', 'frontend', 'config', 'scripts'];
    
    for (const dir of criticalDirs) {
      try {
        const stats = await fs.stat(dir);
        const mode = stats.mode.toString(8);
        
        if (mode.endsWith('777')) {
          results.findings.push({
            type: 'file_permission',
            severity: 'high',
            path: dir,
            description: `Permissões muito permissivas em ${dir}`,
            recommendation: 'Restringir permissões para o mínimo necessário'
          });
          results.summary.high++;
        }
      } catch (error) {
        // Diretório não existe
      }
    }

    // 4. Verificar configurações de segurança
    console.log('\nVerificando configurações de segurança...');
    
    // Frontend
    try {
      const packageJson = JSON.parse(
        await fs.readFile('frontend/package.json', 'utf8')
      );
      
      // Verificar CSP
      if (!packageJson.dependencies['helmet']) {
        results.findings.push({
          type: 'security_config',
          severity: 'medium',
          component: 'frontend',
          description: 'Helmet não está instalado para proteção de headers HTTP',
          recommendation: 'Instalar e configurar helmet para segurança adicional'
        });
        results.summary.medium++;
      }
    } catch (error) {
      console.error('Erro ao verificar configurações do frontend:', error.message);
    }

    // Backend
    try {
      const requirements = await fs.readFile('backend/requirements.txt', 'utf8');
      
      // Verificar dependências de segurança
      const securityPackages = ['python-jose[cryptography]', 'passlib[bcrypt]'];
      securityPackages.forEach(pkg => {
        if (!requirements.includes(pkg)) {
          results.findings.push({
            type: 'security_config',
            severity: 'medium',
            component: 'backend',
            description: `Pacote de segurança ${pkg} não encontrado`,
            recommendation: `Instalar ${pkg} para melhor segurança`
          });
          results.summary.medium++;
        }
      });
    } catch (error) {
      console.error('Erro ao verificar configurações do backend:', error.message);
    }

    // 5. Verificar logs e monitoramento
    console.log('\nVerificando configurações de logs e monitoramento...');
    
    // Verificar Prometheus
    try {
      const prometheusConfig = await fs.readFile('prometheus/prometheus.yml', 'utf8');
      
      if (!prometheusConfig.includes('alertmanager')) {
        results.findings.push({
          type: 'monitoring',
          severity: 'medium',
          description: 'Alertmanager não configurado no Prometheus',
          recommendation: 'Configurar Alertmanager para notificações de segurança'
        });
        results.summary.medium++;
      }
    } catch (error) {
      results.findings.push({
        type: 'monitoring',
        severity: 'high',
        description: 'Configuração do Prometheus não encontrada',
        recommendation: 'Implementar monitoramento com Prometheus'
      });
      results.summary.high++;
    }

    // 6. Verificar backup e recuperação
    console.log('\nVerificando configurações de backup...');
    
    try {
      const dockerCompose = await fs.readFile('docker-compose.yml', 'utf8');
      
      if (!dockerCompose.includes('volume') || !dockerCompose.includes('backup')) {
        results.findings.push({
          type: 'backup',
          severity: 'medium',
          description: 'Configuração de backup não encontrada',
          recommendation: 'Implementar sistema de backup automatizado'
        });
        results.summary.medium++;
      }
    } catch (error) {
      console.error('Erro ao verificar configurações de backup:', error.message);
    }

    // Gerar relatório
    const reportPath = './security-audit-report.json';
    await fs.writeFile(reportPath, JSON.stringify(results, null, 2));
    
    // Exibir sumário
    console.log('\n=== Sumário da Auditoria de Segurança ===');
    console.log(`Vulnerabilidades críticas: ${results.summary.critical}`);
    console.log(`Vulnerabilidades altas: ${results.summary.high}`);
    console.log(`Vulnerabilidades médias: ${results.summary.medium}`);
    console.log(`Vulnerabilidades baixas: ${results.summary.low}`);
    console.log(`\nRelatório detalhado salvo em: ${reportPath}`);

    return results;

  } catch (error) {
    console.error('Erro durante a auditoria de segurança:', error);
    throw error;
  }
}

// Executar auditoria se chamado diretamente
if (require.main === module) {
  runSecurityAudit().catch(console.error);
}

module.exports = { runSecurityAudit }; 