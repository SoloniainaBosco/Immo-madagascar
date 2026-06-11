
import os
import json
import time
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.settings import ES_HOST, ES_INDEX, ES_TIMEOUT, DATA_FILE


# ______________________________Mapping Elasticsearch______________________________

MAPPING = {
    "settings": {
        "number_of_shards":   1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "french_custom": {
                    "type":      "custom",
                    "tokenizer": "standard",
                    "filter":    ["lowercase", "asciifolding"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id":             {"type": "keyword"},
            "titre":          {"type": "text",    "analyzer": "french_custom"},
            "description":    {"type": "text",    "analyzer": "french_custom"},
            "type_bien":      {"type": "keyword"},
            "ville":          {"type": "keyword"},
            "quartier":       {"type": "keyword"},
            "surface":        {"type": "integer"},
            "nb_pieces":      {"type": "integer"},
            "prix_ariary":    {"type": "long"},
            "prix_m2_ariary": {"type": "long"},
            "etat":           {"type": "keyword"},
            "equipements":    {"type": "keyword"},
            "localisation":   {"type": "geo_point"},
            "date_annonce":   {"type": "date", "format": "yyyy-MM-dd"},
        }
    }
}


# ______________________________Fonctions de connexion______________________________

def attendre_elasticsearch(max_tentatives: int = 12) -> bool:
    """Attend qu'Elasticsearch soit prêt."""
    print("Connexion à Elasticsearch...")
    for tentative in range(1, max_tentatives + 1):
        try:
            reponse = requests.get(ES_HOST, timeout=ES_TIMEOUT)
            if reponse.status_code == 200:
                version = reponse.json()["version"]["number"]
                print(f"Elasticsearch connecté — version {version}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        print(f"  Tentative {tentative}/{max_tentatives} — attente 5 secondes...")
        time.sleep(5)
    print("Impossible de contacter Elasticsearch.")
    print("Vérifiez que Docker tourne : docker compose up -d")
    return False



# ______________________________Gestion de l'index______________________________

def supprimer_index() -> None:
    """Supprime l'index s'il existe déjà."""
    reponse = requests.delete(f"{ES_HOST}/{ES_INDEX}", timeout=ES_TIMEOUT)
    if reponse.status_code == 200:
        print(f"Index '{ES_INDEX}' supprimé.")
    elif reponse.status_code == 404:
        print(f"Index '{ES_INDEX}' inexistant — rien à supprimer.")


def creer_index() -> bool: # creer un nouvell index en envoyant le mapping complet via le requete PUT
    """Crée l'index avec le mapping geo_point."""
    reponse = requests.put(
        f"{ES_HOST}/{ES_INDEX}",
        json=MAPPING,
        headers={"Content-Type": "application/json"},
        timeout=ES_TIMEOUT
    )
    if reponse.status_code == 200:
        print(f"Index '{ES_INDEX}' créé avec mapping geo_point.")
        return True
    print(f"Erreur création index : {reponse.text}")
    return False


# ______________________________Indexation des documents______________________________

def indexer_biens(chemin_fichier: str) -> int:
    """
    Indexe tous les biens depuis le fichier JSON.

    Args:
        chemin_fichier: Chemin vers le fichier JSON

    Returns:
        Nombre de documents indexés avec succès
    """
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        biens = json.load(f)

    print(f"{len(biens)} biens chargés depuis {chemin_fichier}")
    print("Indexation en cours...")

    succes  = 0
    erreurs = 0

    for bien in biens:
        doc_id  = bien["id"]
        reponse = requests.put(
            f"{ES_HOST}/{ES_INDEX}/_doc/{doc_id}",
            json=bien,
            headers={"Content-Type": "application/json"},
            timeout=ES_TIMEOUT
        )
        if reponse.status_code in [200, 201]:
            succes += 1
        else:
            erreurs += 1
            print(f"  Erreur sur {doc_id} : {reponse.text[:80]}")

        if succes % 100 == 0 and succes > 0:
            print(f"  {succes}/{len(biens)} documents indexés...")

    print(f"Indexation terminée : {succes} OK, {erreurs} erreurs.")
    return succes


# ______________________________Vérification______________________________

def verifier_indexation() -> None:
    """Vérifie l'indexation avec des tests de base."""
    print("\nVérification de l'indexation...")

    # Compter les documents
    reponse = requests.get(f"{ES_HOST}/{ES_INDEX}/_count", timeout=ES_TIMEOUT)
    total   = reponse.json().get("count", 0)
    print(f"  Total documents indexés : {total}")

    # Test recherche par ville
    query_ville = {
        "query": {"term": {"ville": "Antananarivo"}},
        "size": 1
    }
    reponse = requests.post(
        f"{ES_HOST}/{ES_INDEX}/_search",
        json=query_ville,
        headers={"Content-Type": "application/json"},
        timeout=ES_TIMEOUT
    )
    hits = reponse.json()["hits"]
    print(f"  Test ville 'Antananarivo' : {hits['total']['value']} résultats")

    # Test requête géospatiale
    query_geo = {
        "query": {
            "geo_distance": {
                "distance":    "10km",
                "localisation": {"lat": -18.9137, "lon": 47.5361}
            }
        },
        "size": 1
    }
    reponse = requests.post(
        f"{ES_HOST}/{ES_INDEX}/_search",
        json=query_geo,
        headers={"Content-Type": "application/json"},
        timeout=ES_TIMEOUT
    )
    hits_geo = reponse.json()["hits"]
    print(f"  Test géo 10km/Antananarivo : {hits_geo['total']['value']} résultats")
    print("Vérification OK.")


# ______________________________Point d'entrée__________________________

if __name__ == "__main__":
    
    print("  INDEXATION IMMOBILIER MADAGASCAR")
    

    if not attendre_elasticsearch():
        sys.exit(1)

    supprimer_index()

    if not creer_index():
        sys.exit(1)

    indexer_biens(DATA_FILE)
    verifier_indexation()

  
    print("  DONNÉES PRÊTES DANS ELASTICSEARCH")
    print("  Prochaine étape : python3 src/app.py")
   
