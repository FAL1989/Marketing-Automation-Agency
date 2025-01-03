.
├── 19:07:53.log
├── 19:09:44.log
├── =4.0.2
├── CRONOGRAMA.md
├── ESTRUTURA_PROJETO.md
├── LICENSE
├── README.md
├── assistant_snippet_A03l+ZRD61.txt
├── assistant_snippet_Hs2Wd4Aqxm.txt
├── assistant_snippet_Ik7t9FyXkK.txt
├── assistant_snippet_Js9I7l6+HT.txt
├── assistant_snippet_KifAQa
│   └── QPu.txt
├── assistant_snippet_ky4hvYSrqP.txt
├── assistant_snippet_txjYhJf+AU.txt
├── backend
│   ├── Dockerfile
│   ├── __init__.py
│   ├── alembic.ini
│   ├── app.log
│   ├── conftest.py
│   ├── create_monitoring_tables.py
│   ├── create_sqlite_tables.py
│   ├── create_tables.py
│   ├── init_test_db.py
│   ├── prometheus.yml
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── requirements-test.txt
│   ├── requirements.txt
│   ├── run.py
│   ├── setup.py
│   ├── start.sh
│   └── test.db
├── content.py
├── core
│   ├── README.md
│   └── __init__.py
├── docker-compose.monitoring.yml
├── docker-compose.test.yml
├── docker-compose.yml
├── docs
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   ├── CURRENT_ARCHITECTURE.md
│   ├── INTEGRATION_FLOW.md
│   ├── PLANO_CONTINGENCIA.md
│   ├── deployment-plan.md
│   ├── test-plan.md
│   └── user-guide.md
├── frontend
│   ├── Dockerfile
│   ├── README.md
│   ├── babel.config.js
│   ├── eslint.config.js
│   ├── index.html
│   ├── jest.config.ts
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.cjs
│   ├── tailwind.config.js
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── tsconfig.test.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── grafana
│   └── docker-compose.prod.yml
├── install_dependencies.sh
├── load-test-summary.json
├── logs
│   ├── ai_platform.log
│   └── app.log
├── loki
│   ├── docker-compose.prod.yml
│   ├── loki-config.yml
│   └── promtail-config.yml
├── monitoring
│   └── metrics-validation-2024-12-27
├── package-lock.json
├── package.json
├── project_tree.txt
├── prometheus
│   ├── docker-compose.prod.yml
│   ├── prometheus.prod.yml
│   └── prometheus.yml
├── prometheus.yml
├── pytest.ini
├── requirements-test.txt
├── requirements.txt
├── scripts
│   ├── analyze_mfa_feedback.py
│   ├── backup.sh
│   ├── deploy-test.sh
│   ├── error-analysis.sh
│   ├── gradual-deploy.sh
│   ├── health-check.sh
│   ├── implement_mfa_improvements.py
│   ├── pre-deploy-check.sh
│   ├── resource-monitoring.sh
│   ├── restore.sh
│   ├── rollback.sh
│   ├── run-all-tests.sh
│   ├── run-load-tests.sh
│   ├── schedule-backups.sh
│   ├── setup-monitoring.sh
│   ├── setup-production.sh
│   └── validate-metrics.sh
├── setup_permissions.sh
├── shared
│   ├── cache.py
│   ├── messaging.py
│   ├── monitoring.py
│   └── requirements.txt
├── ssl
│   ├── cert.pem
│   └── key.pem
├── tempo
│   └── config.yml
├── test.db
├── test_server.py
├── udo -u postgres psql -c CREATE USER aiagency WITH PASSWORD 'aiagency123' CREATEDB;
└── venv
    └── pyvenv.cfg

16 directories, 110 files