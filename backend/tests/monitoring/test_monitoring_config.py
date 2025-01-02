import pytest
import yaml
import json
from pathlib import Path
from typing import Dict, List
import requests
from prometheus_client import REGISTRY
from ...app.monitoring.metrics_exporter import metrics_exporter
from ...app.core.config import settings

def load_yaml_file(file_path: str) -> Dict:
    """
    Carrega um arquivo YAML
    """
    with open(file_path) as f:
        return yaml.safe_load(f)

def load_json_file(file_path: str) -> Dict:
    """
    Carrega um arquivo JSON
    """
    with open(file_path) as f:
        return json.load(f)

def test_prometheus_config():
    """
    Testa a configuração do Prometheus
    """
    config_path = Path("prometheus/prometheus.yml")
    assert config_path.exists(), "Prometheus config file not found"
    
    config = load_yaml_file(config_path)
    
    # Verifica configurações globais
    assert "global" in config
    assert "scrape_interval" in config["global"]
    assert "evaluation_interval" in config["global"]
    
    # Verifica jobs de scraping
    assert "scrape_configs" in config
    jobs = {job["job_name"]: job for job in config["scrape_configs"]}
    
    # Verifica job da aplicação
    assert "ai_agency" in jobs
    app_job = jobs["ai_agency"]
    assert "static_configs" in app_job
    assert len(app_job["static_configs"]) > 0
    assert "targets" in app_job["static_configs"][0]
    
    # Verifica configurações de alerta
    assert "rule_files" in config
    for rule_file in config["rule_files"]:
        rule_path = Path(rule_file)
        assert rule_path.exists(), f"Rule file not found: {rule_file}"

def test_alertmanager_config():
    """
    Testa a configuração do Alertmanager
    """
    config_path = Path("alertmanager/config.yml")
    assert config_path.exists(), "Alertmanager config file not found"
    
    config = load_yaml_file(config_path)
    
    # Verifica configurações globais
    assert "global" in config
    
    # Verifica templates
    if "templates" in config:
        for template in config["templates"]:
            template_path = Path(template)
            assert template_path.exists(), f"Template file not found: {template}"
    
    # Verifica rotas
    assert "route" in config
    assert "receiver" in config["route"]
    
    # Verifica receivers
    assert "receivers" in config
    assert len(config["receivers"]) > 0
    
    # Verifica inibições
    if "inhibit_rules" in config:
        for rule in config["inhibit_rules"]:
            assert "source_match" in rule
            assert "target_match" in rule
            assert "equal" in rule

def test_grafana_dashboards():
    """
    Testa a configuração dos dashboards do Grafana
    """
    # Verifica configuração de provisionamento
    provisioning_path = Path("grafana/provisioning/dashboards/security.yaml")
    assert provisioning_path.exists(), "Dashboard provisioning config not found"
    
    provisioning = load_yaml_file(provisioning_path)
    assert "providers" in provisioning
    
    # Verifica dashboards
    dashboard_paths = [
        "grafana/dashboards/security.json",
        "grafana/dashboards/security_audit.json"
    ]
    
    for path in dashboard_paths:
        dashboard_path = Path(path)
        assert dashboard_path.exists(), f"Dashboard file not found: {path}"
        
        dashboard = load_json_file(dashboard_path)
        assert "panels" in dashboard
        assert len(dashboard["panels"]) > 0
        
        # Verifica painéis
        for panel in dashboard["panels"]:
            assert "title" in panel
            assert "type" in panel
            if "targets" in panel:
                for target in panel["targets"]:
                    assert "expr" in target

def test_grafana_datasources():
    """
    Testa a configuração das fontes de dados do Grafana
    """
    config_path = Path("grafana/provisioning/datasources/security.yaml")
    assert config_path.exists(), "Datasource config not found"
    
    config = load_yaml_file(config_path)
    assert "datasources" in config
    
    datasources = {ds["name"]: ds for ds in config["datasources"]}
    
    # Verifica Prometheus
    assert "Prometheus" in datasources
    prometheus = datasources["Prometheus"]
    assert prometheus["type"] == "prometheus"
    assert "url" in prometheus
    
    # Verifica Loki
    assert "Loki" in datasources
    loki = datasources["Loki"]
    assert loki["type"] == "loki"
    assert "url" in loki

def test_metrics_registration():
    """
    Testa o registro das métricas no Prometheus
    """
    metrics = {
        "rate_limit_violations_total",
        "suspicious_ip_activity_total",
        "xss_attempts_total",
        "csrf_attempts_total",
        "unauthorized_access_total",
        "request_latency_seconds"
    }
    
    registered_metrics = set()
    for metric in REGISTRY.collect():
        registered_metrics.add(metric.name)
    
    for metric in metrics:
        assert metric in registered_metrics, f"Metric not registered: {metric}"

@pytest.mark.asyncio
async def test_metrics_server():
    """
    Testa o servidor de métricas
    """
    app = FastAPI()
    port = settings.METRICS_PORT
    
    # Inicia o servidor
    await metrics_exporter.start(app, port)
    
    try:
        # Verifica se o servidor está respondendo
        response = requests.get(f"http://localhost:{port}/metrics")
        assert response.status_code == 200
        assert "rate_limit_violations_total" in response.text
        assert "suspicious_ip_activity_total" in response.text
        assert "xss_attempts_total" in response.text
        assert "csrf_attempts_total" in response.text
        assert "unauthorized_access_total" in response.text
        assert "request_latency_seconds" in response.text
    finally:
        # Desliga o servidor
        await metrics_exporter.shutdown()

def test_alert_rules():
    """
    Testa as regras de alerta do Prometheus
    """
    rules_path = Path("prometheus/rules/security_alerts.yml")
    assert rules_path.exists(), "Alert rules file not found"
    
    rules = load_yaml_file(rules_path)
    assert "groups" in rules
    
    for group in rules["groups"]:
        assert "name" in group
        assert "rules" in group
        
        for rule in group["rules"]:
            assert "alert" in rule
            assert "expr" in rule
            assert "for" in rule
            assert "labels" in rule
            assert "annotations" in rule
            
            # Verifica severidade
            assert "severity" in rule["labels"]
            assert rule["labels"]["severity"] in ["critical", "warning", "info"]
            
            # Verifica anotações
            assert "summary" in rule["annotations"]
            assert "description" in rule["annotations"] 