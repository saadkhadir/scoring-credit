#!/usr/bin/env python3
"""
Script de test pour générer des métriques Prometheus
Effectue des appels API pour vérifier le monitoring
"""

import requests
import time
import json
import random
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
METRICS_URL = f"{API_BASE_URL}/metrics"

# Exemple de données de crédit
SAMPLE_CREDIT_APPLICATIONS = [
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
    },
    {
        "Duration in month": 24,
        "Credit amount": 10000.0,
        "Installment rate in percentage of disposable income": 3,
        "Age in years": 45,
        "Number of existing credits at this bank": 2,
        "Number of people being liable to provide maintenance for": 1,
        "Status of existing checking account": "A14",
        "Credit history": "A34",
        "Savings account/bonds": "A65",
        "Present employment since": "A75",
        "Job": "A174",
        "Purpose": "A40",
        "Personal status and sex": "A91",
        "Other debtors / guarantors": "A101",
        "Property": "A122",
        "Other installment plans": "A142",
        "Housing": "A151",
        "Telephone": "A191",
        "foreign worker": "A201"
    },
    {
        "Duration in month": 6,
        "Credit amount": 2000.0,
        "Installment rate in percentage of disposable income": 1,
        "Age in years": 25,
        "Number of existing credits at this bank": 1,
        "Number of people being liable to provide maintenance for": 1,
        "Status of existing checking account": "A11",
        "Credit history": "A31",
        "Savings account/bonds": "A63",
        "Present employment since": "A72",
        "Job": "A172",
        "Purpose": "A44",
        "Personal status and sex": "A94",
        "Other debtors / guarantors": "A102",
        "Property": "A123",
        "Other installment plans": "A144",
        "Housing": "A153",
        "Telephone": "A193",
        "foreign worker": "A202"
    }
]


def check_api_health() -> bool:
    """Vérifie la santé de l'API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Health: OK")
            print(f"   {response.json()}")
            return True
        else:
            print(f"❌ API Health: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health Error: {e}")
        return False


def test_single_prediction(application: Dict[str, Any]) -> bool:
    """Teste une prédiction simple"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/predict",
            json=application,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            prediction = result.get('prediction')
            prob_good = result.get('probability_good_credit')
            risk = result.get('risk_level')
            
            status = "✅"
            symbol = "✅" if prediction == 1 else "❌"
            
            print(f"{status} Prédiction: {symbol} | "
                  f"P(Good)={prob_good:.2%} | Risk={risk}")
            return True
        else:
            print(f"❌ Prédiction échouée: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur prédiction: {e}")
        return False


def test_batch_predictions() -> bool:
    """Teste les prédictions en batch"""
    try:
        payload = {
            "applications": SAMPLE_CREDIT_APPLICATIONS
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/predict-batch",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            total = result.get('total_processed', 0)
            print(f"✅ Batch Predictions: {total} prédictions traitées")
            return True
        else:
            print(f"❌ Batch échoué: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur batch: {e}")
        return False


def get_metrics() -> bool:
    """Récupère les métriques Prometheus"""
    try:
        response = requests.get(METRICS_URL, timeout=5)
        
        if response.status_code == 200:
            lines = response.text.split('\n')
            
            # Filtrer les métriques intéressantes
            metrics_of_interest = [
                'credit_predictions_total',
                'credit_predictions_good_total',
                'credit_predictions_bad_total',
                'credit_prediction_duration_seconds_bucket',
                'http_requests_total',
                'http_request_duration_seconds'
            ]
            
            print("\n📊 Métriques Prometheus:")
            print("-" * 60)
            
            found_metrics = False
            for line in lines:
                if any(metric in line for metric in metrics_of_interest):
                    if not line.startswith('#'):
                        print(f"   {line}")
                        found_metrics = True
            
            if found_metrics:
                print("-" * 60)
                return True
            else:
                print("   ⚠️ Aucune métrique personnalisée trouvée")
                return False
                
    except Exception as e:
        print(f"❌ Erreur métriques: {e}")
        return False


def run_load_test(num_requests: int = 10, delay: float = 0.5):
    """Teste avec plusieurs requêtes"""
    print(f"\n🔄 Exécution de {num_requests} requêtes de test...")
    print("-" * 60)
    
    successful = 0
    failed = 0
    
    for i in range(num_requests):
        print(f"\n[{i+1}/{num_requests}] Test #{ + i}")
        
        app = random.choice(SAMPLE_CREDIT_APPLICATIONS)
        
        if test_single_prediction(app):
            successful += 1
        else:
            failed += 1
        
        if i < num_requests - 1:
            time.sleep(delay)
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {successful} succès, {failed} échecs")
    print("=" * 60)
    
    return successful, failed


def main():
    print("\n" + "=" * 60)
    print("🚀 SCRIPT DE TEST - MONITORING PROMETHEUS")
    print("=" * 60)
    
    print("\n1️⃣  Vérification de la santé de l'API...")
    print("-" * 60)
    
    if not check_api_health():
        print("❌ L'API n'est pas disponible!")
        print("   Assurez-vous que: docker-compose up -d")
        return
    
    print("\n2️⃣  Test de prédictions simples...")
    print("-" * 60)
    
    # Test quelques prédictions
    for i, app in enumerate(SAMPLE_CREDIT_APPLICATIONS[:2]):
        print(f"\nTest {i+1}:")
        test_single_prediction(app)
    
    print("\n3️⃣  Test de prédictions en batch...")
    print("-" * 60)
    test_batch_predictions()
    
    print("\n4️⃣  Test de charge (génération de métriques)...")
    print("-" * 60)
    successful, failed = run_load_test(num_requests=5, delay=1.0)
    
    print("\n5️⃣  Récupération des métriques Prometheus...")
    print("-" * 60)
    get_metrics()
    
    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS")
    print("=" * 60)
    print("\n📊 Accédez aux dashboards:")
    print("   - Prometheus: http://localhost:9090")
    print("   - Grafana:    http://localhost:3000")
    print("   - API:        http://localhost:8000/docs")
    print("\n💡 Conseil: Attendez 10-15 secondes pour que Prometheus scrape les métriques")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
