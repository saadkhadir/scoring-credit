# 📊 Configuration Prometheus et Grafana

## Vue d'ensemble

La configuration Prometheus et Grafana a été ajoutée au projet **score-credit-project** pour monitorer en temps réel:
- Les performances de l'API
- Les métriques des prédictions
- La latence des requêtes
- Les taux d'erreur
- L'état du système

## 🏗️ Architecture

```
┌─────────────────────┐
│  Grafana (Port 3000)│  ← Dashboards de visualisation
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│Prometheus (Port 9090)│ ← Scrape les métriques
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  FastAPI (Port 8000)│  ← Endpoint /metrics
└─────────────────────┘
```

## 📦 Services Docker

### 1. **API Credit Score** (Port 8000)
- API FastAPI instrumentée avec Prometheus
- Endpoint `/metrics` pour les métriques

### 2. **Prometheus** (Port 9090)
- Scrape les métriques de l'API toutes les 10 secondes
- Stocke les données de série temporelle
- UI: http://localhost:9090

### 3. **Grafana** (Port 3000)
- Dashboards visuels
- UI: http://localhost:3000
- Credentials par défaut:
  - **Username**: admin
  - **Password**: admin123

## 🚀 Démarrage

```bash
# Démarrer tous les services
docker-compose up -d

# Consulter les logs
docker-compose logs -f

# Arrêter les services
docker-compose down
```

## 📊 Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Credit Score API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API Metrics | http://localhost:8000/metrics | Endpoint Prometheus |
| Prometheus | http://localhost:9090 | Query UI & Targets |
| Grafana | http://localhost:3000 | Dashboards |

## 📈 Métriques disponibles

### Métriques personnalisées

#### 1. **Prédictions**
```
credit_predictions_total{prediction_type, status}
credit_predictions_good_total
credit_predictions_bad_total
credit_prediction_duration_seconds (Histogram)
```

#### 2. **Modèle**
```
model_load_attempts_total{status}
active_models_total
```

#### 3. **Erreurs API**
```
api_request_errors_total{endpoint, error_type}
```

### Métriques FastAPI (automatiques)
```
http_requests_total
http_request_duration_seconds
http_requests_in_progress
```

## 🎨 Dashboard Grafana

Un dashboard pré-configuré **"Credit Score API - Monitoring"** est automatiquement provisionné avec:

- **Requêtes HTTP par seconde** (Rate)
- **Latence P95** (Gauge)
- **Distribution des codes HTTP** (Pie Chart)
- **Trafic par endpoint** (Time Series)
- **Statut API** (Status Indicator)
- **Taux de succès** (Success Rate)
- **Erreurs serveur** (5xx errors)

### Configuration du Dashboard

Le dashboard est auto-provisionné via:
```
grafana/provisioning/dashboards/credit-score-dashboard.json
```

Vous pouvez créer des dashboards supplémentaires dans l'UI Grafana.

## 🔧 Configuration Prometheus

Le fichier `prometheus.yml` configure:

```yaml
scrape_configs:
  - job_name: 'credit-score-api'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['api:8000']
```

- **Intervalle de scrape**: 10 secondes
- **Rétention des données**: 30 jours
- **Endpoint**: `/metrics`

## 📝 Exemples de queries Prometheus

### Requêtes par seconde
```promql
rate(http_requests_total[5m])
```

### Latence P95
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Taux d'erreur (5xx)
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

### Prédictions bon crédit par minute
```promql
rate(credit_predictions_good_total[1m])
```

### Prédictions mauvais crédit par minute
```promql
rate(credit_predictions_bad_total[1m])
```

### Latence moyenne des prédictions
```promql
rate(credit_prediction_duration_seconds_sum[5m]) / rate(credit_prediction_duration_seconds_count[5m])
```

## 🔐 Configuration Grafana

### Datasource Prometheus
- **URL**: http://prometheus:9090
- **Access**: Proxy
- **Status**: ✅ (Auto-configured)

Configuration via:
```
grafana/provisioning/datasources/prometheus.yml
```

### Credentials par défaut
| Champ | Valeur |
|-------|--------|
| Admin User | admin |
| Admin Password | admin123 |
| Allow Sign Up | false |

### Changer le mot de passe
1. Accédez à http://localhost:3000
2. Login avec admin/admin123
3. Configuration → Users → Admin
4. Modifier le mot de passe

## 📂 Structure des fichiers

```
score-credit-project/
├── docker-compose.yml                    # Services (API, Prometheus, Grafana)
├── prometheus.yml                        # Configuration Prometheus
├── main.py                              # API instrumentée avec Prometheus
├── requirement.txt                      # Dependencies + Prometheus
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── prometheus.yml           # Configuration Prometheus DS
        └── dashboards/
            ├── dashboard.yml            # Configuration des dashboards
            └── credit-score-dashboard.json  # Dashboard pré-configuré
```

## 🛠️ Instrumentation dans main.py

### Imports
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
```

### Configuration
```python
# Instrumenter FastAPI automatiquement
Instrumentator().instrument(app).expose(app)

# Métriques personnalisées
prediction_counter = Counter(...)
prediction_latency = Histogram(...)
```

### Enregistrement des métriques
```python
# Dans la fonction make_prediction()
prediction_counter.labels(prediction_type='single', status='success').inc()
prediction_latency.observe(duration)
```

## 📊 Alerting (Optionnel)

Vous pouvez ajouter des alertes dans `prometheus.yml`:

```yaml
rule_files:
  - "alert_rules.yml"

alertmanagers:
  - static_configs:
      - targets: ['localhost:9093']
```

Créer un fichier `alert_rules.yml`:

```yaml
groups:
  - name: credit_api_alerts
    rules:
      - alert: APIDown
        expr: up{job="credit-score-api"} == 0
        for: 1m
        
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
```

## 🐛 Troubleshooting

### Prometheus ne scrape pas les métriques

**Vérifier:**
```bash
# Les cibles Prometheus
curl http://localhost:9090/api/v1/targets

# Les métriques de l'API
curl http://localhost:8000/metrics
```

### Grafana ne se connecte pas à Prometheus

1. Vérifier la configuration réseau Docker
2. Vérifier dans Grafana: Configuration → Data Sources → Prometheus
3. Test connection devrait retourner "Data source is working"

### Logs Docker

```bash
# Logs API
docker-compose logs api

# Logs Prometheus
docker-compose logs prometheus

# Logs Grafana
docker-compose logs grafana
```

## 📚 Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)

## ✅ Checklist de vérification

- [ ] Services démarrés: `docker-compose ps`
- [ ] Prometheus scrape l'API: http://localhost:9090/targets
- [ ] Dashboard visible: http://localhost:3000
- [ ] Métriques reçues: http://localhost:8000/metrics
- [ ] Requêtes de test effectuées
- [ ] Données visibles dans Grafana

---

**Note**: Les données de Prometheus sont stockées dans un volume Docker `prometheus-data` et persistées entre les redémarrages.
