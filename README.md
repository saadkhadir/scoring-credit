# Architecture Technique - Projet Score Credit ML

## 📋 Table des Matières
1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Global](#architecture-global)
3. [Composantes Principales](#composantes-principales)
4. [Stack Technologique](#stack-technologique)
5. [Flux de Données](#flux-de-données)
6. [Infrastructure & Déploiement](#infrastructure--déploiement)
7. [Modèle ML Détails](#modèle-ml-détails)
8. [API REST Endpoints](#api-rest-endpoints)
9. [Monitoring & Observabilité](#monitoring--observabilité)

---

## Vue d'ensemble

Le projet **score-credit-project** est une application **Production-Ready** de prédiction de score de crédit basée sur le Machine Learning. L'architecture suit un pattern moderne avec :

- **Frontend** : Interface web vanilla (HTML/CSS/JavaScript)
- **Backend** : API REST asynchrone (FastAPI)
- **ML Model** : RandomForest avec preprocessing complexe (scikit-learn)
- **Model Registry** : MLflow pour versioning et gestion des modèles
- **Monitoring** : Stack complet Prometheus + Grafana
- **Conteneurisation** : Docker & Docker Compose

---

## Architecture Global

### Schéma Haut Niveau

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Web                               │
│              (HTML/CSS/JavaScript - Port 8000)               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • Endpoints: /api/predict, /api/predict-batch       │  │
│  │ • Validation: Pydantic Models                       │  │
│  │ • ML Pipeline: Preprocessing + RandomForest         │  │
│  │ • Caching: ModelCache Singleton                     │  │
│  │ • Metrics: Prometheus Integration                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────┬────────────────────┘
             │                          │
             ▼                          ▼
    ┌─────────────────┐        ┌──────────────────┐
    │ MLflow Registry │        │ Prometheus Metrics│
    │ (Model Store)   │        │ (Time-Series DB) │
    └────────┬────────┘        └────────┬─────────┘
             │                          │
             ▼                          ▼
    ┌──────────────────────────────────────────┐
    │         Grafana Dashboards               │
    │    (Real-time ML & API Monitoring)       │
    └──────────────────────────────────────────┘
```

---

## Composantes Principales

### 1️⃣ Frontend (Client-Side)

**Localisation**: `templates/index.html`

**Caractéristiques**:
- Vanilla JavaScript (pas de framework)
- Design moderne avec palette Midnight Vault
- Responsive layout (Space Grotesk font)
- Form handling avec validation côté client
- AJAX requests asynchrones
- Affichage du résultat de prédiction avec indicateurs visuels

**Technologies**:
- HTML5
- CSS3 (Flexbox, Grid, Animations)
- JavaScript ES6+
- Fetch API pour les requêtes HTTP

---

### 2️⃣ Backend API (FastAPI)

**Localisation**: `main.py`

**Architecture**:

```
FastAPI Application
├── Routes
│   ├── GET /                    → Home page
│   ├── GET /api/health          → Health check
│   ├── GET /api/model-info      → Model metadata
│   ├── POST /api/predict        → Single prediction
│   ├── POST /api/predict-batch  → Batch predictions
│   ├── POST /api/reload-model   → Reload model
│   ├── GET /metrics             → Prometheus metrics
│   └── GET /docs                → Swagger UI
│
├── Data Models (Pydantic)
│   ├── CreditApplicationInput   → Input schema
│   ├── PredictionResponse       → Output schema
│   ├── BatchPredictionRequest   → Batch input
│   └── BatchPredictionResponse  → Batch output
│
├── ML Processing
│   ├── ModelCache               → Model loading & caching
│   ├── Preprocessor             → Data transformation
│   └── RandomForest             → Predictions
│
├── Monitoring
│   ├── Prometheus Metrics       → Counter, Histogram, Gauge
│   ├── prometheus-fastapi-instrumentator
│   └── Health checks
│
└── Error Handling
    └── Global exception handler
```

**Détails du Flow Request**:

1. **Input Validation** : Pydantic valide JSON contre `CreditApplicationInput`
2. **Data Preprocessing** : `CustomPreprocessor` transforme les données
3. **Model Loading** : `ModelCache` charge depuis MLflow Registry
4. **Prediction** : `model.predict()` + `model.predict_proba()`
5. **Risk Calculation** : Niveau de risque basé sur probability
6. **Metrics Recording** : Prometheus metrics incrémentées
7. **Response** : JSON sérialisé avec timestamp

---

### 3️⃣ Machine Learning Pipeline

**Composantes**:

#### 3.1 Features d'Entrée (21 total)

**Numériques (6)**:
```
- Duration in month (1-120)
- Credit amount (>0)
- Installment rate (1-4%)
- Age in years (18-100)
- Number of existing credits (1-4)
- Number of dependents (1-2)
```

**Ordinales (5)** - Codes A** avec mappings:
```
- Status of checking account (A11→0, A12→1, A13→2, A14→3)
- Credit history (A30→0 ... A34→4)
- Savings account (A61→0 ... A65→4)
- Employment since (A71→0 ... A75→4)
- Job (A171→0, A172→1, A173→2, A174→3)
```

**Nominales (8)** - Catégories sans ordre:
```
- Purpose (A43, A44, ...)
- Personal status & sex (A93, A94, ...)
- Other debtors (A101, A102, ...)
- Property (A121, A122, ...)
- Other installment plans (A143, A144, ...)
- Housing (A151, A152, A153)
- Telephone (A191, A192)
- Foreign worker (A201, A202)
```

#### 3.2 Preprocessing Pipeline

```python
Pipeline([
    ('preprocessor', CustomPreprocessor([
        1. Apply ordinal mappings (A11→0, etc)
        2. One-Hot Encoding for nominal features
        3. StandardScaler on numerical features
    ])),
    ('classifier', RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42
    ))
])
```

#### 3.3 Modèle RandomForest

**Configuration**:
```
n_estimators: 100 trees
max_depth: 10 levels
min_samples_split: 20 samples
min_samples_leaf: 10 samples
random_state: 42 (reproducibilité)
n_jobs: -1 (parallélisation)
```

**Output**:
- `predict()` : 0 (Bad Credit) ou 1 (Good Credit)
- `predict_proba()` : [P_bad, P_good] ∈ [0,1]

#### 3.4 Risk Level Classification

```
IF P_good >= 0.7    → RISK = LOW
ELIF P_good >= 0.4  → RISK = MEDIUM
ELSE (P_good < 0.4) → RISK = HIGH
```

---

### 4️⃣ MLflow Model Registry

**Purpose**: Version control, artifact storage, model promotion

**Structure**:

```
MLflow Setup
├── Tracking URI: sqlite:///mlflow.db
├── Experiment: credit-score-production
├── Runs: Each training session
│   └── Artifacts:
│       ├── classification_report.txt
│       ├── confusion_matrix.txt
│       ├── model_metadata.json
│       ├── conda.yaml
│       ├── python_env.yaml
│       ├── MLmodel (config)
│       ├── requirements.txt
│       └── model.pkl
│
└── Model Registry
    └── RDF_score_pipeline
        ├── Version 1: Staging
        ├── Version 2: Production ← Used by API
        └── Version 3: None
```

**Workflow**:
1. Script exécute l'entraînement
2. MLflow logs les métriques, params, artifacts
3. Modèle enregistré dans Model Registry
4. Promotion manuelle vers "Production" stage
5. API charge depuis `models:/RDF_score_pipeline/Production`

---

### 5️⃣ MLflow Database

**Type**: SQLite (fichier local `mlflow.db`)

**Contenu**:
- Experiment metadata
- Run information (run_id, timestamps, parameters)
- Metric history (accuracy, loss, etc.)
- Model registry entries
- Artifact location references

---

## Stack Technologique

### Backend Stack

| Composant | Technologie | Version | Usage |
|-----------|------------|---------|-------|
| **Runtime** | Python | 3.13.2 | Language |
| **Web Framework** | FastAPI | Latest | REST API |
| **Web Server** | Uvicorn | With standard extras | ASGI Server |
| **ML Framework** | scikit-learn | 1.8.0 | Model training & inference |
| **Data Processing** | pandas | 2.3.3 | DataFrame operations |
| **Numerical** | numpy | (via pandas) | Array operations |
| **Serialization** | joblib | 1.5.2 | Model saving |
| **Model Registry** | MLflow | Latest | Version control |
| **Validation** | Pydantic | (FastAPI included) | Input validation |
| **Monitoring** | prometheus-client | ≥0.17.0 | Metrics export |
| **FastAPI Integration** | prometheus-fastapi-instrumentator | ≥6.0.0 | Auto-instrumentation |
| **CORS** | FastAPI middleware | Built-in | Cross-origin requests |

### Infrastructure Stack

| Composant | Technologie | Purpose |
|-----------|------------|---------|
| **Conteneurisation** | Docker | Container images |
| **Orchestration** | Docker Compose | Multi-container setup |
| **Monitoring (Metrics)** | Prometheus | Time-series database |
| **Monitoring (Visualization)** | Grafana | Dashboards & alerts |
| **Base Image** | python:3.13.2-slim | Lightweight Python runtime |

### Frontend Stack

| Composant | Technologie | Purpose |
|-----------|------------|---------|
| **Structure** | HTML5 | Markup |
| **Styling** | CSS3 | Layout & design |
| **Interactivité** | Vanilla JavaScript | Logic & API calls |
| **Font** | Space Grotesk (Google Fonts) | Typography |
| **API Client** | Fetch API | HTTP requests |

---

## Flux de Données

### 🔄 Flux Training (Offline - script.py)

```
1. Load Data
   └─ CSV (estadistical.csv) → Pandas DataFrame
   
2. Data Cleaning
   └─ Column normalization, target mapping (2→0, 1→1)
   
3. Train/Test Split
   └─ 70% train, 30% test (stratified)
   
4. Feature Separation
   ├─ Numerical features (6)
   ├─ Ordinal categorical (5)
   └─ Nominal categorical (8)
   
5. Preprocessing Fit
   └─ CustomPreprocessor.fit(X_train)
      ├─ Learn ordinal mappings
      ├─ Learn one-hot categories
      └─ Fit StandardScaler
   
6. Model Training
   └─ Pipeline.fit(X_train, y_train)
      └─ RandomForestClassifier(100 trees)
   
7. Evaluation
   ├─ predict(X_test) → y_pred
   ├─ predict_proba(X_test) → probabilities
   ├─ Accuracy calculation
   ├─ Classification report
   └─ Confusion matrix
   
8. MLflow Logging
   ├─ Log metrics (accuracy)
   ├─ Log parameters (n_estimators, etc.)
   ├─ Log artifacts (reports)
   ├─ Log model (entire pipeline)
   └─ Create model signature
   
9. Model Registration
   └─ MLflow Model Registry
      └─ RDF_score_pipeline (new version)
   
10. Promotion
    └─ Stage: Staging → Production
       └─ Archive previous Production version
```

### 🎯 Flux Inference (Online - API)

```
1. Client Request
   └─ HTTP POST /api/predict
      └─ JSON payload with 21 features
   
2. Input Validation
   └─ Pydantic validates against CreditApplicationInput
      └─ Type checking, range validation, field aliases
   
3. Convert to DataFrame
   └─ CreditApplicationInput.to_dataframe()
      └─ Original column names restored
   
4. Load Model (from Cache)
   └─ ModelCache.get_model()
      ├─ Check if in memory cache
      └─ If not, load from MLflow Registry
   
5. Preprocessing
   └─ CustomPreprocessor.transform(X)
      ├─ Ordinal mapping (A12→1, etc.)
      ├─ One-Hot Encoding
      └─ StandardScaler (using training statistics)
   
6. Model Prediction
   ├─ prediction = model.predict(X)[0] → 0 or 1
   └─ probabilities = model.predict_proba(X)[0] → [P_bad, P_good]
   
7. Risk Calculation
   └─ risk_level = calculate_risk_level(P_good)
      └─ LOW / MEDIUM / HIGH
   
8. Metrics Recording
   ├─ prediction_counter.inc() → total count
   ├─ prediction_good_credit.inc() (if pred==1)
   ├─ prediction_latency.observe(duration) → histogram
   └─ Send to Prometheus
   
9. Response Building
   └─ PredictionResponse {
      ├─ prediction (int): 0 or 1
      ├─ probability_good_credit (float)
      ├─ probability_bad_credit (float)
      ├─ risk_level (str): LOW/MEDIUM/HIGH
      ├─ model_version (str)
      └─ timestamp (str)
   }
   
10. Return to Client
    └─ HTTP 200 OK
       └─ JSON response
```

---

## Infrastructure & Déploiement

### Docker Configuration

**Base Image**: `python:3.13.2-slim`

**Layers**:
1. Update apt, install gcc/g++ (compilation tools)
2. Copy requirements.txt
3. Pip install Python dependencies
4. Copy project files
5. Create /app/model directory
6. Copy model.pkl from mlruns

**Healthcheck**: 
```bash
python -c "import requests; requests.get('http://localhost:8000/api/health')"
Interval: 30s | Timeout: 10s | Retries: 3 | Start period: 10s
```

**Volume Mounts**:
```yaml
volumes:
  - ./mlruns:/app/mlruns           # Model artifacts sync
  - ./mlflow.db:/app/mlflow.db     # MLflow database sync
```

**Environment Variables**:
```
MLFLOW_TRACKING_URI=sqlite:///mlflow.db
```

### Docker Compose Services

#### Service 1: API (credit-score-api)

```yaml
build: .                           # Build from Dockerfile
container_name: credit-score-api
ports:
  - "8000:8000"                    # API endpoint
environment:
  - MLFLOW_TRACKING_URI=sqlite:///mlflow.db
volumes:
  - ./mlruns:/app/mlruns
  - ./mlflow.db:/app/mlflow.db
networks:
  - monitoring
healthcheck: ✓ enabled
depends_on:
  - prometheus
```

#### Service 2: Prometheus

```yaml
image: prom/prometheus:latest
container_name: prometheus
ports:
  - "9090:9090"                    # Metrics UI
volumes:
  - ./prometheus.yml:/etc/prometheus/prometheus.yml
  - prometheus-data:/prometheus    # Named volume
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.path=/prometheus'
  - '--storage.tsdb.retention.time=30d'
networks:
  - monitoring
healthcheck: ✓ enabled
```

#### Service 3: Grafana

```yaml
image: grafana/grafana:latest
container_name: grafana
ports:
  - "3000:3000"                    # Dashboard UI
environment:
  - GF_SECURITY_ADMIN_USER=admin
  - GF_SECURITY_ADMIN_PASSWORD=admin123
  - GF_INSTALL_PLUGINS=
  - GF_USERS_ALLOW_SIGN_UP=false
volumes:
  - grafana-data:/var/lib/grafana
  - ./grafana/provisioning:/etc/grafana/provisioning
networks:
  - monitoring
depends_on:
  - prometheus
healthcheck: ✓ enabled
```

### Network & Volumes

**Network**: `monitoring` (bridge driver)
- Enables inter-container communication
- Services accessible by name (credit-score-api, prometheus, grafana)

**Named Volumes**:
- `prometheus-data`: Persist metrics
- `grafana-data`: Persist dashboards

---

## Modèle ML Détails

### Training Configuration

**Dataset**:
- Source: `data/estadistical.csv`
- Samples: 1000
- Features: 21 (input) + 1 (target)
- Target: Binary classification
  - 0 = Bad Credit (Reject)
  - 1 = Good Credit (Approve)

**Train/Test Split**:
- Training: 700 samples (70%)
- Testing: 300 samples (30%)
- Stratified split (preserve class distribution)

**Evaluation Metrics**:
- Accuracy
- Precision, Recall, F1-Score (per class)
- Confusion Matrix

### Model Signature

MLflow infers model signature from training data:

```python
signature = infer_signature(X_train, pipeline.predict(X_train))
```

**Input**: CreditApplicationInput (21 features)
**Output**: int (0 or 1)

---

## API REST Endpoints

### 1. GET `/`

**Description**: Home page
**Response**: HTML file (index.html)
**Status**: 200 OK

### 2. GET `/api/health`

**Description**: Health check endpoint
**Response**:
```json
{
  "status": "healthy",
  "model_path": "/app/model/model.pkl",
  "model_loaded": true,
  "timestamp": "2024-12-14T10:30:45.123456"
}
```
**Status**: 200 OK (or 503 Service Unavailable)

### 3. GET `/api/model-info`

**Description**: Model metadata
**Response**:
```json
{
  "name": "RDF_score_pipeline",
  "version": "1",
  "stage": "Production",
  "description": "RandomForest Credit Score Model"
}
```
**Status**: 200 OK

### 4. POST `/api/predict`

**Description**: Single prediction
**Request Body**:
```json
{
  "Duration in month": 12,
  "Credit amount": 5000.0,
  "Installment rate in percentage of disposable income": 2,
  "Age in years": 35,
  "Number of existing credits at this bank": 1,
  "Number of people being liable to provide maintenance for": 1,
  "Status of existing checking account": "A12",
  "Credit history": "A32",
  "Savings account/bonds": "A61",
  "Present employment since": "A73",
  "Job": "A173",
  "Purpose": "A43",
  "Personal status and sex": "A93",
  "Other debtors / guarantors": "A101",
  "Property": "A121",
  "Other installment plans": "A143",
  "Housing": "A152",
  "Telephone": "A192",
  "foreign worker": "A201"
}
```

**Response**:
```json
{
  "prediction": 1,
  "probability_good_credit": 0.85,
  "probability_bad_credit": 0.15,
  "risk_level": "LOW",
  "model_version": "1",
  "timestamp": "2024-12-14T10:30:45.123456"
}
```
**Status**: 200 OK

### 5. POST `/api/predict-batch`

**Description**: Batch predictions
**Request Body**:
```json
{
  "applications": [
    { /* CreditApplicationInput 1 */ },
    { /* CreditApplicationInput 2 */ },
    ...
  ]
}
```

**Response**:
```json
{
  "predictions": [
    { /* PredictionResponse 1 */ },
    { /* PredictionResponse 2 */ },
    ...
  ],
  "total_processed": 10,
  "model_version": "1",
  "timestamp": "2024-12-14T10:30:45.123456"
}
```
**Status**: 200 OK

### 6. POST `/api/reload-model`

**Description**: Force reload model from registry
**Response**: Success message
**Status**: 200 OK

### 7. GET `/metrics`

**Description**: Prometheus metrics endpoint
**Response**: Text format (OpenMetrics)
```
# HELP credit_predictions_total Total number of predictions
# TYPE credit_predictions_total counter
credit_predictions_total{prediction_type="single",status="success"} 42.0
credit_predictions_total{prediction_type="single",status="error"} 2.0
...
```
**Status**: 200 OK

### 8. GET `/docs`

**Description**: Swagger UI
**Response**: Interactive API documentation
**Status**: 200 OK

### 9. GET `/redoc`

**Description**: ReDoc API documentation
**Response**: Alternative API documentation
**Status**: 200 OK

---

## Monitoring & Observabilité

### Prometheus Metrics

#### Counters

1. **credit_predictions_total**
   - Labels: `prediction_type` (single/batch), `status` (success/error)
   - Incremented on each prediction request
   - Cumulative count

2. **credit_predictions_good_total**
   - Incremented when prediction == 1 (Good Credit)
   - Subset of total predictions

3. **credit_predictions_bad_total**
   - Incremented when prediction == 0 (Bad Credit)
   - Subset of total predictions

4. **api_request_errors_total**
   - Labels: `endpoint`, `error_type`
   - Tracks API errors by endpoint

5. **model_load_attempts_total**
   - Labels: `status` (success/failure)
   - Tracks model loading attempts

#### Histograms

1. **credit_prediction_duration_seconds**
   - Buckets: 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0
   - Measures request latency
   - Auto-instrumented by prometheus-fastapi-instrumentator

#### Gauges

1. **active_models_total**
   - Number of models currently loaded in memory
   - Real-time count

### Prometheus Configuration

**Config File**: `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'credit-score-api'
    static_configs:
      - targets: ['credit-score-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

**Storage**:
- TSDB Path: `/prometheus`
- Retention: 30 days
- Time-series indexed by labels

### Grafana Dashboards

**Pre-provisioned**: `grafana/provisioning/dashboards/credit-score-dashboard.json`

**Visualizations**:
1. **Prediction Volume** (Time series)
   - Total predictions over time
   - Good vs Bad split

2. **Latency Distribution** (Histogram)
   - P50, P95, P99 latencies
   - Track API performance

3. **Error Rate** (Gauge)
   - Percentage of failed requests
   - Alert threshold: > 5%

4. **Model Load Status** (Gauge)
   - Active models loaded
   - Load success/failure ratio

5. **Credit Distribution** (Pie chart)
   - Percentage Good vs Bad predictions
   - Real-time update

**Alerting Rules**: `alert_rules.yml`
- High error rate
- Long latency
- Model unavailable
- Prometheus down

---

## 📊 Résumé Architecture

### Caractéristiques Clés

✅ **Production-Ready**:
- Health checks sur tous les services
- Error handling et logging
- Graceful shutdown
- Automated restart policies

✅ **Scalable**:
- Stateless API design
- Model caching pour performance
- Batch prediction support
- Metrics for monitoring

✅ **Maintainable**:
- Clear separation of concerns
- Type hints with Pydantic
- MLflow for model versioning
- Docker for reproducibility

✅ **Observable**:
- Prometheus metrics
- Grafana dashboards
- Health checks
- Detailed logging

✅ **Secure**:
- Input validation
- CORS configurable
- Error messages non-exposing internals
- Dependency pinning

### Points d'Extension

1. **Ajouter des modèles** :
   - Train nouveau modèle
   - Register dans MLflow
   - Update model loading logic

2. **Améliorer preprocessing**:
   - Modifier CustomPreprocessor
   - Retrain avec nouvelles transformations
   - New model version

3. **Ajouter des features**:
   - Extend CreditApplicationInput
   - Update preprocessing
   - Retrain avec nouvelles données

4. **Alertes additionnelles**:
   - Définir dans alert_rules.yml
   - Configure dans Grafana
   - Notification channels

---

## 🚀 Déploiement

### Pré-requis
- Docker >= 20.10
- Docker Compose >= 1.29
- 2GB RAM minimum
- 5GB disk space

### Commandes

```bash
# Build et démarrage
docker-compose up -d

# Vérifier les logs
docker-compose logs -f api

# Arrêt
docker-compose down

# Volume cleanup
docker volume prune
```

### Endpoints Accessibles

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

---

**Document généré**: 14 Décembre 2024
**Version Architecture**: 2.0.0
**Status**: Production Ready
