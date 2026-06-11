Immo Madagascar

Moteur de recherche immobilier en langage naturel pour Madagascar.

---

 Description

Immo Madagascar permet de rechercher des biens immobiliers à Madagascar en utilisant des phrases en français courant.

Exemple : `"villa avec piscine à Nosy Be moins de 300 millions"`

Le système analyse la phrase, extrait les critères (type de bien, ville, budget, équipements) et interroge une base de 20 000 annonces indexées dans Elasticsearch. Les résultats sont affichés sur une carte interactive.

---

Fonctionnalités

- Recherche en langage naturel français
- Extraction automatique des critères (type, ville, prix, surface, équipements)
- Carte interactive Leaflet avec marqueurs colorés par type de bien
- Recherche géospatiale via Elasticsearch (geo_point)
- Pipeline NLP from scratch (NumPy, Pandas)
- Dashboard Kibana pour visualisation des données
- API REST documentée avec Swagger



## Stack technique

 Technologie  Usage
 Python 3.12 | Langage principal |
 FastAPI | API REST |
 Elasticsearch | Indexation et recherche géospatiale |
 Kibana | Visualisation des données |
 Docker Compose | Infrastructure |
 NumPy | Vectorisation et similarité cosinus |
 Pandas | Extraction d'entités |
 Leaflet.js | Carte interactive |
 HTML / CSS / JS | Interface web |

---

## Structure du projet
