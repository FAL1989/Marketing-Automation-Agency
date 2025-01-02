# Arquitetura do Projeto (Segunda etaoa)

## Visão Geral

graph TB
    %% Frontend Layer
    subgraph Frontend["Frontend Layer - Next.js + TypeScript"]
        UI["Web Interface"]
        Auth_UI["Authentication UI"]
        
        subgraph Content_Management["Content Management"]
            TM["Template Manager"]
            CG["Content Generator"]
            PE["Post Editor"]
        end
        
        subgraph Innovation_UI["Innovation Interface"]
            HI["Human Interface"]
            AD["AI Dashboard"]
            IM["Innovation Manager"]
        end

        UI --> Auth_UI
        UI --> Content_Management
        UI --> Innovation_UI
    end

    %% Backend Layer
    subgraph Backend["Backend Services"]
        API["FastAPI + TypeScript"]
        
        subgraph Security["Security Layer"]
            JWT["JWT Auth"]
            RL["Rate Limiting"]
            Audit["Audit System"]
        end
        
        subgraph AI_Core["AI Core Services"]
            IL["Innovation Lab"]
            SA["Super Agents"]
            ML["Machine Learning"]
            
            subgraph Agent_System["Agent System"]
                TE["Technical Expert"]
                BA["Business Analyst"]
                IC["Innovation Consultant"]
            end
            
            subgraph Knowledge["Knowledge System"]
                Vector[(Vector Store)]
                Doc["Document Store"]
                Memory["Memory System"]
            end
        end
        
        subgraph Content_Service["Content Services"]
            Templates["Template Service"]
            Generator["Content Generator"]
            Publisher["Content Publisher"]
        end
    end

    %% Data Layer
    subgraph Data["Data Layer"]
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Vector_DB[(Vector DB)]
        
        subgraph Storage["Object Storage"]
            Assets["Asset Storage"]
            Backups["Backup System"]
        end
    end

    %% Infrastructure
    subgraph Infrastructure["Infrastructure"]
        K8s["Kubernetes"]
        
        subgraph Observability["Observability"]
            Metrics["Prometheus"]
            Logs["Loki"]
            Traces["Jaeger"]
            Grafana["Grafana Dashboards"]
        end
        
        subgraph DevOps["DevOps Tools"]
            CI["CI/CD Pipeline"]
            IaC["Infrastructure as Code"]
            Monitoring["Monitoring Stack"]
        end
    end

    %% Connections
    Frontend --> API
    API --> Security
    Security --> AI_Core
    Security --> Content_Service
    
    AI_Core --> Data
    Content_Service --> Data
    
    Infrastructure --> Backend
    
    %% Data Flows
    Vector --> Knowledge
    DB --> Content_Service
    Cache --> AI_Core