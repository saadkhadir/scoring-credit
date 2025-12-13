# FastAPI MLflow Interface Web

Cette application FastAPI permet d'accéder à vos modèles MLflow depuis une interface web intuitive.

## 📋 Prérequis

- Python 3.8+
- FastAPI
- Uvicorn
- MLflow
- Pandas
- Scikit-learn

## 🚀 Installation et Démarrage

### 1. Installer les dépendances

```bash
# Activer l'environnement virtuel
.\venv\Scripts\activate

# Installer FastAPI et Uvicorn
pip install fastapi uvicorn
```

### 2. Démarrer l'application FastAPI

```bash
# Depuis le répertoire racine du projet
python main.py
```

L'application sera disponible à `http://localhost:8000`

## 📡 Endpoints API

### Health Check
```
GET /api/health
```
Vérifie l'état du serveur et la connexion à MLflow.

### Lister les Modèles
```
GET /api/models
```
Retourne tous les modèles enregistrés dans MLflow.

### Détails d'un Modèle
```
GET /api/models/{model_name}
```
Retourne les détails et versions d'un modèle spécifique.

### Prédiction Simple
```
POST /api/predict/{model_name}
Content-Type: application/json

{
  "data": [value1, value2, ...],
  "columns": ["col1", "col2", ...]
}
```

### Prédictions en Lot
```
POST /api/predict-batch/{model_name}
Content-Type: application/json

[
  {"data": [value1, value2, ...], "columns": ["col1", "col2", ...]},
  {"data": [value3, value4, ...], "columns": ["col1", "col2", ...]}
]
```

### Lister les Expériences
```
GET /api/experiments
```

### Lister les Runs d'une Expérience
```
GET /api/experiments/{exp_id}/runs
```

## 🌐 Interface Web

Accédez à `http://localhost:8000` dans votre navigateur.

L'interface permet de :
- ✅ Faire des prédictions uniques ou en lot
- 📦 Consulter les modèles disponibles
- 📊 Consulter les expériences MLflow
- 🔍 Voir les réponses en temps réel en JSON

## 📝 Exemple d'utilisation avec cURL

### Prédiction simple
```bash
curl -X POST "http://localhost:8000/api/predict/RDF_score" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [3, 0.25, 2, 0.94, 4, 1, -1.76, 1, 0.74, 1.02, 2, -0.42],
    "columns": ["Status of existing checking account", "Duration in month", "Credit history", "Credit amount", "Savings account/bonds", "Present employment since", "Installment rate in percentage of disposable income", "Present residence since", "Age in years", "Number of existing credits at this bank", "Job", "Number of people being liable to provide maintenance for"]
  }'
```

## 🔧 Configuration

Modifiez le fichier `main.py` pour :
- Changer l'URI de MLflow : `MLFLOW_TRACKING_URI`
- Changer le port : dans `uvicorn.run(app, host="0.0.0.0", port=8000)`
- Changer le host : modifiez `host="0.0.0.0"`

## 🔐 Sécurité

⚠️ Cette interface est pour le développement/test. Pour la production :
- Ajoutez l'authentification
- Activez HTTPS
- Limitez les CORS
- Validez les entrées utilisateur
- Utilisez des variables d'environnement pour les configurations sensibles

## 📄 Logs

Les logs sont affichés dans le terminal où l'application s'exécute.

## ❌ Troubleshooting

### Erreur "Modèle non trouvé"
- Vérifiez que le modèle existe dans MLflow
- Vérifiez le nom du modèle (sensible à la casse)

### Erreur "Production stage not found"
- Le modèle n'a pas un stage "Production"
- L'API utilisera automatiquement le stage "latest"

### Connexion MLflow refusée
- Assurez-vous que MLflow est en cours d'exécution
- Vérifiez l'URI de MLflow dans `main.py`

## 📚 Documentation Interactive

Accédez à la documentation Swagger :
```
http://localhost:8000/docs
```

Accédez à la documentation ReDoc :
```
http://localhost:8000/redoc
```
