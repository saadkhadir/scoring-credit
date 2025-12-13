# 📊 Monitoring avec Prometheus et Grafana

## 🎯 Objectif

Ajouter une stack de **monitoring complet** au projet **score-credit-project** avec:
- ✅ **Prometheus** pour la collecte des métriques
- ✅ **Grafana** pour la visualisation
- ✅ **Métriques personnalisées** pour les prédictions
- ✅ **Dashboards pré-configurés**
- ✅ **Alertes disponibles** (optionnel)

---

## 📦 Fichiers ajoutés/modifiés

### ✨ Nouveaux fichiers

```
├── docker-compose.yml                    (MODIFIÉ - ajout Prometheus & Grafana)
├── prometheus.yml                        (NOUVEAU - config Prometheus)
├── alert_rules.yml                       (NOUVEAU - règles d'alertes optionnelles)
├── requirement.txt                       (MODIFIÉ - deps Prometheus)
├── main.py                               (MODIFIÉ - instrumentation Prometheus)
├── MONITORING_SETUP.md                   (NOUVEAU - documentation complète)
├── test_monitoring.py                    (NOUVEAU - script de test)
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── prometheus.yml            (NOUVEAU)
        └── dashboards/
            ├── dashboard.yml             (NOUVEAU)
            └── credit-score-dashboard.json (NOUVEAU)
```

---

## 🚀 Démarrage rapide

### 1. Démarrer la stack

```bash
cd score-credit-project
docker-compose up -d
```

**Attendez 30 secondes** que tous les services se lancent.

### 2. Vérifier le statut

```bash
docker-compose ps
```

Output attendu:
```
NAME                COMMAND                  SERVICE            STATUS
credit-score-api    python main.py           api                Up
grafana             /run.sh                  grafana            Up
prometheus          /bin/prometheus ...      prometheus         Up
```

### 3. Tester le monitoring

```bash
python test_monitoring.py
```

---

## 🌐 Accès aux services

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| **API** | http://localhost:8000 | N/A | N/A |
| **API Docs** | http://localhost:8000/docs | N/A | N/A |
| **Prometheus** | http://localhost:9090 | N/A | N/A |
| **Grafana** | http://localhost:3000 | admin | admin123 |

---

## 📊 Dashboard principal

**Nom**: Credit Score API - Monitoring

### Panneaux disponibles

1. **Requêtes HTTP/sec** - Tendance du trafic
2. **Latence P95** - Performance en temps réel
3. **Distribution codes HTTP** - Répartition 2xx/4xx/5xx
4. **Trafic par endpoint** - Charge par route
5. **Statut API** - Indicateur up/down
6. **Taux de succès** - Percentage de requêtes réussies
7. **Erreurs serveur** - Nombre d'erreurs 5xx

---

## 📈 Métriques disponibles

### Prédictions ML

```promql
# Nombre total de prédictions
credit_predictions_total

# Prédictions: BON crédit
credit_predictions_good_total

# Prédictions: MAUVAIS crédit  
credit_predictions_bad_total

# Latence des prédictions (Histogram)
credit_prediction_duration_seconds
```

### API HTTP

```promql
# Requêtes HTTP totales (par status, endpoint, method)
http_requests_total

# Durée des requêtes (Histogram)
http_request_duration_seconds

# Requêtes en cours
http_requests_in_progress
```

---

## 📝 Exemples de queries PromQL

### Trafic
```promql
# RPS (requêtes par seconde)
rate(http_requests_total[5m])

# RPS par endpoint
sum(rate(http_requests_total[5m])) by (endpoint)
```

### Performance
```promql
# Latence P50, P95, P99
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Erreurs
```promql
# Taux d'erreur 5xx
sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)

# Taux de succès
sum(rate(http_requests_total{status=~"2.."}[5m])) 
/ sum(rate(http_requests_total[5m]))
```

### Prédictions
```promql
# Prédictions BON crédit / min
rate(credit_predictions_good_total[1m])

# Prédictions MAUVAIS crédit / min
rate(credit_predictions_bad_total[1m])

# Latence moyenne des prédictions
rate(credit_prediction_duration_seconds_sum[5m]) 
/ rate(credit_prediction_duration_seconds_count[5m])
```

---

## 🔧 Configuration personnalisée

### Modifier l'intervalle de scrape

**File**: `prometheus.yml`
```yaml
scrape_configs:
  - job_name: 'credit-score-api'
    scrape_interval: 10s  # ← Modifier ici
```

### Modifier les credentials Grafana

**File**: `docker-compose.yml`
```yaml
grafana:
  environment:
    - GF_SECURITY_ADMIN_USER=admin      # ← Modifier
    - GF_SECURITY_ADMIN_PASSWORD=admin123  # ← Modifier
```

### Ajouter des alertes

**File**: `alert_rules.yml`

1. Décommenter dans `prometheus.yml`:
```yaml
rule_files:
  - "alert_rules.yml"
```

2. Ajouter vos règles dans `alert_rules.yml`

---

## 🔍 Diagnostics

### Vérifier que Prometheus scrape l'API

```
curl http://localhost:9090/api/v1/targets
```

### Vérifier les métriques de l'API

```
curl http://localhost:8000/metrics | grep credit_
```

### Consulter les logs

```bash
# API
docker-compose logs api -f

# Prometheus
docker-compose logs prometheus -f

# Grafana
docker-compose logs grafana -f
```

### Redémarrer un service

```bash
docker-compose restart api
docker-compose restart prometheus
docker-compose restart grafana
```

---

## 🛑 Arrêter la stack

```bash
docker-compose down

# Avec suppression des volumes (données)
docker-compose down -v
```

---

## 💡 Tips

1. **Prometheus met du temps à scraper**: Par défaut toutes les 10 secondes
2. **Grafana cache les requêtes**: Rafraîchir la page (Ctrl+Shift+R)
3. **Volume de données**: Prometheus stocke 30 jours de données
4. **Performance**: Pour plus de prédictions, augmentez `num_requests` dans `test_monitoring.py`

---

## 📚 Documentation détaillée

Voir [MONITORING_SETUP.md](./MONITORING_SETUP.md) pour:
- Architecture détaillée
- Configuration avancée
- Écriture de règles d'alerte
- Troubleshooting
- Ressources externes

---

## ✅ Checklist finale

- [ ] Docker Compose lancé
- [ ] 3 services running (`docker-compose ps`)
- [ ] API répond (`http://localhost:8000/api/health`)
- [ ] Prometheus scrape (`http://localhost:9090/targets`)
- [ ] Dashboard visible (`http://localhost:3000`)
- [ ] Tests passent (`python test_monitoring.py`)
- [ ] Métriques apparaissent dans Grafana (attendre 10-15s)

---

## 🎓 Architecture

```
┌─────────────────────────────────────────────────────┐
│              Docker Compose Network                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   FastAPI    │  │  Prometheus  │  │  Grafana  │ │
│  │   (8000)     │  │   (9090)     │  │  (3000)   │ │
│  │              │  │              │  │           │ │
│  │ • /metrics   │  │ • Time DB    │  │ • Dash    │ │
│  │ • /predict   │  │ • Scrape     │  │ • Query   │ │
│  │ • /docs      │  │ • Collect    │  │ • Alert   │ │
│  │              │  │              │  │           │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│         ▲                 ▲                 ▲        │
│         │ expose metrics  │ scrape metrics  │ read   │
│         └─────────────────┴─────────────────┘        │
│                                                     │
│  Volumes:                                           │
│  • prometheus-data: Time series database            │
│  • grafana-data: Dashboards & configs               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🤝 Support

Pour des questions ou problèmes:
1. Vérifier [MONITORING_SETUP.md](./MONITORING_SETUP.md)
2. Consulter les logs: `docker-compose logs`
3. Vérifier les targets Prometheus
4. Réinitialiser: `docker-compose down -v && docker-compose up -d`

---

**Version**: 1.0  
**Date**: 2025-12-13  
**Status**: ✅ Production Ready
