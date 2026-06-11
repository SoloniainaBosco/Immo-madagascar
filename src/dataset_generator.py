
#-------------------- Génération du dataset immobilier Madagascar-------------------- 

import os
import json
import math
import random
import pandas as pd
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.settings import VILLES, TYPES_BIENS, ETATS, EQUIPEMENTS, NB_BIENS, DATA_DIR, DATA_FILE, DATA_CSV


# -------------------Fonctions utilitaires-------------------- 

def point_aleatoire_autour(lat: float, lon: float, rayon_km: float = 5.0):
    """Génère un point GPS aléatoire autour d'un centre."""
    rayon_deg = rayon_km / 111.0
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, rayon_deg)
    return (
        round(lat + distance * math.cos(angle), 6),
        round(lon + distance * math.sin(angle), 6),
    )


def calculer_prix(ville_data: dict, type_bien: str, surface: int, etat: str) -> int:
    """Calcule un prix réaliste selon la ville, le type et l'état."""
    coef_type = {
        "villa":        1.4,
        "maison":       1.1,
        "appartement":  1.0,
        "duplex":       1.2,
        "studio":       0.9,
        "terrain":      0.5,
    }
    coef_etat = {
        "neuf":       1.25,
        "bon état":   1.00,
        "à rénover":  0.70,
    }
    variation  = random.uniform(0.80, 1.25)
    prix_m2    = int(
        ville_data["prix_m2"]
        * coef_type.get(type_bien, 1.0)
        * coef_etat.get(etat, 1.0)
        * variation
    )
    return prix_m2 * surface


def surface_selon_type(type_bien: str) -> tuple:
    """Retourne (surface, nb_pieces) selon le type de bien."""
    configs = {
        "studio":       (random.randint(18, 38),  1),
        "appartement":  (lambda: (nb := random.randint(2, 5), nb * random.randint(14, 22))[1], lambda: random.randint(2, 5)),
        "maison":       (random.randint(70, 280),  random.randint(3, 7)),
        "villa":        (random.randint(150, 500), random.randint(4, 9)),
        "duplex":       (random.randint(80, 200),  random.randint(3, 6)),
        "terrain":      (random.randint(100, 3000), 0),
    }
    if type_bien == "appartement":
        nb_pieces = random.randint(2, 5)
        surface   = nb_pieces * random.randint(14, 22)
        return surface, nb_pieces
    surface, nb_pieces = configs.get(type_bien, (100, 3))
    if callable(surface):
        surface = surface()
    if callable(nb_pieces):
        nb_pieces = nb_pieces()
    return surface, nb_pieces


def generer_titre(type_bien: str, quartier: str, ville: str, nb_pieces: int, surface: int) -> str:
    """Génère un titre d'annonce réaliste."""
    templates = [
        f"{type_bien.capitalize()} {nb_pieces}P à {quartier}",
        f"À vendre : {type_bien} {surface}m² – {quartier}, {ville}",
        f"Beau {type_bien} {nb_pieces} pièces – {ville}",
        f"{type_bien.capitalize()} lumineux {surface}m² – {quartier}",
        f"Vente {type_bien} {nb_pieces}P {surface}m² {quartier}",
    ]
    return random.choice(templates)


def generer_description(type_bien: str, surface: int, nb_pieces: int,
                        quartier: str, etat: str, equipements: list) -> str:
    """Génère une description d'annonce réaliste."""
    equip_str = ", ".join(equipements) if equipements else "aucun équipement mentionné"
    return (
        f"{type_bien.capitalize()} de {surface} m² composé de {nb_pieces} pièce(s), "
        f"situé à {quartier}. "
        f"État général : {etat}. "
        f"Équipements inclus : {equip_str}. "
        f"Idéal pour résidence principale ou investissement locatif."
    )


# -------------------- Générateur principal-------------------- 

def generer_dataset(nb_biens: int = NB_BIENS) -> list:
    """
    Génère un dataset immobilier Madagascar avec des données réalistes.

    Args:
        nb_biens: Nombre de biens à générer

    Returns:
        Liste de dictionnaires représentant les biens immobiliers
    """
    print(f"Génération de {nb_biens} biens immobiliers...")
    biens = []
    date_debut = datetime.now() - timedelta(days=730)  # 2 ans en arrière

    for i in range(nb_biens):
        # Sélection aléatoire des attributs principaux
        ville_nom  = random.choice(list(VILLES.keys()))
        ville_data = VILLES[ville_nom]
        type_bien  = random.choice(TYPES_BIENS)
        etat       = random.choice(ETATS)
        quartier   = random.choice(ville_data["quartiers"])

        # Surface et pièces
        surface, nb_pieces = surface_selon_type(type_bien)

        # Prix
        prix = calculer_prix(ville_data, type_bien, surface, etat)

        # Localisation GPS
        lat, lon = point_aleatoire_autour(ville_data["lat"], ville_data["lon"])

        # Équipements (2 à 6 aléatoires)
        nb_equip   = random.randint(2, 6)
        equipements = random.sample(EQUIPEMENTS, k=nb_equip)

        # Date d'annonce
        jours_offset = random.randint(0, 730)
        date_annonce = (date_debut + timedelta(days=jours_offset)).strftime("%Y-%m-%d")

        bien = {
            "id":             f"immo-{i+1:05d}",
            "titre":          generer_titre(type_bien, quartier, ville_nom, nb_pieces, surface),
            "description":    generer_description(type_bien, surface, nb_pieces, quartier, etat, equipements),
            "type_bien":      type_bien,
            "ville":          ville_nom,
            "quartier":       quartier,
            "surface":        surface,
            "nb_pieces":      nb_pieces,
            "prix_ariary":    prix,
            "prix_m2_ariary": prix // surface if surface > 0 else 0,
            "etat":           etat,
            "equipements":    equipements,
            "localisation":   {"lat": lat, "lon": lon},
            "date_annonce":   date_annonce,
        }
        biens.append(bien)

        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{nb_biens} biens générés...")

    print(f"Génération terminée : {len(biens)} biens.")
    return biens

#--------------------  Sauvegarde -------------------- 

def sauvegarder_json(biens: list, chemin: str) -> None:
    """Sauvegarde les biens au format JSON."""
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(biens, f, ensure_ascii=False, indent=2)
    print(f"JSON sauvegardé : {chemin}")


def sauvegarder_csv(biens: list, chemin: str) -> None:
    """Sauvegarde les biens au format CSV (pour Kibana)."""
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    df = pd.DataFrame(biens)
    df["latitude"]    = df["localisation"].apply(lambda x: x["lat"])
    df["longitude"]   = df["localisation"].apply(lambda x: x["lon"])
    df["equipements"] = df["equipements"].apply(lambda x: ", ".join(x))
    df.drop(columns=["localisation"], inplace=True)
    df.to_csv(chemin, index=False, encoding="utf-8")
    print(f"CSV sauvegarde  : {chemin}")


def afficher_statistiques(biens: list) -> None:
    """Affiche les statistiques du dataset généré."""
    prix_list    = [b["prix_ariary"] for b in biens]
    surface_list = [b["surface"] for b in biens]
    villes       = {}
    types        = {}

    for b in biens:
        villes[b["ville"]]     = villes.get(b["ville"], 0) + 1
        types[b["type_bien"]]  = types.get(b["type_bien"], 0) + 1

   
    print("  STATISTIQUES DU DATASET")
   
    print(f"  Total biens         : {len(biens)}")
    print(f"  Villes couvertes    : {len(villes)}")
    print(f"  Prix moyen          : {int(sum(prix_list)/len(prix_list)):>15,} Ar")
    print(f"  Prix minimum        : {int(min(prix_list)):>15,} Ar")
    print(f"  Prix maximum        : {int(max(prix_list)):>15,} Ar")
    print(f"  Surface moyenne     : {int(sum(surface_list)/len(surface_list)):>10} m²")
    print("-" * 55)
    print("  Répartition par ville :")
    for ville, nb in sorted(villes.items(), key=lambda x: -x[1]):
        barre = "█" * (nb // 20)
        print(f"    {ville:<20} {nb:>4}  {barre}")
    print("-" * 55)
    print("  Répartition par type :")
    for t, nb in sorted(types.items(), key=lambda x: -x[1]):
        barre = "█" * (nb // 20)
        print(f"    {t:<20} {nb:>4}  {barre}")
  


# -------------------------------------------------------------
# Point d'entrée
# -------------------------------------------------------------

if __name__ == "__main__":
    biens = generer_dataset(NB_BIENS)
    sauvegarder_json(biens, DATA_FILE)
    sauvegarder_csv(biens, DATA_CSV)
    afficher_statistiques(biens)
