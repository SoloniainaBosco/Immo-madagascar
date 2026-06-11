# =============================================================
# config/settings.py
# Configuration centrale du projet
# =============================================================

# Elasticsearch
ES_HOST       = "http://localhost:9200"
ES_INDEX      = "immo_madagascar"
ES_TIMEOUT    = 10

# Dataset
NB_BIENS      = 20000
DATA_DIR      = "data"
DATA_FILE     = "data/immo_madagascar.json"
DATA_CSV      = "data/immo_madagascar.csv"

# Flask
FLASK_HOST    = "0.0.0.0"
FLASK_PORT    = 5000
FLASK_DEBUG   = True

# Scraper
SCRAPER_DELAY_MIN = 2
SCRAPER_DELAY_MAX = 5

# Villes de Madagascar avec coordonnées GPS et prix au m² en Ariary
VILLES = {
    "Antananarivo": {
        "lat": -18.9137, "lon": 47.5361,
        "prix_m2": 1_500_000,
        "quartiers": [
            "Analakely", "Tsaralalana", "Ankorondrano", "Ambohijatovo",
            "Ivandry", "Ankadifotsy", "Mahamasina", "Andohatapenaka",
            "Ambatobe", "Tanjombato", "Andravoahangy", "Isotry",
            "Ampefiloha", "Faravohitra", "Isoraka", "Antanimena",
            "Ambohidahy", "Mandrosoa", "Talatamaty", "Androhibe"
        ]
    },
    "Toamasina": {
        "lat": -18.1443, "lon": 49.3958,
        "prix_m2": 700_000,
        "quartiers": [
            "Bazary Be", "Tanambao", "Morafeno", "Ampasimadinika",
            "Anjoma", "Ambohipo", "Logement", "Barikadimy"
        ]
    },
    "Mahajanga": {
        "lat": -15.7167, "lon": 46.3167,
        "prix_m2": 600_000,
        "quartiers": [
            "Mahabibo", "Tsaramandroso", "Amborovy", "Mangarivotra",
            "Marofarihy", "Abattoir", "Aranta", "Mangabe"
        ]
    },
    "Fianarantsoa": {
        "lat": -21.4531, "lon": 47.0833,
        "prix_m2": 500_000,
        "quartiers": [
            "Haute Ville", "Basse Ville", "Andrainjato",
            "Tsianolondroa", "Ambozontany", "Mahereza"
        ]
    },
    "Antsiranana": {
        "lat": -12.3530, "lon": 49.2960,
        "prix_m2": 550_000,
        "quartiers": [
            "Joffreville", "Ramena", "Centre Ville",
            "Antsikorotana", "Tanambao", "Scama"
        ]
    },
    "Toliara": {
        "lat": -23.3568, "lon": 43.6693,
        "prix_m2": 480_000,
        "quartiers": [
            "Mahavatse", "Betania", "Tsienimparihy",
            "Anketa", "Mitsinjo", "Sanfily"
        ]
    },
    "Nosy Be": {
        "lat": -13.3333, "lon": 48.2667,
        "prix_m2": 900_000,
        "quartiers": [
            "Hell-Ville", "Ambatoloaka", "Dzamandzar",
            "Madirokely", "Ambatozavavy"
        ]
    },
    "Antsirabe": {
        "lat": -19.8659, "lon": 47.0337,
        "prix_m2": 450_000,
        "quartiers": [
            "Ambohimena", "Andranomanalina", "Tsarahonenana",
            "Antsenakely", "Mandrosoa"
        ]
    },
}

# Types de biens
TYPES_BIENS = ["appartement", "maison", "villa", "studio", "terrain", "duplex"]

# États du bien
ETATS = ["neuf", "bon état", "à rénover"]

# Équipements possibles
EQUIPEMENTS = [
    "parking", "jardin", "terrasse", "clôture", "gardien",
    "puits", "groupe électrogène", "panneau solaire",
    "citerne eau", "portail", "piscine", "balcon",
    "cuisine équipée", "climatisation", "internet fibre"
]
