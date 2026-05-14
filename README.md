# 🏥 ARIA Secure — Module IA Radiographique pour GNU Health

> Ajout d'un module d'analyse automatique de radiographies par intelligence artificielle dans GNU Health, avec détection de pathologies et génération de heatmaps.

**Projet tuteuré de synthèse — Équipe ARIA Secure, 2026**

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [Entraînement du modèle](#-entraînement-du-modèle)
- [Planning](#-planning)
- [Ressources](#-ressources)

---

## 🎯 Vue d'ensemble

ARIA Secure intègre un bouton **« Analyser par IA »** directement dans les fiches radiographies de GNU Health. En un clic, le système :

1. Envoie la radiographie au moteur IA
2. Détecte automatiquement les pathologies
3. Calcule un score de confiance
4. Génère une heatmap de visualisation
5. Affiche les résultats dans le dossier patient

---

## 🏗️ Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────┐
│       GNU Health            │        │      Service IA (ARIA)   │
│  (Tryton / Python)          │        │   (FastAPI / PyTorch)    │
│                             │        │                          │
│  Module z_health_aria  ─────┼──────▶ │  POST /analyze           │
│  (bouton + onglet IA)       │        │  Modèle EfficientNetV2-S │
│                             │◀───────┼─ Résultats JSON          │
└─────────────────────────────┘        └──────────────────────────┘
         Port 8000                               Port 8001
```

| Composant | Description | Technologie |
|---|---|---|
| **GNU Health** | Système hospitalier : patients, dossiers, auth | Python / Tryton |
| **z_health_aria** | Module custom : onglet IA + bouton d'analyse | Python / XML |
| **Service IA** | Microservice de détection de pathologies | Python / PyTorch / FastAPI |

---

## ⚙️ Prérequis

- **OS** : Ubuntu 22.04 LTS (ou WSL2 sous Windows)
- **Python** : 3.10 ou supérieur
- **PostgreSQL** : 14+
- **RAM** : 8 Go minimum recommandés
- **GPU** : optionnel (nécessaire pour l'entraînement, utiliser Kaggle sinon)

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-org/aria-gnuhealth.git
cd aria-gnuhealth
```

### 2. Créer l'environnement Python

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
# Dépendances GNU Health
pip install trytond gnuhealth-all-modules psycopg2-binary Pillow pydicom requests

# Dépendances Service IA
pip install fastapi uvicorn torch torchvision numpy opencv-python-headless python-multipart
```

### 4. Configurer PostgreSQL

```bash
sudo -u postgres psql <<EOF
CREATE USER gnuhealth WITH PASSWORD 'gnuhealth';
CREATE DATABASE gnuhealth OWNER gnuhealth;
GRANT ALL PRIVILEGES ON DATABASE gnuhealth TO gnuhealth;
EOF
```

### 5. Configurer et initialiser GNU Health

```bash
# Initialiser la base de données (5-10 min)
trytond-admin -c config/trytond.conf -d gnuhealth --all
```

### 6. Activer le module ARIA

```bash
# Créer le lien symbolique vers le module
ln -s $(pwd)/modules/z_health_aria $(python3 -c "import trytond, os; print(os.path.join(os.path.dirname(trytond.__file__), 'modules'))")/z_health_aria

# Installer le module dans la base
trytond-admin -c config/trytond.conf -d gnuhealth -u z_health_aria
```

---

## 💻 Utilisation

### Démarrer le projet (à chaque session)

```bash
# Terminal 1 — GNU Health
source venv/bin/activate
sudo systemctl start postgresql
trytond -c config/trytond.conf

# Terminal 2 — Service IA
source venv/bin/activate
cd ai_service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

- **GNU Health** : http://localhost:8000 (identifiants : `admin` / `admin`)
- **Service IA** : http://localhost:8001

### Après chaque modification du module

```bash
trytond-admin -c config/trytond.conf -d gnuhealth -u z_health_aria
trytond -c config/trytond.conf
```

### Tester le service IA

```bash
curl -X POST http://localhost:8001/analyze \
     -F 'file=@/chemin/vers/radiographie.jpg'
```

---

## 📁 Structure du projet

```
aria-gnuhealth/
│
├── config/
│   └── trytond.conf          # Configuration GNU Health
│
├── modules/
│   └── z_health_aria/        # Module GNU Health custom
│       ├── __init__.py
│       ├── __tryton__.py     # Déclaration du module
│       ├── z_health_aria.py  # Modèles de données + bouton
│       ├── tryton.cfg
│       └── view/
│           └── radiography_aria_form.xml  # Interface XML
│
└── ai_service/               # Moteur IA indépendant
    ├── main.py               # Serveur FastAPI
    ├── model.py              # Chargement + inférence PyTorch
    ├── heatmap.py            # Génération Grad-CAM
    ├── schemas.py            # Structures de données
    ├── dataset.py            # Dataset PyTorch (MURA)
    ├── train.py              # Script d'entraînement
    └── checkpoints/          # Poids du modèle entraîné
```

---

## 🧠 Entraînement du modèle

Le modèle de base est un **EfficientNetV2-S** pré-entraîné sur ImageNet, fine-tuné sur des radiographies médicales.

### Datasets recommandés

| Dataset | Contenu | Taille | Source |
|---|---|---|---|
| **MURA** *(recommandé pour débuter)* | Fractures osseuses — 2 classes | ~3 Go | [stanfordmlgroup.github.io/mura](https://stanfordmlgroup.github.io/mura) |
| **NIH ChestX-ray14** | 14 pathologies thoraciques | ~40 Go | [kaggle.com/datasets/nih-chest-xrays](https://www.kaggle.com/datasets/nih-chest-xrays) |

### Lancer l'entraînement

```bash
cd ai_service
python train.py
```

> 💡 **Conseil** : utilisez [Kaggle Notebooks](https://www.kaggle.com/notebooks) (GPU gratuit) pour l'entraînement, puis téléchargez le fichier `.pt` généré.

---

## 🧪 Tests

| Test | Commande / Action | Résultat attendu |
|---|---|---|
| Service IA démarre | `uvicorn main:app --port 8001` | Pas d'erreur |
| Service IA répond | `GET http://localhost:8001/` | `{"status": "ok"}` |
| Analyse d'une image | `POST /analyze` avec une radio | JSON avec pathologies |
| Module GNU Health | Redémarrer GNU Health | Pas d'erreur dans les logs |
| Onglet IA visible | Ouvrir une fiche radiographie | Onglet « Analyse IA » présent |
| Bouton fonctionnel | Cliquer sur « Lancer l'analyse IA » | Statut → « Terminé » |

### Problèmes fréquents

| Problème | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError` | Environnement virtuel non activé | `source venv/bin/activate` |
| Erreur PostgreSQL | Service arrêté | `sudo systemctl start postgresql` |
| Module non trouvé par Tryton | Lien symbolique manquant | Refaire la commande `ln -s` |
| Timeout lors de l'analyse | Modèle lent sur CPU | Augmenter le timeout dans `requests.post` |
| Port déjà utilisé | Conflit de ports | Changer le port dans la commande `uvicorn` |

---

## 📅 Planning

| Semaine | Travail | Livrable |
|---|---|---|
| 1 | Installation de l'environnement | Environnement prêt |
| 2 | Installation et exploration de GNU Health | GNU Health opérationnel |
| 3-4 | Création du module `z_health_aria` | Onglet IA visible |
| 5 | Développement du service IA (FastAPI + EfficientNet) | Service IA fonctionnel |
| 6 | Connexion GNU Health ↔ Service IA | Analyse end-to-end |
| 7-8 | Téléchargement MURA + entraînement sur Kaggle | Modèle `.pt` entraîné |
| 9 | Intégration du vrai modèle + tests complets | Résultats réels |
| 10 | Documentation + démonstration | Projet final |

---

## 📚 Ressources

| Ressource | Lien |
|---|---|
| Documentation GNU Health | https://docs.gnuhealth.org |
| Documentation Tryton | https://doc.tryton.org |
| Documentation FastAPI | https://fastapi.tiangolo.com |
| Documentation PyTorch | https://pytorch.org/docs |
| Dataset MURA | https://stanfordmlgroup.github.io/mura |
| Kaggle (GPU gratuit) | https://www.kaggle.com/notebooks |
| Forum GNU Health / Tryton | https://discuss.tryton.org |

---

## 👥 Équipe

Projet réalisé par l'**Équipe ARIA Secure** dans le cadre d'un projet tuteuré de synthèse — 2026.

---

*Pour toute question : aria@votreuniversite.cm*
