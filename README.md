# **PokeValue**

PokeValue est une application permettant de rechercher et d’évaluer des cartes Pokémon via un backend Flask et une interface utilisateur Streamlit.

---

## **Aperçu du projet**

PokeValue est une application composée de deux parties :

- **Backend Flask :** Permet de rechercher des cartes Pokémon via un scraping d'un site externe et d’enregistrer les recherches dans une base de données SQLite.
- **Frontend Streamlit :** Offre une interface utilisateur simple pour effectuer des recherches et consulter des collections.

---

## **Tâches principales**

1. **Extraction des annonces :** Scraper les données des cartes via Selenium.
2. **Filtrage des données :** Supprimer les cartes non pertinentes (par exemple, cartes gradées).
3. **Calcul de la valeur moyenne :** Fournir une estimation basée sur les prix disponibles.
4. **Lister les items en vente :** Ajouter manuellement ou scraper les produits Pokémon disponibles sur d'autres plateformes.
5. **Calcul de l’espérance de valeur :** Analyser les probabilités de tirage en fonction des prix de marché.
6. **Comparer espérance vs coût :** Estimer la rentabilité des achats.
7. **Suivi des ouvertures de boosters :** Enregistrer les résultats des ouvertures.
8. **Comparer aux taux officiels :** Vérifier la cohérence entre les probabilités officielles et les données collectées.

---

## **Structure du projet**

Voici l’arborescence du projet avec une brève description des fichiers et dossiers :

PokeValue/
├── .venv/               # Environnement virtuel Python
├── .vscode/             # Paramètres spécifiques à VS Code
├── app/                 # Répertoire principal de l'application
│   ├── backend/         # Contient la logique backend
│   │   ├── models.py    # Gestion de la base de données
│   │   ├── routes.py    # Déclaration des routes Flask
│   │   ├── utils.py     # Fonctions utilitaires pour le backend
│   ├── frontend/        # Contient la logique frontend
│   │   ├── __init__.py  # Fichier d'initialisation pour le frontend
│   │   ├── front_app.py # Interface utilisateur Streamlit
├── .gitignore           # Fichiers à ignorer par Git
├── database.db          # Base de données SQLite pour le projet
├── README.md            # Documentation du projet
├── requirements.txt     # Liste des dépendances nécessaires

---

## **Prérequis**

Avant de commencer, assure-toi d’avoir les éléments suivants installés sur ton système :

1. **Python 3.8 ou supérieur**
2. **pip** (gestionnaire de paquets Python)
3. **Google Chrome** (utilisé par Selenium)
4. **Chromedriver** (version correspondant à celle de Chrome installée)

---

## **Installation**

### **Étape 1 : Cloner le dépôt**

Clone le projet depuis GitHub et place-toi dans le répertoire du projet :

```bash
git clone https://github.com/Etens/PokeValue.git
```

```bash
cd PokeValue
```

### **Étape 2 : Vérifier ou configurer un environnement virtuel**

*Optionnel : Vérifier si un venv existe déjà*
Si un environnement virtuel est déjà configuré, active-le directement :

```bash
source venv/bin/activate
```

Si aucun venv n’existe

Crée un nouvel environnement virtuel avec la commande suivante, puis active-le :

```bash
python3 -m venv venv
source venv/bin/activate
```

### **Étape 3 : Installer les dépendances**

Installe toutes les dépendances nécessaires :

```bash
pip install -r requirements.txt
```

---

## Exécution

**Lancer le backend Flask**

Depuis le dossier racine du projet :

```bash
python -m flask --app app run
```

**Lancer le frontend Streamlit**

Dans une nouvelle console, exécute :

```bash
streamlit run app/frontend/front_app.py
```
