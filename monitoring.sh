#!/bin/bash
# Quick Commands for Monitoring Stack

echo "📊 SCORE-CREDIT-PROJECT - MONITORING COMMANDS"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

case "${1:-help}" in
  
  # Démarrer la stack
  up)
    echo -e "${BLUE}🚀 Démarrage de la stack Docker...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ Stack lancée!${NC}"
    echo ""
    echo "Services disponibles en 30-60 secondes:"
    echo "  - API:        http://localhost:8000"
    echo "  - API Docs:   http://localhost:8000/docs"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana:    http://localhost:3000"
    ;;

  # Arrêter la stack
  down)
    echo -e "${BLUE}🛑 Arrêt de la stack Docker...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Stack arrêtée!${NC}"
    ;;

  # Arrêter avec suppression volumes
  clean)
    echo -e "${YELLOW}⚠️  Suppression de tous les volumes...${NC}"
    docker-compose down -v
    echo -e "${GREEN}✅ Nettoyage effectué!${NC}"
    ;;

  # Statut des services
  status|ps)
    echo -e "${BLUE}📊 Statut des services:${NC}"
    docker-compose ps
    ;;

  # Logs
  logs)
    echo -e "${BLUE}📝 Logs en temps réel (Ctrl+C pour quitter):${NC}"
    docker-compose logs -f
    ;;

  logs:api)
    docker-compose logs -f api
    ;;

  logs:prometheus)
    docker-compose logs -f prometheus
    ;;

  logs:grafana)
    docker-compose logs -f grafana
    ;;

  # Tests
  test)
    echo -e "${BLUE}🧪 Exécution des tests de monitoring...${NC}"
    python test_monitoring.py
    ;;

  # Vérifications santé
  health)
    echo -e "${BLUE}🏥 Vérification de santé:${NC}"
    echo ""
    
    echo -n "API Health: "
    curl -s http://localhost:8000/api/health > /dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}❌${NC}"
    
    echo -n "Prometheus Health: "
    curl -s http://localhost:9090/-/healthy > /dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}❌${NC}"
    
    echo -n "Grafana Health: "
    curl -s http://localhost:3000/api/health > /dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}❌${NC}"
    
    echo ""
    echo -n "Prometheus scrape API: "
    curl -s "http://localhost:9090/api/v1/targets" | grep -q "credit-score-api" && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}❌${NC}"
    ;;

  # Ouvrir les UIs
  open)
    echo -e "${BLUE}🌐 Ouverture des UIs...${NC}"
    echo ""
    echo "🔗 http://localhost:3000   (Grafana)"
    echo "🔗 http://localhost:9090   (Prometheus)"
    echo "🔗 http://localhost:8000/docs (API Docs)"
    echo ""
    echo "Credentials Grafana:"
    echo "  Username: admin"
    echo "  Password: admin123"
    
    # Essayer d'ouvrir dans le navigateur (si disponible)
    if command -v xdg-open > /dev/null; then
      xdg-open http://localhost:3000
    elif command -v open > /dev/null; then
      open http://localhost:3000
    elif command -v start > /dev/null; then
      start http://localhost:3000
    fi
    ;;

  # Voir les métriques
  metrics)
    echo -e "${BLUE}📊 Métriques disponibles:${NC}"
    echo ""
    curl -s http://localhost:8000/metrics | grep "^credit_" | head -20
    ;;

  # API status
  api:health)
    echo -e "${BLUE}API Status:${NC}"
    curl -s http://localhost:8000/api/health | jq .
    ;;

  # Example prediction
  api:predict)
    echo -e "${BLUE}📮 Exemple de prédiction:${NC}"
    curl -s -X POST http://localhost:8000/api/predict \
      -H "Content-Type: application/json" \
      -d '{
        "Duration in month": 12,
        "Credit amount": 5000,
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
      }' | jq .
    ;;

  # Restart service
  restart)
    if [ -z "$2" ]; then
      echo -e "${BLUE}🔄 Redémarrage de tous les services...${NC}"
      docker-compose restart
    else
      echo -e "${BLUE}🔄 Redémarrage de $2...${NC}"
      docker-compose restart "$2"
    fi
    echo -e "${GREEN}✅ Service redémarré!${NC}"
    ;;

  # Documentation
  docs)
    echo -e "${GREEN}📖 Documentation disponible:${NC}"
    echo ""
    echo "  1. MONITORING_README.md       - Guide rapide"
    echo "  2. MONITORING_SETUP.md        - Documentation détaillée"
    echo "  3. CHANGES_SUMMARY.md         - Résumé des modifications"
    echo "  4. main.py                    - Code instrumenté"
    echo "  5. prometheus.yml             - Config Prometheus"
    echo "  6. docker-compose.yml         - Stack Docker"
    ;;

  # Help
  help|*)
    echo -e "${GREEN}Usage:${NC} ./monitoring.sh [command]"
    echo ""
    echo -e "${BLUE}Stack Management:${NC}"
    echo "  up              Démarrer la stack"
    echo "  down            Arrêter la stack"
    echo "  clean           Arrêter et supprimer les volumes"
    echo "  status, ps      Afficher l'état des services"
    echo "  restart [svc]   Redémarrer un service"
    echo ""
    echo -e "${BLUE}Logs & Monitoring:${NC}"
    echo "  logs            Logs en temps réel (tous les services)"
    echo "  logs:api        Logs API seulement"
    echo "  logs:prometheus Logs Prometheus seulement"
    echo "  logs:grafana    Logs Grafana seulement"
    echo ""
    echo -e "${BLUE}Tests & Vérifications:${NC}"
    echo "  test            Exécuter test_monitoring.py"
    echo "  health          Vérifier la santé des services"
    echo "  metrics         Afficher les métriques Prometheus"
    echo "  api:health      Santé API détaillée"
    echo "  api:predict     Test de prédiction"
    echo ""
    echo -e "${BLUE}UIs & Accès:${NC}"
    echo "  open            Ouvrir les dashboards"
    echo "  docs            Afficher la documentation"
    echo ""
    echo -e "${BLUE}Exemples:${NC}"
    echo "  ./monitoring.sh up"
    echo "  ./monitoring.sh status"
    echo "  ./monitoring.sh logs:api"
    echo "  ./monitoring.sh test"
    echo "  ./monitoring.sh health"
    ;;

esac

echo ""
