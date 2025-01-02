#!/usr/bin/env python3
import pandas as pd
import prometheus_client
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MFAFeedbackAnalyzer:
    def __init__(self):
        self.metrics = {
            'success_rate': prometheus_client.Counter(
                'mfa_feedback_analysis_success_rate',
                'Success rate of MFA operations'
            ),
            'user_satisfaction': prometheus_client.Gauge(
                'mfa_feedback_user_satisfaction',
                'User satisfaction score for MFA'
            ),
            'issues_reported': prometheus_client.Counter(
                'mfa_feedback_issues_reported',
                'Number of issues reported by category',
                ['category']
            )
        }
        
    def collect_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Coleta métricas do Prometheus para o período especificado"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        metrics_data = {
            'success_rate': [],
            'verification_time': [],
            'failed_attempts': [],
            'backup_codes_used': []
        }
        
        # Aqui você implementaria a lógica real de coleta do Prometheus
        logger.info(f"Coletando métricas de {start_time} até {end_time}")
        return metrics_data
    
    def analyze_feedback(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analisa o feedback dos usuários"""
        analysis = {
            'total_feedback': len(feedback_data),
            'satisfaction_score': 0,
            'common_issues': {},
            'improvement_suggestions': [],
            'positive_aspects': []
        }
        
        for feedback in feedback_data:
            # Análise de satisfação
            analysis['satisfaction_score'] += feedback.get('satisfaction', 0)
            
            # Categorização de problemas
            if 'issues' in feedback:
                for issue in feedback['issues']:
                    analysis['common_issues'][issue] = analysis['common_issues'].get(issue, 0) + 1
            
            # Coleta de sugestões
            if 'suggestions' in feedback:
                analysis['improvement_suggestions'].extend(feedback['suggestions'])
            
            # Aspectos positivos
            if 'positive_aspects' in feedback:
                analysis['positive_aspects'].extend(feedback['positive_aspects'])
        
        # Calcula média de satisfação
        if analysis['total_feedback'] > 0:
            analysis['satisfaction_score'] /= analysis['total_feedback']
            
        return analysis
    
    def generate_report(self, metrics_data: Dict[str, Any], feedback_analysis: Dict[str, Any]) -> str:
        """Gera um relatório combinando métricas e análise de feedback"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics_summary': {
                'success_rate': f"{metrics_data.get('success_rate', 0):.2f}%",
                'avg_verification_time': f"{metrics_data.get('avg_verification_time', 0):.2f}ms",
                'failed_attempts_rate': f"{metrics_data.get('failed_attempts_rate', 0):.2f}%"
            },
            'feedback_summary': {
                'total_responses': feedback_analysis['total_feedback'],
                'satisfaction_score': f"{feedback_analysis['satisfaction_score']:.2f}/5.0",
                'top_issues': dict(sorted(
                    feedback_analysis['common_issues'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]),
                'key_suggestions': feedback_analysis['improvement_suggestions'][:5]
            },
            'recommendations': self._generate_recommendations(metrics_data, feedback_analysis)
        }
        
        return json.dumps(report, indent=2)
    
    def _generate_recommendations(self, metrics_data: Dict[str, Any], feedback_analysis: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas nas métricas e feedback"""
        recommendations = []
        
        # Análise de performance
        if metrics_data.get('avg_verification_time', 0) > 500:
            recommendations.append("Otimizar tempo de verificação do MFA")
            
        # Análise de usabilidade
        if feedback_analysis['satisfaction_score'] < 4.0:
            recommendations.append("Melhorar a experiência do usuário no processo de MFA")
            
        # Análise de falhas
        if metrics_data.get('failed_attempts_rate', 0) > 5:
            recommendations.append("Investigar e reduzir taxa de falhas no MFA")
            
        return recommendations
    
    def visualize_data(self, metrics_data: Dict[str, Any], feedback_analysis: Dict[str, Any]) -> None:
        """Cria visualizações dos dados coletados"""
        # Configura o estilo
        plt.style.use('seaborn')
        
        # Cria uma figura com múltiplos subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Success Rate Over Time
        if 'success_rate' in metrics_data:
            sns.lineplot(data=metrics_data['success_rate'], ax=ax1)
            ax1.set_title('Taxa de Sucesso do MFA')
            ax1.set_ylabel('Taxa de Sucesso (%)')
        
        # 2. Verification Time Distribution
        if 'verification_time' in metrics_data:
            sns.histplot(data=metrics_data['verification_time'], ax=ax2)
            ax2.set_title('Distribuição do Tempo de Verificação')
            ax2.set_xlabel('Tempo (ms)')
        
        # 3. Common Issues
        issues_df = pd.DataFrame.from_dict(
            feedback_analysis['common_issues'],
            orient='index',
            columns=['count']
        )
        sns.barplot(data=issues_df, x=issues_df.index, y='count', ax=ax3)
        ax3.set_title('Problemas Mais Comuns')
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. User Satisfaction Distribution
        if 'satisfaction_scores' in feedback_analysis:
            sns.boxplot(data=feedback_analysis['satisfaction_scores'], ax=ax4)
            ax4.set_title('Distribuição da Satisfação dos Usuários')
        
        plt.tight_layout()
        plt.savefig('mfa_analysis.png')
        logger.info("Visualizações salvas em 'mfa_analysis.png'")

def main():
    analyzer = MFAFeedbackAnalyzer()
    
    # Coleta métricas
    logger.info("Coletando métricas...")
    metrics_data = analyzer.collect_metrics(days=7)
    
    # Coleta feedback (simulado para exemplo)
    logger.info("Coletando feedback...")
    feedback_data = [
        {
            "satisfaction": 4,
            "issues": ["setup_time"],
            "suggestions": ["Simplificar processo de setup"],
            "positive_aspects": ["Segurança aumentada"]
        }
        # Adicionar mais feedback real aqui
    ]
    
    # Analisa feedback
    logger.info("Analisando feedback...")
    feedback_analysis = analyzer.analyze_feedback(feedback_data)
    
    # Gera relatório
    logger.info("Gerando relatório...")
    report = analyzer.generate_report(metrics_data, feedback_analysis)
    
    # Salva relatório
    with open('mfa_feedback_report.json', 'w') as f:
        f.write(report)
    logger.info("Relatório salvo em 'mfa_feedback_report.json'")
    
    # Gera visualizações
    logger.info("Gerando visualizações...")
    analyzer.visualize_data(metrics_data, feedback_analysis)
    
    logger.info("Análise completa!")

if __name__ == "__main__":
    main() 