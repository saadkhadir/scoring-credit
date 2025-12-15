# 📐 Architecture Techniques du Projet Score-Credit - Index des Diagrammes PlantUML

## 📑 Vue d'ensemble

Cette documentation contient **4 diagrammes PlantUML complètement détaillés** qui décrivent l'architecture technique complète du projet **score-credit-project**.

---

## 📊 Diagrammes Disponibles

### 1️⃣ **ARCHITECTURE_DIAGRAM.puml**
**Type**: Architecture Générale Complète
**Focus**: Composantes principales et flux de données haut niveau

```
📍 Localisation: ARCHITECTURE_DIAGRAM.puml
📐 Type: Component & C4 Diagram Hybrid
🎯 Audience: Architectes, Tech Leads
📊 Complexité: Très Haute (détaillée)
```

**Contient**:
- ✅ Frontend (HTML/CSS/JavaScript)
- ✅ Backend API (FastAPI, Pydantic, Endpoints)
- ✅ ML Processing (Preprocessing, Classifier)
- ✅ Prometheus & Grafana
- ✅ MLflow Integration
- ✅ Data & Storage
- ✅ Training Pipeline (Offline)
- ✅ All connections & data flows

**Sections Principales**:
1. Frontend Client
2. Backend API avec tous les endpoints
3. ML Model Processing Pipeline
4. Monitoring & Metrics Collection
5. MLflow Integration
6. Storage & Databases
7. Training Pipeline (offline)

**Utilité**: 
- Comprendre l'architecture globale du système
- Identifier toutes les composantes
- Voir les interactions entre services
- Planifier les modifications d'architecture

---

### 2️⃣ **DEPLOYMENT_ARCHITECTURE.puml**
**Type**: Architecture de Déploiement Docker
**Focus**: Conteneurisation et infrastructure

```
📍 Localisation: DEPLOYMENT_ARCHITECTURE.puml
📐 Type: Deployment & Infrastructure Diagram
🎯 Audience: DevOps, SRE, Infrastructure Engineers
📊 Complexité: Haute
```

**Contient**:
- ✅ Docker Engine
- ✅ 3 Conteneurs (API, Prometheus, Grafana)
- ✅ Bridge Network ('monitoring')
- ✅ Volumes & Bind Mounts
- ✅ Port Mappings
- ✅ Health Checks
- ✅ Host File System
- ✅ Dependencies Management

**Détails**:
- **API Container**
  - Image base: python:3.13.2-slim
  - Port mapping: 8000:8000
  - Health check configuration
  - Volume mounts (mlruns, mlflow.db)

- **Prometheus Container**
  - Port mapping: 9090:9090
  - Data storage configuration
  - Scrape settings (15s, 30d retention)

- **Grafana Container**
  - Port mapping: 3000:3000
  - Provisioning paths
  - Data volumes

- **File System**
  - Project structure
  - Docker Compose file
  - Configuration files
  - Model artifacts directory

**Utilité**:
- Comprendre le déploiement Docker
- Identifier les volumes et mounts
- Gérer les configurations de containers
- Troubleshoot les problèmes de déploiement
- Planifier le scaling

---

### 3️⃣ **ML_DATAFLOW_ARCHITECTURE.puml**
**Type**: Flux de Données ML Détaillé
**Focus**: Training et Inference pipelines

```
📍 Localisation: ML_DATAFLOW_ARCHITECTURE.puml
📐 Type: Sequence & Data Flow Diagram
🎯 Audience: Data Scientists, ML Engineers
📊 Complexité: Très Haute (très détaillée)
```

**Contient**:
- ✅ **Phase Training** (script.py)
  - Data loading (CSV → DataFrame)
  - Data cleaning & normalization
  - Train/test split
  - Feature engineering (num/ordinal/nominal)
  - CustomPreprocessor logic
  - RandomForest configuration
  - Model training
  - Evaluation metrics
  - MLflow logging & registration
  - Model promotion to Production

- ✅ **Phase Inference** (API main.py)
  - Request reception & validation
  - Pydantic schema validation
  - Data preprocessing (matching training)
  - Model loading from cache/registry
  - Prediction & probability calculation
  - Risk level computation
  - Response building
  - Metrics recording
  - JSON serialization

- ✅ **Batch Inference**
  - Batch request handling
  - Loop processing
  - Aggregated response

- ✅ **Monitoring**
  - Prometheus metrics
  - Grafana visualization
  - Real-time alerts

**Détails Techniques**:
- Feature types (6 num, 5 ordinal, 8 nominal)
- Preprocessing steps (mapping, encoding, scaling)
- RandomForest hyperparameters
- Probability calibration
- Risk classification logic

**Utilité**:
- Comprendre le pipeline ML complet
- Debugging des prédictions
- Feature engineering
- Model retraining
- Performance optimization

---

### 4️⃣ **TECHNOLOGY_STACK.puml**
**Type**: Stack Technologique Complète
**Focus**: Dépendances et versions

```
📍 Localisation: TECHNOLOGY_STACK.puml
📐 Type: Dependency Graph & Technology Diagram
🎯 Audience: Developers, Architects, DevOps
📊 Complexité: Moyenne-Haute
```

**Contient**:
- ✅ **Presentation Layer**
  - Browser/Frontend
  - HTML5/CSS3/JavaScript
  - Responsive Design

- ✅ **API Layer**
  - FastAPI (async framework)
  - Uvicorn (ASGI server)
  - Pydantic (validation)
  - CORS middleware

- ✅ **ML Layer**
  - scikit-learn 1.8.0
  - CustomPreprocessor
  - RandomForest Classifier
  - Model Serialization (joblib)

- ✅ **Data Layer**
  - pandas 2.3.3
  - numpy
  - CSV Reader

- ✅ **Model Registry**
  - MLflow (versioning)
  - SQLite (mlflow.db)
  - Artifact Storage

- ✅ **Monitoring Layer**
  - prometheus-client >=0.17.0
  - prometheus-fastapi-instrumentator >=6.0.0
  - Prometheus Database
  - Grafana Dashboards

- ✅ **Infrastructure Layer**
  - Docker
  - Docker Compose
  - python:3.13.2-slim base image

- ✅ **Runtime Environment**
  - Python 3.13.2
  - System libraries (gcc, g++)
  - Linux Debian Slim

**Versions Clés**:
| Composant | Version | Notes |
|-----------|---------|-------|
| Python | 3.13.2 | Latest stable |
| FastAPI | Latest | Async/await |
| scikit-learn | 1.8.0 | Pinned |
| pandas | 2.3.3 | Pinned |
| joblib | 1.5.2 | Model serialization |
| prometheus-client | ≥0.17.0 | Metrics |
| Prometheus | Latest | TSDB |
| Grafana | Latest | Dashboards |
| Docker | ≥20.10 | Container runtime |

**Utilité**:
- Comprendre les dépendances
- Vérifier les versions compatibles
- Planifier les upgrades
- Identifier les conflits
- Requirements management

---

## 🎯 Comment Utiliser Ces Diagrammes

### Pour Comprendre l'Architecture
1. **Commencez par** : `ARCHITECTURE_DIAGRAM.puml`
   - Vue d'ensemble complète
   - Identifie toutes les composantes
   - Comprendre les interactions

2. **Puis explorez** : `ML_DATAFLOW_ARCHITECTURE.puml`
   - Détails du flux ML
   - Training vs Inference
   - Data transformations

3. **Pour déploiement** : `DEPLOYMENT_ARCHITECTURE.puml`
   - Configuration Docker
   - Volumes & networks
   - Port mappings

4. **Pour dépendances** : `TECHNOLOGY_STACK.puml`
   - Versions des packages
   - Dépendances entre couches
   - Requirements

### Pour Modifications de Code

**Si vous modifiez**:
- **Frontend** → Voir `ARCHITECTURE_DIAGRAM.puml` (section Frontend)
- **API endpoints** → Voir `ARCHITECTURE_DIAGRAM.puml` (section API Endpoints)
- **ML model** → Voir `ML_DATAFLOW_ARCHITECTURE.puml` (Training/Inference)
- **Preprocessing** → Voir `ML_DATAFLOW_ARCHITECTURE.puml` (Data Preprocessing)
- **Docker setup** → Voir `DEPLOYMENT_ARCHITECTURE.puml`
- **Dépendances** → Voir `TECHNOLOGY_STACK.puml`

### Pour Documentation
- Utiliser ces diagrammes dans les documentation
- Partager avec les nouvelles équipes
- Présenter aux stakeholders
- Planning technique

### Pour Troubleshooting
1. **L'API ne répond pas** → Check `DEPLOYMENT_ARCHITECTURE.puml`
2. **Erreur de prédiction** → Check `ML_DATAFLOW_ARCHITECTURE.puml`
3. **Métriques manquantes** → Check `ARCHITECTURE_DIAGRAM.puml` (Monitoring)
4. **Dépendance manquante** → Check `TECHNOLOGY_STACK.puml`

---

## 📋 Architecture Résumé

### Composantes Principales
```
Frontend (HTML/CSS/JS)
    ↓ HTTP REST
FastAPI Backend (Port 8000)
    ├─ Validation (Pydantic)
    ├─ ML Pipeline (scikit-learn)
    └─ Metrics (Prometheus)
    ↓
MLflow Registry
    └─ Model Artifacts
    ↓
Prometheus (Port 9090)
    ↓
Grafana Dashboards (Port 3000)
```

### Stack Technologique
```
Language: Python 3.13.2
Web: FastAPI + Uvicorn
ML: scikit-learn + pandas
Models: MLflow Registry
Monitoring: Prometheus + Grafana
Containers: Docker + Docker Compose
```

### Deployment
```
3 Docker Containers:
- credit-score-api (Port 8000)
- prometheus (Port 9090)
- grafana (Port 3000)

Network: 'monitoring' bridge
Volumes: mlruns/, mlflow.db
```

---

## 🔄 Flux Principaux

### 1. Training Workflow
```
Data (CSV) → Load → Clean → Split → Preprocess → Train → Evaluate → MLflow → Production
```

### 2. Inference Workflow
```
HTTP Request → Validate → Preprocess → Predict → Risk Calc → Response → Metrics
```

### 3. Monitoring Workflow
```
Metrics → Prometheus → Storage → Grafana → Dashboards → Alerts
```

---

## 📝 Documentation Associée

Cette architecture est documentée dans:
- **ARCHITECTURE_DOCUMENTATION.md** : Documentation détaillée complète
- **ARCHITECTURE_DIAGRAM.puml** : Diagramme global
- **DEPLOYMENT_ARCHITECTURE.puml** : Déploiement
- **ML_DATAFLOW_ARCHITECTURE.puml** : Flux ML
- **TECHNOLOGY_STACK.puml** : Stack technique

---

## 🚀 Prochaines Étapes

Pour continuer l'exploration:

1. **Lancer le projet**:
   ```bash
   docker-compose up -d
   ```

2. **Accéder aux services**:
   - API: http://localhost:8000
   - Swagger: http://localhost:8000/docs
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000

3. **Tester une prédiction**:
   ```bash
   curl -X POST http://localhost:8000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"Duration in month": 12, ...}'
   ```

4. **Consulter les métriques**:
   - Prometheus: http://localhost:9090/graph
   - Grafana: http://localhost:3000/d/...

---

**Architecture Version**: 2.0.0
**Documentation Date**: 14 Décembre 2024
**Status**: Production Ready ✅
**All Diagrams**: PlantUML Format (.puml)
**Rendering**: Supported by most UML tools, GitHub, GitLab, etc.

---

## 📞 Notes

Ces diagrammes sont:
- ✅ Complets et détaillés
- ✅ À jour avec le code source
- ✅ Prêts pour documentation
- ✅ Prêts pour présentation
- ✅ En format PlantUML standard

Pour visualiser les diagrammes:
1. VS Code avec extension PlantUML
2. GitHub/GitLab (rendering automatique)
3. PlantUML Online Editor: https://www.plantuml.com/plantuml/uml/
4. Exporter en PNG/PDF via ces outils
