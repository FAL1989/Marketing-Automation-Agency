# Arquitetura do Sistema

## Visão Geral

```mermaid
graph TB
    subgraph Frontend["Frontend (React + TypeScript)"]
        subgraph Auth_Layer["Authentication Layer"]
            Login["Login Interface"]
            MFA_UI["MFA Interface"]
            QR["QR Code Generator"]
            Backup["Backup Codes UI"]
            Recovery_UI["Recovery Email UI"]
        end
        
        subgraph Core_UI["Core Components"]
            Dashboard["Main Dashboard"]
            Templates["Template Manager"]
            Content["Content Generator"]
            Analytics["Analytics View"]
            Settings["User Settings"]
        end
        
        subgraph Optimizations["Performance Features"]
            Lazy["Lazy Loading"]
            Split["Code Splitting"]
            ErrorBound["Error Boundaries"]
            PWA["PWA Features"]
            Cache_UI["Client Cache"]
        end
    end
    
    subgraph Backend["Backend (Node.js + TypeScript)"]
        API["REST API"]
        
        subgraph Security["Security Layer"]
            JWT["JWT Service"]
            MFA["MFA Service"]
            Rate["Rate Limiting"]
            Circuit["Circuit Breaker"]
            
            subgraph MFA_Components["MFA Components"]
                Secret["Secret Generator"]
                TOTP["TOTP Validator"]
                Recovery["Recovery System"]
                Backup_Gen["Backup Codes Generator"]
                Lock["Account Locking"]
            end
        end
        
        subgraph Core_Services["Core Services"]
            Users["User Service"]
            Templates_Svc["Template Service"]
            Generator["Content Generator"]
            Events["Event Tracker"]
            Email["Email Service"]
        end
        
        subgraph Cache["Cache Layer"]
            Redis["Redis Cluster"]
            Cache_Rules["Cache Rules"]
            TTL["TTL Manager"]
            Invalid["Cache Invalidator"]
            Health["Health Check"]
        end
    end
    
    subgraph Data["Data Layer"]
        DB[(PostgreSQL)]
        Audit["Audit Logs"]
        Events_DB["Events Store"]
        MFA_Store["MFA Data Store"]
    end
    
    subgraph Monitoring["Monitoring Stack"]
        subgraph Metrics["Metrics Collection"]
            Prom["Prometheus"]
            MFA_Metrics["MFA Metrics"]
            Cache_Metrics["Cache Metrics"]
            Perf_Metrics["Performance Metrics"]
            Security_Metrics["Security Metrics"]
        end
        
        subgraph Visualization["Dashboards"]
            Grafana["Grafana"]
            MFA_Dash["MFA Dashboard"]
            Perf_Dash["Performance Dashboard"]
            Audit_Dash["Audit Dashboard"]
            Security_Dash["Security Dashboard"]
        end
        
        subgraph Alerts["Alert System"]
            Alert_Man["Alert Manager"]
            MFA_Alerts["MFA Alerts"]
            Security_Alerts["Security Alerts"]
            Perf_Alerts["Performance Alerts"]
            Cache_Alerts["Cache Alerts"]
        end
    end
    
    %% Connections
    Login --> MFA_UI
    MFA_UI --> QR
    MFA_UI --> Backup
    MFA_UI --> Recovery_UI
    
    API --> Security
    Security --> Core_Services
    Core_Services --> Cache
    Cache --> Data
    
    Security --> Audit
    Core_Services --> Events_DB
    MFA --> MFA_Store
    
    Backend --> Metrics
    Metrics --> Visualization
    Visualization --> Alerts
    
    Email --> Recovery
    Lock --> MFA_Alerts
```

## Componentes Principais

### Frontend

#### Authentication Layer
- **Login Interface**: Gerencia autenticação inicial
- **MFA Interface**: Interface para 2FA com QR code e backup codes
- **Recovery Email UI**: Gerenciamento de email de recuperação
- **Backup Codes UI**: Visualização e gestão de códigos de backup

#### Core Components
- **User Settings**: Configurações do usuário, incluindo MFA
- **Template Manager**: Gerenciamento de templates
- **Content Generator**: Geração de conteúdo com IA
- **Analytics View**: Visualização de métricas e analytics

### Backend

#### Security Layer
- **MFA Service**: Serviço completo de autenticação em duas etapas
  - Geração de segredos TOTP
  - Validação de códigos
  - Sistema de backup codes
  - Sistema de recuperação
  - Rate limiting específico
  - Bloqueio de conta após tentativas falhas

#### Core Services
- **Email Service**: Envio de notificações e códigos de recuperação
- **User Service**: Gerenciamento de usuários e perfis
- **Event Tracker**: Rastreamento de eventos de segurança

#### Cache Layer
- **Redis Cluster**: Cache distribuído
- **TTL Manager**: Gestão de tempo de vida do cache
- **Health Check**: Monitoramento de saúde do cache

### Monitoring Stack

#### Metrics Collection
- **MFA Metrics**: Métricas específicas de MFA
  - Taxa de sucesso
  - Tempo de verificação
  - Tentativas falhas
  - Uso de backup codes

#### Dashboards
- **MFA Dashboard**: Visualização de métricas MFA
- **Security Dashboard**: Monitoramento de segurança
- **Audit Dashboard**: Logs de auditoria

#### Alerts
- **MFA Alerts**: Alertas específicos de MFA
- **Security Alerts**: Alertas de segurança
- **Cache Alerts**: Alertas de performance do cache

## Métricas Atuais

- Cobertura de testes: > 90%
- Tempo médio de resposta: < 200ms
- Taxa de erro: < 0.1%
- Disponibilidade: > 99.9%
- Taxa de sucesso do MFA: > 98%
- Tempo médio de verificação MFA: < 500ms 