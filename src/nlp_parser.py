
# ______________________________Pipeline : Normalisation → Tokenisation → Vectorisation
#            → Similarité cosinus → Extraction → Query DSL______________________________

import re
import numpy as np
import pandas as pd


# ÉTAPE 1 — TABLE DE NORMALISATION DES CARACTÈRES
# Objectif : supprimer les accents et mettre en minuscules
# Pourquoi : "Ivandry" et "ivandry" doivent être identiques

TABLE_ACCENTS = str.maketrans(
    "àáâãäèéêëìíîïòóôõöùúûüýÿçñ",
    "aaaaaeeeeiiiiooooouuuuyycn"
)

def normaliser(texte: str) -> str:
    """
    Étape 1 — Nettoyage du texte brut.

    Opérations :
      - Mise en minuscules
      - Suppression des accents via table de traduction
      - Suppression des caractères spéciaux inutiles

    Exemple :
      "Moins de 300 Millions à Ivandry" 
      → "moins de 300 millions a ivandry"
    """
    texte = texte.lower()
    texte = texte.translate(TABLE_ACCENTS)
    texte = re.sub(r"[^\w\s]", " ", texte)   # garde lettres, chiffres, espaces
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte


# ______________________________ÉTAPE 2 — TOKENISATION______________________________
# Objectif : découper la phrase en liste de tokens (mots)
# Pourquoi : on ne peut pas comparer des phrases directement

def tokeniser(texte: str) -> list:
    """
    Étape 2 — Découpage en tokens.

    Méthode : on split sur les espaces et on filtre les vides.
    On conserve aussi les bigrammes (paires de mots consécutifs)
    pour capturer "nosy be", "bon etat", "groupe electrogene".

    Exemple :
      "villa avec jardin a tana"
      → unigrammes : ["villa","avec","jardin","a","tana"]
      → bigrammes  : ["villa avec","avec jardin","jardin a","a tana"]
      → sortie     : les deux listes combinées
    """
    unigrammes = [t for t in texte.split() if t]

    # Bigrammes : paires de mots adjacents
    bigrammes = [
        f"{unigrammes[i]} {unigrammes[i+1]}"
        for i in range(len(unigrammes) - 1)
    ]

    return unigrammes + bigrammes


#______________________________ ÉTAPE 3 — VOCABULAIRE ET VECTEURS TF (Term Frequency)______________________________
# Objectif : représenter chaque token par un vecteur numérique
# Pourquoi : les comparaisons numériques sont plus robustes

# Vocabulaire de référence : tous les termes du domaine immobilier
VOCABULAIRE_DOMAINE = [
    # Types de biens
    "villa", "maison", "appartement", "appart", "studio",
    "terrain", "duplex", "loft", "bureau",
    # Villes
    "antananarivo", "tana", "tananarive", "toamasina", "tamatave",
    "mahajanga", "majunga", "fianarantsoa", "fianar",
    "antsiranana", "diego", "toliara", "tulear",
    "nosy be", "antsirabe",
    # Quartiers
    "analakely", "tsaralalana", "ankorondrano", "ambohijatovo",
    "ivandry", "ankadifotsy", "mahamasina", "andohatapenaka",
    "ambatobe", "tanjombato", "andravoahangy", "isotry",
    "ampefiloha", "faravohitra", "isoraka", "antanimena",
    "talatamaty", "androhibe", "bazary be", "tanambao",
    "morafeno", "ampasimadinika", "mahabibo", "amborovy",
    "mangarivotra", "joffreville", "ramena", "centre ville",
    "mahavatse", "betania", "hell ville", "ambatoloaka",
    "dzamandzar", "madirokely", "mandrosoa", "ambohimena",
    # Équipements
    "jardin", "parking", "terrasse", "piscine", "gardien",
    "cloture", "puits", "electrogene", "groupe electrogene",
    "solaire", "panneau solaire", "citerne", "portail",
    "balcon", "climatisation", "clim", "internet", "fibre",
    "cuisine", "cuisine equipee",
    # États
    "neuf", "nouveau", "renover", "renovation", "bon etat",
    # Indicateurs de prix
    "moins", "max", "maximum", "plus", "min", "minimum",
    "cher", "abordable", "economique", "budget",
    # Unités
    "million", "millions", "milliard", "milliards",
    # Indicateurs de surface
    "m2", "metre", "metres",
    # Indicateurs de pièces
    "pieces", "piece", "chambres", "chambre",
]

# Créer un DataFrame vocabulaire pour accès rapide 
df_vocab = pd.DataFrame({
    "terme": VOCABULAIRE_DOMAINE,
    "index": range(len(VOCABULAIRE_DOMAINE))
}).set_index("terme")


def vectoriser(tokens: list) -> np.ndarray:
    """
    Étape 3 — Vectorisation TF (Term Frequency).

    Chaque dimension = fréquence d'un terme dans les tokens.

    Exemple :
      tokens = ["villa", "jardin", "villa"]
      → vecteur[index("villa")] = 2
      → vecteur[index("jardin")] = 1
      → tous les autres = 0

    Pourquoi NumPy : opérations vectorielles rapides.
    """
    vecteur = np.zeros(len(VOCABULAIRE_DOMAINE), dtype=np.float32)

    for token in tokens:
        if token in df_vocab.index:
            idx = df_vocab.loc[token, "index"]
            vecteur[idx] += 1.0

    return vecteur


def similarite_cosinus(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Mesure la similarité entre deux vecteurs.

    Formule cosinus :
      sim(A, B) = (A · B) / (||A|| × ||B||)

    Retourne 1.0 si identiques, 0.0 si aucun point commun.
    Utilisé pour : matcher la phrase avec les catégories connues.
    """
    norme_a = np.linalg.norm(vec_a)
    norme_b = np.linalg.norm(vec_b)

    if norme_a == 0 or norme_b == 0:
        return 0.0

    return float(np.dot(vec_a, vec_b) / (norme_a * norme_b))


#______________________________ ÉTAPE 4 — DICTIONNAIRES DE CORRESPONDANCE (MAPPING)______________________________
# Objectif : convertir les tokens en valeurs structurées

TYPES_BIENS = {
    "villa": "villa", "maison": "maison",
    "appartement": "appartement", "appart": "appartement",
    "studio": "studio", "terrain": "terrain",
    "duplex": "duplex", "loft": "loft", "bureau": "bureau",
}

VILLES = {
    "antananarivo": {"nom": "Antananarivo", "lat": -18.9137, "lon": 47.5361},
    "tana":         {"nom": "Antananarivo", "lat": -18.9137, "lon": 47.5361},
    "tananarive":   {"nom": "Antananarivo", "lat": -18.9137, "lon": 47.5361},
    "toamasina":    {"nom": "Toamasina",    "lat": -18.1443, "lon": 49.3958},
    "tamatave":     {"nom": "Toamasina",    "lat": -18.1443, "lon": 49.3958},
    "mahajanga":    {"nom": "Mahajanga",    "lat": -15.7167, "lon": 46.3167},
    "majunga":      {"nom": "Mahajanga",    "lat": -15.7167, "lon": 46.3167},
    "fianarantsoa": {"nom": "Fianarantsoa", "lat": -21.4531, "lon": 47.0833},
    "fianar":       {"nom": "Fianarantsoa", "lat": -21.4531, "lon": 47.0833},
    "antsiranana":  {"nom": "Antsiranana",  "lat": -12.3530, "lon": 49.2960},
    "diego":        {"nom": "Antsiranana",  "lat": -12.3530, "lon": 49.2960},
    "toliara":      {"nom": "Toliara",      "lat": -23.3568, "lon": 43.6693},
    "tulear":       {"nom": "Toliara",      "lat": -23.3568, "lon": 43.6693},
    "nosy be":      {"nom": "Nosy Be",      "lat": -13.3333, "lon": 48.2667},
    "antsirabe":    {"nom": "Antsirabe",    "lat": -19.8659, "lon": 47.0337},
}

QUARTIERS = [
    "analakely","tsaralalana","ankorondrano","ambohijatovo",
    "ivandry","ankadifotsy","mahamasina","andohatapenaka",
    "ambatobe","tanjombato","andravoahangy","isotry",
    "ampefiloha","faravohitra","isoraka","antanimena",
    "talatamaty","androhibe","bazary be","tanambao",
    "morafeno","ampasimadinika","mahabibo","amborovy",
    "mangarivotra","joffreville","ramena","centre ville",
    "mahavatse","betania","hell-ville","ambatoloaka",
    "dzamandzar","madirokely","mandrosoa","ambohimena",
    "antsikorotana","scama","tsienimparihy","anketa",
    "mitsinjo","sanfily","andrainjato","tsianolondroa",
    "mahereza","abattoir","aranta","mangabe","logement",
    "anjoma","ambohipo","barikadimy","tsaramandroso",
    "andranomanalina","tsarahonenana","antsenakely",
]

EQUIPEMENTS = {
    "jardin": "jardin", "parking": "parking",
    "terrasse": "terrasse", "piscine": "piscine",
    "gardien": "gardien", "cloture": "clôture",
    "puits": "puits", "electrogene": "groupe électrogène",
    "groupe electrogene": "groupe électrogène",
    "solaire": "panneau solaire", "panneau solaire": "panneau solaire",
    "citerne": "citerne eau", "portail": "portail",
    "balcon": "balcon", "climatisation": "climatisation",
    "clim": "climatisation", "internet": "internet fibre",
    "fibre": "internet fibre", "cuisine": "cuisine équipée",
    "cuisine equipee": "cuisine équipée",
}

ETATS = {
    "neuf": "neuf", "nouveau": "neuf",
    "renover": "à rénover", "renovation": "à rénover",
    "bon etat": "bon état",
}

UNITES_PRIX = {
    "million": 1_000_000, "millions": 1_000_000,
    "milliard": 1_000_000_000, "milliards": 1_000_000_000,
}

MOTS_PRIX_MAX = {"moins", "max", "maximum", "jusqu", "inferieur"}
MOTS_PRIX_MIN = {"plus", "min", "minimum", "partir", "superieur"}
MOTS_PAS_CHER = {"cher", "abordable", "economique", "budget"}


# ______________________________Objectif : utiliser les vecteurs + dictionnaires pour extraire______________________________


def extraire_type_bien(tokens: list, vecteur: np.ndarray) -> str | None:
    """
    Extraction du type de bien.

    Méthode hybride :
      1. Correspondance exacte dans le dictionnaire (rapide)
      2. Si pas trouvé → similarité cosinus avec les types connus

    Le vecteur NumPy permet de comparer rapidement
    la phrase avec chaque type de bien connu.
    """
    # Méthode 1 : correspondance directe
    for token in tokens:
        if token in TYPES_BIENS:
            return TYPES_BIENS[token]

    # Méthode 2 : similarité cosinus (fallback)
    meilleur_score = 0.3   # seuil minimum
    meilleur_type  = None

    for type_bien in TYPES_BIENS:
        tokens_type  = tokeniser(type_bien)
        vecteur_type = vectoriser(tokens_type)
        score        = similarite_cosinus(vecteur, vecteur_type)

        if score > meilleur_score:
            meilleur_score = score
            meilleur_type  = TYPES_BIENS[type_bien]

    return meilleur_type


def extraire_ville(texte_norm: str) -> tuple:
    """
    Extraction de la ville.

    On travaille sur le texte complet (pas les tokens)
    pour gérer les villes en deux mots : "nosy be".

    Priorité : alias spécifiques avant les noms généraux.
    """
    # Priorité aux noms composés
    if "nosy be" in texte_norm:
        d = VILLES["nosy be"]
        return d["nom"], {"lat": d["lat"], "lon": d["lon"]}

    for alias, data in VILLES.items():
        if alias in texte_norm:
            return data["nom"], {"lat": data["lat"], "lon": data["lon"]}

    return None, None


def extraire_quartier(texte_norm: str) -> str | None:
    """
    Extraction du quartier.

    On cherche chaque quartier connu dans le texte normalisé.
    Si un quartier est trouvé, il est prioritaire sur la ville
    lors de la construction de la requête Elasticsearch.
    """
    for quartier in QUARTIERS:
        if quartier in texte_norm:
            return quartier.title()
    return None


def extraire_nb_pieces(tokens: list, texte_norm: str) -> int | None:
    """
    Extraction du nombre de pièces.

    Gère plusieurs formats courants :
      - "4 pièces" / "4 pieces"
      - "T3" / "F3"  (notation française)
      - "4P" (notation courte)
    """
    # Format "T3" ou "F3"
    match = re.search(r"\b[tf](\d)\b", texte_norm)
    if match:
        return int(match.group(1))

    # Format "4 pièces" ou "4 pieces"
    match = re.search(r"(\d+)\s*(?:pieces?|p\b)", texte_norm)
    if match:
        return int(match.group(1))

    return None


def extraire_prix(tokens: list, texte_norm: str) -> tuple:
    """
    Extraction du prix minimum et maximum.

    Algorithme :
      1. Détecter les indicateurs de direction (min/max)
      2. Trouver les nombres dans les tokens (NumPy array)
      3. Associer chaque nombre à son unité (million/milliard)
      4. Classer en prix_min ou prix_max selon le contexte

    NumPy est utilisé pour :
      - Stocker les positions des nombres (array d'indices)
      - Recherche vectorielle des contextes numériques
    """
    prix_min = None
    prix_max = None

    # Détecter "pas cher" → plafond implicite 150M Ar
    mots = set(tokens)
    if "pas" in mots and bool(mots & MOTS_PAS_CHER):
        prix_max = 150_000_000

    # Extraire tous les nombres et leurs positions
    nombres_pos = np.array([
        i for i, t in enumerate(tokens) if t.isdigit()
    ], dtype=np.int32)

    for pos in nombres_pos:
        valeur  = int(tokens[pos])
        unite   = 1_000_000    

        # Chercher l'unité dans les 2 tokens suivants
        for j in range(pos + 1, min(pos + 3, len(tokens))):
            if tokens[j] in UNITES_PRIX:
                unite = UNITES_PRIX[tokens[j]]
                break

        montant  = valeur * unite

        # Analyser le contexte (3 tokens avant le nombre)
        debut    = max(0, int(pos) - 3)
        contexte = set(tokens[debut:int(pos)])

        if contexte & MOTS_PRIX_MAX:
            prix_max = montant
        elif contexte & MOTS_PRIX_MIN:
            prix_min = montant

    return prix_min, prix_max


def extraire_surface(tokens: list, texte_norm: str) -> tuple:
    """
    Extraction de la surface en m².

    Cherche les patterns : "120m2", "120 m2", "120 metres"
    puis regarde le contexte pour savoir si c'est min ou max.

    NumPy : utilisé pour créer le tableau des positions
    des nombres dans la liste de tokens.
    """
    surf_min = None
    surf_max = None

    match = re.search(r"(\d+)\s*m[2²]", texte_norm)
    if match:
        valeur = int(match.group(1))

        # Chercher la direction dans les mots avant
        pos_match = match.start()
        contexte  = texte_norm[:pos_match]

        if any(m in contexte for m in ["moins", "max", "maximum"]):
            surf_max = valeur
        elif any(m in contexte for m in ["plus", "min", "minimum"]):
            surf_min = valeur
        else:
            # Surface exacte : tolérance ±15 m²
            surf_min = max(0, valeur - 15)
            surf_max = valeur + 15

    return surf_min, surf_max


def extraire_equipements(tokens: list) -> list:
    """
    Extraction des équipements mentionnés.

    Utilise un DataFrame Pandas pour la recherche :
    on crée un Series des tokens et on filtre ceux
    qui correspondent à un équipement connu.

    Avantage Pandas : filtre vectoriel sur toute la liste
    en une seule opération (pas de boucle explicite).
    """
    # Série Pandas des tokens
    serie_tokens = pd.Series(tokens)

    # Bigrammes Pandas (tokens consécutifs joints)
    if len(serie_tokens) > 1:
        bigrammes = serie_tokens + " " + serie_tokens.shift(-1).fillna("")
    else:
        bigrammes = pd.Series([], dtype=str)

    # Combiner unigrammes et bigrammes
    tous = pd.concat([serie_tokens, bigrammes], ignore_index=True)

    # Filtrer ceux qui sont dans le dictionnaire d'équipements
    trouves_raw = tous[tous.isin(EQUIPEMENTS.keys())].tolist()

    # Convertir en valeurs normalisées et dédupliquer
    trouves = []
    for t in trouves_raw:
        valeur = EQUIPEMENTS[t]
        if valeur not in trouves:
            trouves.append(valeur)

    return trouves


def extraire_etat(tokens: list, texte_norm: str) -> str | None:
    """
    Extraction de l'état du bien.

    Gère les cas en un mot ("neuf") et deux mots ("bon état").
    On cherche d'abord les bigrammes, puis les unigrammes.
    """
    # Bigramme "bon etat"
    if "bon etat" in texte_norm:
        return "bon état"

    # Unigrammes
    for token in tokens:
        if token in ETATS and token != "bon":
            return ETATS[token]

    return None


def extraire_rayon(tokens: list) -> int:
    """
    Extraction du rayon de recherche géospatiale en km.

    Format attendu : "5 km", "dans 10km"
    Défaut : 10 km si aucun rayon mentionné.
    """
    for i, token in enumerate(tokens):
        if token == "km" and i > 0 and tokens[i - 1].isdigit():
            return int(tokens[i - 1])
    return 10


# ÉTAPE 6 — PARSEUR PRINCIPAL
# Orchestre toutes les étapes du pipeline NLP

def parser_phrase(phrase: str) -> dict:
    """
    Pipeline NLP complet from scratch.

    Flux de traitement :
      Texte brut
        → [Étape 1] Normalisation
        → [Étape 2] Tokenisation + Bigrammes
        → [Étape 3] Vectorisation TF (NumPy)
        → [Étape 4] Extraction entités (Pandas + NumPy)
        → Dictionnaire structuré

    Args:
        phrase : requête textuelle de l'utilisateur

    Returns:
        Dictionnaire des entités extraites
    """
    # Étape 1 : normaliser
    texte_norm = normaliser(phrase)

    # Étape 2 : tokeniser
    tokens = tokeniser(texte_norm)

    # Étape 3 : vectoriser (représentation numérique)
    vecteur = vectoriser(tokens)

    # Étape 4 : extraire chaque entité
    ville_nom, coords  = extraire_ville(texte_norm)
    prix_min, prix_max = extraire_prix(tokens, texte_norm)
    surf_min, surf_max = extraire_surface(tokens, texte_norm)

    return {
        "phrase_originale": phrase,
        "type_bien":        extraire_type_bien(tokens, vecteur),
        "ville":            ville_nom,
        "coords":           coords,
        "quartier":         extraire_quartier(texte_norm),
        "nb_pieces":        extraire_nb_pieces(tokens, texte_norm),
        "prix_min":         prix_min,
        "prix_max":         prix_max,
        "surface_min":      surf_min,
        "surface_max":      surf_max,
        "equipements":      extraire_equipements(tokens),
        "etat":             extraire_etat(tokens, texte_norm),
        "rayon_km":         extraire_rayon(tokens),
    }

# ______________________________ÉTAPE 7 — CONSTRUCTION REQUÊTE ELASTICSEARCH DSL______________________________
# Traduit les entités en filtres Elasticsearch

def construire_query(entites: dict) -> dict:
    """
    Traduit les entités en requête Elasticsearch DSL.

    Chaque entité trouvée = un filtre dans bool/filter.
    L'opérateur filter (pas must) ignore le scoring
    et optimise les performances sur grand dataset.

    Args:
        entites : dictionnaire retourné par parser_phrase()

    Returns:
        Requête DSL prête à envoyer à Elasticsearch
    """
    filtres = []

    if entites["type_bien"]:
        filtres.append({"term": {"type_bien": entites["type_bien"]}})

    # Quartier prioritaire sur ville
    if entites["quartier"]:
        filtres.append({"term": {"quartier": entites["quartier"]}})
    elif entites["ville"]:
        filtres.append({"term": {"ville": entites["ville"]}})

    if entites["nb_pieces"]:
        filtres.append({"term": {"nb_pieces": entites["nb_pieces"]}})

    if entites["prix_min"] or entites["prix_max"]:
        plage = {}
        if entites["prix_min"]: plage["gte"] = entites["prix_min"]
        if entites["prix_max"]: plage["lte"] = entites["prix_max"]
        filtres.append({"range": {"prix_ariary": plage}})

    if entites["surface_min"] or entites["surface_max"]:
        plage = {}
        if entites["surface_min"]: plage["gte"] = entites["surface_min"]
        if entites["surface_max"]: plage["lte"] = entites["surface_max"]
        filtres.append({"range": {"surface": plage}})

    for equip in entites["equipements"]:
        filtres.append({"term": {"equipements": equip}})

    if entites["etat"]:
        filtres.append({"term": {"etat": entites["etat"]}})

    if entites["coords"]:
        filtres.append({
            "geo_distance": {
                "distance":    f"{entites['rayon_km']}km",
                "localisation": entites["coords"]
            }
        })

    query = {"bool": {"filter": filtres}} if filtres else {"match_all": {}}
    return {"query": query, "size": 10, "sort": [{"prix_ariary": {"order": "asc"}}]}


# ______________________________TESTS______________________________

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  NLP FROM SCRATCH — NumPy + Pandas")
    print("  Normalisation → Tokenisation → Vectorisation → Extraction")
    print("=" * 65)

    tests = [
        "villa avec jardin à Ivandry moins de 300 millions",
        "maison 4 pièces à Mahajanga avec groupe électrogène",
        "studio pas cher à Antananarivo",
        "appartement T3 neuf à Tana moins de 200 millions",
        "terrain à Toamasina plus de 100 millions",
        "villa avec piscine et parking à Nosy Be",
        "duplex 120m2 à Antsirabe bon état",
    ]

    for phrase in tests:
        norm    = normaliser(phrase)
        tokens  = tokeniser(norm)
        vecteur = vectoriser(tokens)
        entites = parser_phrase(phrase)
        query   = construire_query(entites)

        print(f" Phrase     : {phrase}")
        print(f"   Normalisé  : {norm}")
        print(f"   Tokens     : {tokens[:8]}{'...' if len(tokens)>8 else ''}")
        print(f"   Vecteur    : {vecteur[vecteur>0]} (termes non nuls: {int(np.sum(vecteur>0))})")
        print("   Entités    :")
        for k, v in entites.items():
            if v and k not in ("phrase_originale","coords"):
                print(f"     {k:<15} → {v}")
        nb = len(query["query"].get("bool",{}).get("filter",[]))
        print(f"   → {nb} filtre(s) ES générés")
