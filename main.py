from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
import numpy as np
import os
from datetime import datetime
import logging
import joblib
import pickle
import warnings
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator

# Ignorer les warnings de compatibilité
warnings.filterwarnings('ignore')

# ==================== CONFIGURATION ====================
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Chemin vers le modèle dans Docker - essayer plusieurs emplacements
MODEL_PATHS = [
    "/app/model/model.pkl",
    "/app/model",  # Dossier complet pour MLflow
    "/app/mlruns",  # Fallback vers mlruns
]

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FASTAPI APP ====================
app = FastAPI(
    title="Credit Score ML API",
    description="API de production pour prédiction de crédit avec MLflow",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS pour permettre les requêtes depuis un frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PROMETHEUS METRICS ====================
# Métriques personnalisées
prediction_counter = Counter(
    'credit_predictions_total',
    'Nombre total de prédictions',
    ['prediction_type', 'status']
)

prediction_good_credit = Counter(
    'credit_predictions_good_total',
    'Nombre de prédictions: BON crédit'
)

prediction_bad_credit = Counter(
    'credit_predictions_bad_total',
    'Nombre de prédictions: MAUVAIS crédit'
)

prediction_latency = Histogram(
    'credit_prediction_duration_seconds',
    'Latence des prédictions en secondes',
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

model_load_counter = Counter(
    'model_load_attempts_total',
    'Nombre total de tentatives de chargement du modèle',
    ['status']
)

active_models = Gauge(
    'active_models_total',
    'Nombre de modèles actuellement chargés'
)

api_request_errors = Counter(
    'api_request_errors_total',
    'Nombre d\'erreurs API',
    ['endpoint', 'error_type']
)

# Instrumenter FastAPI avec prometheus-fastapi-instrumentator
Instrumentator().instrument(app).expose(app)


# ==================== MODELS PYDANTIC ====================
class CreditApplicationInput(BaseModel):
    """
    Format d'entrée pour une demande de crédit individuelle.
    Les données sont au format ORIGINAL (non prétraitées).
    """
    duration_in_month: int = Field(..., alias="Duration in month", ge=1, le=120)
    credit_amount: float = Field(..., alias="Credit amount", gt=0)
    installment_rate: int = Field(
        ..., 
        alias="Installment rate in percentage of disposable income",
        ge=1, le=4
    )
    age_in_years: int = Field(..., alias="Age in years", ge=18, le=100)
    num_existing_credits: int = Field(
        ..., 
        alias="Number of existing credits at this bank",
        ge=1, le=4
    )
    num_dependents: int = Field(
        ..., 
        alias="Number of people being liable to provide maintenance for",
        ge=1, le=2
    )
    
    # Catégorielles ordinales (codes A11, A12, etc.)
    status_checking_account: str = Field(
        ..., 
        alias="Status of existing checking account"
    )
    credit_history: str = Field(..., alias="Credit history")
    savings_account: str = Field(..., alias="Savings account/bonds")
    employment_since: str = Field(..., alias="Present employment since")
    job: str = Field(..., alias="Job")
    
    # Catégorielles nominales
    purpose: str = Field(..., alias="Purpose")
    personal_status_sex: str = Field(..., alias="Personal status and sex")
    other_debtors: str = Field(..., alias="Other debtors / guarantors")
    property: str = Field(..., alias="Property")
    other_installment_plans: str = Field(..., alias="Other installment plans")
    housing: str = Field(..., alias="Housing")
    telephone: str = Field(..., alias="Telephone")
    foreign_worker: str = Field(..., alias="foreign worker")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
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
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convertit l'input en DataFrame avec les noms de colonnes originaux"""
        data = {
            "Duration in month": self.duration_in_month,
            "Credit amount": self.credit_amount,
            "Installment rate in percentage of disposable income": self.installment_rate,
            "Age in years": self.age_in_years,
            "Number of existing credits at this bank": self.num_existing_credits,
            "Number of people being liable to provide maintenance for": self.num_dependents,
            "Status of existing checking account": self.status_checking_account,
            "Credit history": self.credit_history,
            "Savings account/bonds": self.savings_account,
            "Present employment since": self.employment_since,
            "Job": self.job,
            "Purpose": self.purpose,
            "Personal status and sex": self.personal_status_sex,
            "Other debtors / guarantors": self.other_debtors,
            "Property": self.property,
            "Other installment plans": self.other_installment_plans,
            "Housing": self.housing,
            "Telephone": self.telephone,
            "foreign worker": self.foreign_worker
        }
        return pd.DataFrame([data])


class PredictionResponse(BaseModel):
    """Réponse pour une prédiction individuelle"""
    prediction: int = Field(..., description="0=Mauvais crédit, 1=Bon crédit")
    probability_good_credit: float = Field(..., description="Probabilité de bon crédit (0-1)")
    probability_bad_credit: float = Field(..., description="Probabilité de mauvais crédit (0-1)")
    risk_level: str = Field(..., description="Niveau de risque: LOW, MEDIUM, HIGH")
    model_version: str
    timestamp: str
    
    
class BatchPredictionRequest(BaseModel):
    """Requête pour prédictions batch"""
    applications: List[CreditApplicationInput]
    

class BatchPredictionResponse(BaseModel):
    """Réponse pour prédictions batch"""
    predictions: List[PredictionResponse]
    total_processed: int
    model_version: str
    timestamp: str


class ModelInfo(BaseModel):
    """Informations sur un modèle"""
    name: str
    version: Optional[str]
    stage: Optional[str]
    description: Optional[str]


class HealthResponse(BaseModel):
    """Réponse du health check"""
    status: str
    model_path: str
    model_loaded: bool
    timestamp: str


# ==================== CACHE DU MODÈLE ====================
class ModelCache:
    """Cache simple pour éviter de recharger le modèle à chaque requête"""
    def __init__(self):
        self.model = None
        self.model_path = None
        self.model_version = "local-docker"
        self.load_method = None
        
    def find_model_file(self):
        """Trouve le fichier modèle dans différents emplacements"""
        for path in MODEL_PATHS:
            if os.path.exists(path):
                if os.path.isfile(path):
                    logger.info(f"✅ Fichier modèle trouvé: {path}")
                    return path
                elif os.path.isdir(path):
                    # Chercher model.pkl dans le dossier
                    pkl_path = os.path.join(path, "model.pkl")
                    if os.path.exists(pkl_path):
                        logger.info(f"✅ Fichier modèle trouvé: {pkl_path}")
                        return pkl_path
                    # Chercher un dossier MLflow model
                    mlmodel_path = os.path.join(path, "MLmodel")
                    if os.path.exists(mlmodel_path):
                        logger.info(f"✅ Dossier MLflow model trouvé: {path}")
                        return path
                    # Lister le contenu
                    contents = os.listdir(path)
                    logger.info(f"📁 Contenu de {path}: {contents}")
        
        raise FileNotFoundError(f"Aucun modèle trouvé dans: {MODEL_PATHS}")
        
    def load_model_from_file(self):
        """Charge le modèle depuis un fichier pickle local avec gestion des erreurs améliorée"""
        try:
            model_path = self.find_model_file()
            
            # Recharger seulement si changement de path
            if model_path != self.model_path:
                logger.info(f"📂 Chargement du modèle depuis: {model_path}")
                
                loaded = False
                errors = []
                
                # Méthode 1: MLflow (pour dossiers avec MLmodel)
                if os.path.isdir(model_path) or (os.path.isdir(os.path.dirname(model_path)) and 
                    os.path.exists(os.path.join(os.path.dirname(model_path), "MLmodel"))):
                    try:
                        load_path = model_path if os.path.isdir(model_path) else os.path.dirname(model_path)
                        logger.info(f"🔄 Tentative MLflow depuis: {load_path}")
                        self.model = mlflow.sklearn.load_model(load_path)
                        self.load_method = "mlflow"
                        loaded = True
                        logger.info("✅ Modèle chargé via mlflow.sklearn.load_model")
                    except Exception as e1:
                        errors.append(f"MLflow: {str(e1)}")
                        logger.warning(f"⚠️ Échec MLflow: {e1}")
                
                # Méthode 2: joblib avec gestion d'erreur spéciale
                if not loaded and os.path.isfile(model_path):
                    try:
                        logger.info(f"🔄 Tentative joblib depuis: {model_path}")
                        # Utiliser mmap_mode=None pour éviter les problèmes de compatibilité
                        import sklearn
                        logger.info(f"Version sklearn: {sklearn.__version__}")
                        self.model = joblib.load(model_path)
                        self.load_method = "joblib"
                        loaded = True
                        logger.info("✅ Modèle chargé via joblib")
                    except Exception as e2:
                        errors.append(f"Joblib: {str(e2)}")
                        logger.warning(f"⚠️ Échec joblib: {e2}")
                
                # Méthode 3: pickle standard
                if not loaded and os.path.isfile(model_path):
                    try:
                        logger.info(f"🔄 Tentative pickle depuis: {model_path}")
                        with open(model_path, 'rb') as f:
                            self.model = pickle.load(f)
                        self.load_method = "pickle"
                        loaded = True
                        logger.info("✅ Modèle chargé via pickle")
                    except Exception as e3:
                        errors.append(f"Pickle: {str(e3)}")
                        logger.warning(f"⚠️ Échec pickle: {e3}")
                
                if not loaded:
                    raise Exception(f"Toutes les méthodes ont échoué: {' | '.join(errors)}")
                
                self.model_path = model_path
                logger.info(f"✅ Modèle chargé avec succès")
                logger.info(f"   Type: {type(self.model)}")
                logger.info(f"   Méthode: {self.load_method}")
                
                # Tester le modèle avec des données factices
                try:
                    self._test_model()
                except Exception as test_error:
                    logger.error(f"❌ Le modèle ne fonctionne pas correctement: {test_error}")
                    raise
            
            return self.model
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Impossible de charger le modèle: {str(e)}"
            )
    
    def _test_model(self):
        """Teste le modèle avec des données factices"""
        try:
            logger.info("🧪 Test du modèle avec des données factices...")
            test_data = {
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
            df_test = pd.DataFrame([test_data])
            
            # Test predict
            pred = self.model.predict(df_test)
            logger.info(f"   Test predict: {pred}")
            
            # Test predict_proba
            proba = self.model.predict_proba(df_test)
            logger.info(f"   Test predict_proba: {proba}")
            
            logger.info("✅ Test du modèle réussi!")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test: {e}")
            raise
    
    def get_model(self):
        """Récupère le modèle (depuis cache ou charge)"""
        if self.model is None:
            self.load_model_from_file()
        return self.model, self.model_version


# Instance globale du cache
model_cache = ModelCache()


# ==================== FONCTIONS UTILITAIRES ====================
def calculate_risk_level(probability: float) -> str:
    """Détermine le niveau de risque basé sur la probabilité"""
    if probability >= 0.7:
        return "LOW"
    elif probability >= 0.4:
        return "MEDIUM"
    else:
        return "HIGH"


def make_prediction(model, df: pd.DataFrame) -> Dict[str, Any]:
    """Fait une prédiction et retourne les résultats formatés"""
    start_time = time.time()
    try:
        logger.info(f"🔮 Début de la prédiction...")
        logger.info(f"   Type modèle: {type(model)}")
        logger.info(f"   Shape DataFrame: {df.shape}")
        logger.info(f"   Colonnes: {df.columns.tolist()}")
        
        # Prédiction
        logger.info("   Appel model.predict()...")
        prediction = model.predict(df)[0]
        logger.info(f"   ✅ Prédiction: {prediction}")
        
        logger.info("   Appel model.predict_proba()...")
        probabilities = model.predict_proba(df)[0]
        logger.info(f"   ✅ Probabilités: {probabilities}")
        
        # Proba classe 1 (bon crédit)
        prob_good = float(probabilities[1])
        prob_bad = float(probabilities[0])
        
        result = {
            "prediction": int(prediction),
            "probability_good_credit": prob_good,
            "probability_bad_credit": prob_bad,
            "risk_level": calculate_risk_level(prob_good)
        }
        
        # Incrémenter les métriques Prometheus
        prediction_counter.labels(
            prediction_type='single',
            status='success'
        ).inc()
        
        if int(prediction) == 1:
            prediction_good_credit.inc()
        else:
            prediction_bad_credit.inc()
        
        # Enregistrer la latence
        duration = time.time() - start_time
        prediction_latency.observe(duration)
        
        logger.info(f"✅ Résultat final: {result}")
        return result
        
    except Exception as e:
        prediction_counter.labels(
            prediction_type='single',
            status='error'
        ).inc()
        api_request_errors.labels(
            endpoint='predict',
            error_type=type(e).__name__
        ).inc()
        
        duration = time.time() - start_time
        prediction_latency.observe(duration)
        
        logger.error(f"❌ Erreur lors de la prédiction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la prédiction: {str(e)}"
        )


# ==================== ENDPOINTS ====================

@app.get("/", tags=["Home"])
async def root():
    """Page d'accueil"""
    if os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    return JSONResponse({
        "message": "Credit Score ML API",
        "version": "2.0.0",
        "deployment": "Docker",
        "endpoints": {
            "health": "/api/health",
            "docs": "/docs",
            "predict": "/api/predict",
            "predict_batch": "/api/predict-batch",
            "model_info": "/api/model-info"
        }
    })


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Vérifie l'état de santé de l'API"""
    try:
        model, version = model_cache.get_model()
        model_loaded = model is not None
    except Exception:
        model_loaded = False
        
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_path=str(model_cache.model_path) if model_cache.model_path else "N/A",
        model_loaded=model_loaded,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/model-info", tags=["Models"])
async def get_model_info():
    """Récupère les informations du modèle chargé"""
    try:
        model, version = model_cache.get_model()
        
        return {
            "model_version": version,
            "model_path": str(model_cache.model_path),
            "model_type": str(type(model)),
            "load_method": model_cache.load_method,
            "model_loaded": model is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict_credit(application: CreditApplicationInput):
    """
    Prédit le risque de crédit pour une demande individuelle.
    
    Retourne:
    - prediction: 0 (mauvais crédit) ou 1 (bon crédit)
    - probability_good_credit: probabilité d'être un bon crédit
    - risk_level: LOW, MEDIUM, ou HIGH
    """
    try:
        # Charger le modèle
        model, version = model_cache.get_model()
        
        # Convertir en DataFrame
        df = application.to_dataframe()
        
        logger.info(f"📥 Nouvelle requête de prédiction")
        logger.info(f"   Données: {df.iloc[0].to_dict()}")
        
        # Faire la prédiction
        result = make_prediction(model, df)
        
        # Créer la réponse
        response = PredictionResponse(
            **result,
            model_version=str(version),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"📤 Résultat: {result['prediction']} (proba: {result['probability_good_credit']:.3f})")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la prédiction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la prédiction: {str(e)}"
        )


@app.post("/api/predict-batch", response_model=BatchPredictionResponse, tags=["Predictions"])
async def predict_batch(request: BatchPredictionRequest):
    """
    Prédit le risque de crédit pour plusieurs demandes en batch.
    
    Accepte une liste de demandes de crédit et retourne les prédictions
    pour chacune.
    """
    try:
        # Charger le modèle
        model, version = model_cache.get_model()
        
        # Convertir toutes les applications en DataFrame
        dfs = [app.to_dataframe() for app in request.applications]
        df_batch = pd.concat(dfs, ignore_index=True)
        
        logger.info(f"📥 Prédiction batch pour {len(request.applications)} demandes")
        
        # Faire les prédictions
        predictions_list = []
        for i, row in df_batch.iterrows():
            df_single = pd.DataFrame([row])
            result = make_prediction(model, df_single)
            
            predictions_list.append(
                PredictionResponse(
                    **result,
                    model_version=version,
                    timestamp=datetime.now().isoformat()
                )
            )
        
        response = BatchPredictionResponse(
            predictions=predictions_list,
            total_processed=len(predictions_list),
            model_version=str(version),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Batch terminé: {len(predictions_list)} prédictions")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du batch: {str(e)}"
        )


@app.post("/api/reload-model", tags=["Admin"])
async def reload_model():
    """Force le rechargement du modèle depuis le disque"""
    try:
        model_cache.model = None
        model_cache.model_path = None
        
        model, version = model_cache.get_model()
        
        return {
            "message": "Modèle rechargé avec succès",
            "model_path": str(model_cache.model_path),
            "version": version,
            "load_method": model_cache.load_method,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du rechargement: {str(e)}"
        )


# ==================== GESTION DES ERREURS ====================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestion globale des erreurs"""
    logger.error(f"❌ Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Une erreur interne est survenue",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ==================== STARTUP ====================
@app.on_event("startup")
async def startup_event():
    """Actions au démarrage de l'API"""
    logger.info("="*60)
    logger.info("🚀 DÉMARRAGE DE L'API CREDIT SCORE ML (DOCKER)")
    logger.info("="*60)
    
    # Lister tous les chemins possibles
    logger.info("📂 Chemins de recherche du modèle:")
    for path in MODEL_PATHS:
        exists = "✅" if os.path.exists(path) else "❌"
        logger.info(f"   {exists} {path}")
    
    # Lister le contenu de /app
    if os.path.exists("/app"):
        logger.info("\n📁 Contenu de /app:")
        for item in os.listdir("/app"):
            item_path = os.path.join("/app", item)
            if os.path.isdir(item_path):
                logger.info(f"   📂 {item}/")
                # Lister aussi le contenu des sous-dossiers
                try:
                    sub_items = os.listdir(item_path)
                    for sub_item in sub_items[:5]:  # Limiter à 5 items
                        logger.info(f"      - {sub_item}")
                    if len(sub_items) > 5:
                        logger.info(f"      ... et {len(sub_items)-5} autres")
                except:
                    pass
            else:
                logger.info(f"   📄 {item}")
    
    logger.info("\n🔄 Tentative de chargement du modèle...")
    try:
        # Précharger le modèle
        model, version = model_cache.get_model()
        logger.info(f"✅ Modèle préchargé avec succès!")
        logger.info(f"   Version: {version}")
        logger.info(f"   Méthode: {model_cache.load_method}")
        logger.info(f"   Chemin: {model_cache.model_path}")
    except Exception as e:
        logger.error(f"❌ Impossible de précharger le modèle: {e}")
        logger.warning("⚠️ L'API démarrera sans modèle - il sera chargé à la première requête")
    
    logger.info("="*60)


# ==================== LANCEMENT ====================
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 DÉMARRAGE DE L'API CREDIT SCORE ML (DOCKER)")
    print("="*60)
    print(f"📍 URL: http://localhost:8000")
    print(f"📚 Documentation: http://localhost:8000/docs")
    print(f"📂 Model Paths: {MODEL_PATHS}")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )