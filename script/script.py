import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
from mlflow.tracking import MlflowClient
import joblib
import json


# ==================== CONFIGURATION DES FEATURES ====================
numerical_features = [
    'Duration in month',
    'Credit amount',
    'Installment rate in percentage of disposable income',
    'Age in years',
    'Number of existing credits at this bank',
    'Number of people being liable to provide maintenance for'
]

ordinal_categorical_features = [
    'Status of existing checking account',
    'Credit history',
    'Savings account/bonds',
    'Present employment since',
    'Job'
]

nominal_categorical_features = [
    'Purpose',
    'Personal status and sex',
    'Other debtors / guarantors',
    'Property',
    'Other installment plans',
    'Housing',
    'Telephone',
    'foreign worker'
]

# ==================== MAPPINGS (ORDINAL) ====================
status_mapping = {
    'A11': 0,  # ... < 0 DM
    'A12': 1,  # 0 <= ... < 200 DM
    'A13': 2,  # ... >= 200 DM / salary assignments for at least 1 year
    'A14': 3   # no checking account
}

credit_history_mapping = {
    'A30': 0,  # no credits taken/ all credits paid back duly
    'A31': 1,  # all credits at this bank paid back duly
    'A32': 2,  # existing credits paid back duly till now
    'A33': 3,  # delay in paying off in the past
    'A34': 4   # critical account/ other credits existing (not at this bank)
}

savings_mapping = {
    'A61': 0,  # ... < 100 DM
    'A62': 1,  # 100 <= ... < 500 DM
    'A63': 2,  # 500 <= ... < 1000 DM
    'A64': 3,  # ... >= 1000 DM
    'A65': 4   # unknown/ no savings account
}

employment_mapping = {
    'A71': 0,  # unemployed
    'A72': 1,  # ... < 1 year
    'A73': 2,  # 1 <= ... < 4 years
    'A74': 3,  # 4 <= ... < 7 years
    'A75': 4   # .. >= 7 years
}

job_mapping = {
    'A171': 0, # unemployed/ unskilled - non-resident
    'A172': 1, # unskilled - resident
    'A173': 2, # skilled employee / official
    'A174': 3  # management/ self-employed/ highly qualified employee/ officer
}

# Dictionnaire global des mappings
ALL_MAPPINGS = {
    'Status of existing checking account': status_mapping,
    'Credit history': credit_history_mapping,
    'Savings account/bonds': savings_mapping,
    'Present employment since': employment_mapping,
    'Job': job_mapping
}


# ==================== FONCTIONS DE PREPROCESSING ====================
def apply_ordinal_mappings(df):
    """Applique les mappings ordinaux aux colonnes catégorielles"""
    df = df.copy()
    for col, mapping in ALL_MAPPINGS.items():
        if col in df.columns:
            df[col] = df[col].map(mapping)
            # Gérer les valeurs manquantes ou inconnues
            if df[col].isna().any():
                print(f"⚠️ Attention: valeurs inconnues dans '{col}', remplacement par -1")
                df[col] = df[col].fillna(-1)
    return df


def create_preprocessing_pipeline():
    """
    Crée un pipeline de preprocessing complet qui :
    1. Applique les mappings ordinaux
    2. Fait le one-hot encoding des variables nominales
    3. Scale les variables numériques
    """
    
    # Transformer pour les mappings ordinaux
    ordinal_transformer = FunctionTransformer(apply_ordinal_mappings)
    
    # Pipeline complet
    # Note: On ne peut pas utiliser ColumnTransformer directement pour le one-hot
    # car pd.get_dummies doit être appliqué sur tout le DataFrame
    # On va donc créer un transformer personnalisé
    
    return ordinal_transformer


class CustomPreprocessor:
    """Préprocesseur personnalisé pour gérer tout le pipeline"""
    
    def __init__(self, numerical_features, ordinal_features, nominal_features, mappings):
        self.numerical_features = numerical_features
        self.ordinal_features = ordinal_features
        self.nominal_features = nominal_features
        self.mappings = mappings
        self.scaler = StandardScaler()
        self.feature_names_ = None
        
    def fit(self, X, y=None):
        """Fit le scaler sur les données d'entraînement"""
        X_processed = self._apply_mappings_and_encoding(X)
        # Fit le scaler seulement sur les colonnes numériques
        num_cols = [col for col in X_processed.columns if col in self.numerical_features]
        if num_cols:
            self.scaler.fit(X_processed[num_cols])
        self.feature_names_ = list(X_processed.columns)
        return self
    
    def transform(self, X):
        """Transform les données"""
        X_processed = self._apply_mappings_and_encoding(X)
        
        # Scale les features numériques
        num_cols = [col for col in X_processed.columns if col in self.numerical_features]
        if num_cols:
            X_processed[num_cols] = self.scaler.transform(X_processed[num_cols])
        
        # S'assurer que les colonnes sont dans le bon ordre
        if self.feature_names_:
            # Ajouter les colonnes manquantes avec des 0
            for col in self.feature_names_:
                if col not in X_processed.columns:
                    X_processed[col] = 0
            X_processed = X_processed[self.feature_names_]
        
        return X_processed
    
    def fit_transform(self, X, y=None):
        """Fit et transform"""
        return self.fit(X, y).transform(X)
    
    def _apply_mappings_and_encoding(self, X):
        """Applique les mappings et le one-hot encoding"""
        X = X.copy()
        
        # 1. Appliquer les mappings ordinaux
        for col, mapping in self.mappings.items():
            if col in X.columns:
                X[col] = X[col].map(mapping)
                if X[col].isna().any():
                    X[col] = X[col].fillna(-1)
        
        # 2. One-hot encoding des variables nominales
        cols_to_encode = [col for col in self.nominal_features if col in X.columns]
        if cols_to_encode:
            X = pd.get_dummies(X, columns=cols_to_encode, drop_first=True)
        
        return X


# ==================== CHARGEMENT ET PRÉPARATION DES DONNÉES ====================
print("📊 Chargement des données...")
data = pd.read_csv('data/estadistical.csv')
data.columns = data.columns.str.strip()
data = data.rename(columns={'Receive/ Not receive credit': 'Credit_Risk'})

# Mapper la cible (2=mauvais crédit -> 0, 1=bon crédit -> 1)
data['Credit_Risk'] = data['Credit_Risk'].map({2: 0, 1: 1})

# Séparer X et y AVANT tout preprocessing
X = data.drop('Credit_Risk', axis=1)
y = data['Credit_Risk']

print(f"✅ Données chargées: {X.shape[0]} lignes, {X.shape[1]} colonnes")
print(f"   Distribution cible: {y.value_counts().to_dict()}")

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

print(f"📊 Split: Train={len(X_train)}, Test={len(X_test)}")


# ==================== CRÉATION DU PIPELINE COMPLET ====================
print("\n🔧 Création du pipeline de preprocessing + modèle...")

# Créer le preprocessor
preprocessor = CustomPreprocessor(
    numerical_features=numerical_features,
    ordinal_features=ordinal_categorical_features,
    nominal_features=nominal_categorical_features,
    mappings=ALL_MAPPINGS
)

# Pipeline complet
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42,
        n_jobs=-1
    ))
])

print("✅ Pipeline créé")


# ==================== ENTRAÎNEMENT ====================
print("\n🚀 Entraînement du modèle...")
pipeline.fit(X_train, y_train)
print("✅ Entraînement terminé")


# ==================== ÉVALUATION ====================
print("\n📈 Évaluation sur le test set...")
y_pred = pipeline.predict(X_test)
y_pred_proba = pipeline.predict_proba(X_test)

accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)

print(f"\n{'='*60}")
print(f"RÉSULTATS DU MODÈLE")
print(f"{'='*60}")
print(f"Accuracy: {accuracy:.4f}")
print(f"\nClassification Report:\n{report}")
print(f"\nConfusion Matrix:\n{conf_matrix}")
print(f"{'='*60}\n")


# ==================== MLFLOW LOGGING ====================
print("📝 Logging dans MLflow...")

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("credit-score-production")

with mlflow.start_run(run_name="rf-pipeline-v2") as run:
    
    # 1. Logger les métriques
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("test_samples", len(X_test))
    mlflow.log_metric("train_samples", len(X_train))
    
    # 2. Logger les hyperparamètres du modèle
    mlflow.log_params({
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 20,
        "min_samples_leaf": 10,
        "random_state": 42
    })
    
    # 3. Logger le rapport de classification
    mlflow.log_text(report, "classification_report.txt")
    mlflow.log_text(str(conf_matrix), "confusion_matrix.txt")
    
    # 4. Sauvegarder les métadonnées
    metadata = {
        "numerical_features": numerical_features,
        "ordinal_features": ordinal_categorical_features,
        "nominal_features": nominal_categorical_features,
        "mappings": {k: {str(k2): v2 for k2, v2 in v.items()} 
                     for k, v in ALL_MAPPINGS.items()},
        "final_feature_count": len(preprocessor.feature_names_),
        "final_features": preprocessor.feature_names_
    }
    
    mlflow.log_dict(metadata, "model_metadata.json")
    
    # 5. Créer la signature avec les colonnes ORIGINALES (avant preprocessing)
    # Ceci est crucial pour que l'API sache quelles colonnes accepter
    signature = infer_signature(X_train, pipeline.predict(X_train))
    
    # 6. Logger le pipeline complet
    mlflow.sklearn.log_model(
        sk_model=pipeline,
        artifact_path="model",
        registered_model_name="RDF_score_pipeline",
        signature=signature,
        input_example=X_train.iloc[:5]  # Exemple d'input
    )
    
    print(f"✅ Modèle enregistré dans MLflow")
    print(f"   Run ID: {run.info.run_id}")
    print(f"   Modèle: RDF_score_pipeline")
    print(f"   Features d'entrée: {list(X_train.columns)}")
    print(f"   Features après preprocessing: {len(preprocessor.feature_names_)}")


# ==================== PROMOTION EN PRODUCTION ====================
print("\n🎯 Promotion du modèle en Production...")

try:
    client = MlflowClient()
    
    # Récupérer la dernière version
    versions = client.search_model_versions("name='RDF_score_pipeline'")
    if versions:
        latest_version = max(versions, key=lambda v: int(v.version))
        version_number = latest_version.version
        
        # Transition vers Production
        client.transition_model_version_stage(
            name="RDF_score_pipeline",
            version=version_number,
            stage="Production",
            archive_existing_versions=True  # Archive les anciennes versions en Production
        )
        
        print(f"✅ Modèle version {version_number} promu en Production")
    else:
        print("⚠️ Aucune version trouvée pour promotion")
        
except Exception as e:
    print(f"⚠️ Erreur lors de la promotion: {e}")


# ==================== TEST DU MODÈLE CHARGÉ ====================
print("\n🧪 Test de chargement du modèle depuis MLflow...")

try:
    # Charger le modèle depuis le registry
    loaded_model = mlflow.sklearn.load_model("models:/RDF_score_pipeline/Production")
    
    # Tester sur un échantillon
    sample = X_test.iloc[:3]
    predictions = loaded_model.predict(sample)
    probas = loaded_model.predict_proba(sample)
    
    print("✅ Modèle chargé avec succès depuis MLflow")
    print(f"   Test sur {len(sample)} échantillons:")
    for i, (pred, proba) in enumerate(zip(predictions, probas)):
        print(f"   Sample {i+1}: Prédiction={pred}, Proba classe 1={proba[1]:.4f}")
    
except Exception as e:
    print(f"❌ Erreur lors du chargement: {e}")


print("\n" + "="*60)
print("✅ PROCESSUS TERMINÉ AVEC SUCCÈS")
print("="*60)
print(f"📊 Modèle: RDF_score_pipeline")
print(f"🎯 Stage: Production")
print(f"📈 Accuracy: {accuracy:.4f}")
print(f"🔗 MLflow UI: http://localhost:5000")
print("="*60)