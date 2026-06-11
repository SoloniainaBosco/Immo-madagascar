# Immo Madagascar

Moteur de recherche immobilier en langage naturel pour Madagascar.

---

## Description

Immo Madagascar permet de rechercher des biens immobiliers à Madagascar en utilisant des phrases en français courant.

Exemple : `"villa avec piscine à Nosy Be moins de 300 millions"`

Le système analyse la phrase, extrait les critères (type de bien, ville, budget, équipements) et interroge une base de 20 000 annonces indexées dans Elasticsearch. Les résultats sont affichés sur une carte interactive.

---

## Fonctionnalités

- Recherche en langage naturel français
- Extraction automatique des critères (type, ville, prix, surface, équipements)
- Carte interactive Leaflet avec marqueurs colorés par type de bien
- Recherche géospatiale via Elasticsearch (geo_point)
- Pipeline NLP from scratch (NumPy, Pandas)
- Dashboard Kibana pour visualisation des données
- API REST documentée avec Swagger

---

## Stack technique

| Technologie | Usage |
|-------------|-------|
| Python 3.12 | Langage principal |
| FastAPI | API REST |
| Elasticsearch | Indexation et recherche géospatiale |
| Kibana | Visualisation des données |
| Docker Compose | Infrastructure |
| NumPy | Vectorisation et similarité cosinus |
| Pandas | Extraction d'entités |
| Leaflet.js | Carte interactive |
| HTML / CSS / JS | Interface web |

---


---

## Installation

### Prérequis

- Docker et Docker Compose
- Python 3.12 ou supérieur
- Git

### Lancement

```bash
git clone https://github.com/SoloniainaBosco/immo-madagascar.git
cd immo-madagascar

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

docker compose up -d

PYTHONPATH=. python3 src/dataset_generator.py
PYTHONPATH=. python3 src/indexer.py
PYTHONPATH=. python3 src/nlp_parser.py
PYTHONPATH=. python3 src/app.py

### Accès
Service	URL
Interface web	http://localhost:5000
Documentation API	http://localhost:5000/docs
Kibana	http://localhost:5601
Élastique Recherche	http://localhost:9200

