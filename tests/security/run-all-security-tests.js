const fs = require('fs').promises;
const { runSecurityChecks } = require('./security-checks.js');
const { runPenetrationTests } = require('./run-pentest.js');
const { runSecurityAudit } = require('./security-audit.js');
const { runComplianceCheck } = require('./compliance-check.js');

async function runAllSecurityTests() {
  console.log('Iniciando bateria completa de testes de segurança...\n');

  const results = {
    timestamp: new Date().toISOString(),
    security_checks: null,
    penetration_tests: null,
    security_audit: null,
    compliance_check: null,
    summary: {
      total_vulnerabilities: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      compliance_passed: 0,
      compliance_failed: 0,
      errors: []
    }
  };

  // 1. Verificações básicas de segurança
  try {
    console.log('=== Executando verificações básicas de segurança ===');
    results.security_checks = await runSecurityChecks();
    console.log('Verificações básicas concluídas\n');
  } catch (error) {
    console.error('Erro nas verificações básicas:', error.message);
    results.summary.errors.push({
      phase: 'security_checks',
      error: error.message
    });
  }

  // 2. Testes de penetração
  try {
    console.log('=== Executando testes de penetração ===');
    results.penetration_tests = await runPenetrationTests();
    console.log('Testes de penetração concluídos\n');
  } catch (error) {
    console.error('Erro nos testes de penetração:', error.message);
    results.summary.errors.push({
      phase: 'penetration_tests',
      error: error.message
    });
  }

  // 3. Auditoria de segurança
  try {
    console.log('=== Executando auditoria de segurança ===');
    results.security_audit = await runSecurityAudit();
    console.log('Auditoria de segurança concluída\n');
  } catch (error) {
    console.error('Erro na auditoria de segurança:', error.message);
    results.summary.errors.push({
      phase: 'security_audit',
      error: error.message
    });
  }

  // 4. Verificação de compliance
  try {
    console.log('=== Executando verificação de compliance ===');
    results.compliance_check = await runComplianceCheck();
    console.log('Verificação de compliance concluída\n');
  } catch (error) {
    console.error('Erro na verificação de compliance:', error.message);
    results.summary.errors.push({
      phase: 'compliance_check',
      error: error.message
    });
  }

  // Calcular sumário
  try {
    if (results.security_checks?.vulnerabilities) {
      results.security_checks.vulnerabilities.forEach(vuln => {
        results.summary.total_vulnerabilities++;
        if (vuln.severity === 'critical') results.summary.critical++;
        else if (vuln.severity === 'high') results.summary.high++;
        else if (vuln.severity === 'medium') results.summary.medium++;
        else results.summary.low++;
      });
    }

    if (results.penetration_tests?.vulnerabilities) {
      results.penetration_tests.vulnerabilities.forEach(vuln => {
        results.summary.total_vulnerabilities++;
        if (vuln.severity === 'critical') results.summary.critical++;
        else if (vuln.severity === 'high') results.summary.high++;
        else if (vuln.severity === 'medium') results.summary.medium++;
        else results.summary.low++;
      });
    }

    if (results.security_audit?.findings) {
      results.security_audit.findings.forEach(finding => {
        results.summary.total_vulnerabilities++;
        if (finding.severity === 'critical') results.summary.critical++;
        else if (finding.severity === 'high') results.summary.high++;
        else if (finding.severity === 'medium') results.summary.medium++;
        else results.summary.low++;
      });
    }

    if (results.compliance_check?.compliance_checks) {
      results.compliance_check.compliance_checks.forEach(check => {
        if (check.status === 'passed') results.summary.compliance_passed++;
        else results.summary.compliance_failed++;
      });
    }

    // Gerar relatório final
    const reportPath = './security-full-report.json';
    await fs.writeFile(reportPath, JSON.stringify(results, null, 2));

    // Exibir sumário
    console.log('\n=== Sumário Final dos Testes de Segurança ===');
    if (results.summary.errors.length > 0) {
      console.log('\n⚠️ Alguns testes falharam ou não puderam ser executados:');
      results.summary.errors.forEach(error => {
        console.log(`- ${error.phase}: ${error.error}`);
      });
      console.log('');
    }

    console.log(`Total de vulnerabilidades: ${results.summary.total_vulnerabilities}`);
    console.log(`  - Críticas: ${results.summary.critical}`);
    console.log(`  - Altas: ${results.summary.high}`);
    console.log(`  - Médias: ${results.summary.medium}`);
    console.log(`  - Baixas: ${results.summary.low}`);
    console.log('\nCompliance:');
    console.log(`  - Verificações passadas: ${results.summary.compliance_passed}`);
    console.log(`  - Verificações falhas: ${results.summary.compliance_failed}`);
    console.log(`\nRelatório detalhado salvo em: ${reportPath}`);

    // Gerar recomendações baseadas nos resultados
    if (results.summary.total_vulnerabilities > 0 || results.summary.compliance_failed > 0) {
      await generateRecommendations(results);
    }

    return results;

  } catch (error) {
    console.error('Erro ao gerar relatório:', error);
    throw error;
  }
}

async function generateRecommendations(results) {
  const recommendations = {
    critical: [],
    high: [],
    medium: [],
    low: []
  };

  // Analisar vulnerabilidades críticas e altas primeiro
  if (results.summary.critical > 0 || results.summary.high > 0) {
    recommendations.critical.push(
      'AÇÃO IMEDIATA NECESSÁRIA: Vulnerabilidades críticas ou de alta severidade encontradas',
      'Priorize a correção das seguintes issues:'
    );

    // Adicionar vulnerabilidades críticas dos testes de penetração
    results.penetration_tests?.vulnerabilities
      ?.filter(v => v.severity === 'critical' || v.severity === 'high')
      ?.forEach(v => {
        recommendations.critical.push(`- ${v.description} (${v.type})`);
        if (v.recommendation) {
          recommendations.critical.push(`  Recomendação: ${v.recommendation}`);
        }
      });

    // Adicionar findings críticos da auditoria
    results.security_audit?.findings
      ?.filter(f => f.severity === 'critical' || f.severity === 'high')
      ?.forEach(f => {
        recommendations.critical.push(`- ${f.description} (${f.type})`);
        if (f.recommendation) {
          recommendations.critical.push(`  Recomendação: ${f.recommendation}`);
        }
      });
  }

  // Analisar issues de compliance
  if (results.summary.compliance_failed > 0) {
    recommendations.high.push(
      'COMPLIANCE: Falhas de conformidade encontradas',
      'Corrija as seguintes não-conformidades:'
    );

    results.compliance_check?.compliance_checks
      ?.filter(c => c.status === 'failed')
      ?.forEach(c => {
        recommendations.high.push(`- ${c.check} (${c.standard})`);
        if (c.message) {
          recommendations.high.push(`  Problema: ${c.message}`);
        }
      });
  }

  // Analisar vulnerabilidades médias
  if (results.summary.medium > 0) {
    recommendations.medium.push(
      'ATENÇÃO: Vulnerabilidades de média severidade encontradas',
      'Planeje a correção das seguintes issues:'
    );

    // Adicionar todas as vulnerabilidades médias
    [...(results.penetration_tests?.vulnerabilities || []),
     ...(results.security_audit?.findings || [])]
      .filter(v => v.severity === 'medium')
      .forEach(v => {
        recommendations.medium.push(`- ${v.description} (${v.type})`);
        if (v.recommendation) {
          recommendations.medium.push(`  Recomendação: ${v.recommendation}`);
        }
      });
  }

  // Analisar vulnerabilidades baixas
  if (results.summary.low > 0) {
    recommendations.low.push(
      'MELHORIAS: Vulnerabilidades de baixa severidade encontradas',
      'Considere as seguintes melhorias:'
    );

    // Adicionar todas as vulnerabilidades baixas
    [...(results.penetration_tests?.vulnerabilities || []),
     ...(results.security_audit?.findings || [])]
      .filter(v => v.severity === 'low')
      .forEach(v => {
        recommendations.low.push(`- ${v.description} (${v.type})`);
        if (v.recommendation) {
          recommendations.low.push(`  Recomendação: ${v.recommendation}`);
        }
      });
  }

  // Salvar recomendações
  const recommendationsPath = './security-recommendations.json';
  await fs.writeFile(recommendationsPath, JSON.stringify(recommendations, null, 2));
  
  console.log(`\nRecomendações detalhadas salvas em: ${recommendationsPath}`);
  
  // Exibir recomendações críticas e altas imediatamente
  if (recommendations.critical.length > 0) {
    console.log('\n⚠️ RECOMENDAÇÕES CRÍTICAS:');
    recommendations.critical.forEach(r => console.log(r));
  }
  
  if (recommendations.high.length > 0) {
    console.log('\n⚠️ RECOMENDAÇÕES DE ALTA PRIORIDADE:');
    recommendations.high.forEach(r => console.log(r));
  }
}

// Executar testes se chamado diretamente
if (require.main === module) {
  runAllSecurityTests().catch(console.error);
}

module.exports = { runAllSecurityTests }; 