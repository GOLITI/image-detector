# Image Detector - Détecteur de Falsification d'Images

Application web Django pour détecter les falsifications et manipulations d'images en utilisant l'analyse ELA (Error Level Analysis) et le calcul de hash.

## 🎯 Fonctionnalités

- **Détection de falsification** : Analyse d'images pour détecter les modifications et manipulations
- **Comparaison d'images** : Comparaison de deux images pour vérifier leur authenticité
- **Analyse ELA** : Utilisation de l'Error Level Analysis pour identifier les zones modifiées
- **Calcul de hash** : Génération de hash pour identifier les images dupliquées
- **Interface intuitive** : Interface web responsive et facile à utiliser
- **Historique des analyses** : Conservation et consultation des analyses précédentes

## 🛠️ Technologies Utilisées

- **Backend** : Django 5.2.7
- **Traitement d'images** : 
  - OpenCV (opencv-python)
  - Pillow
  - scikit-image
  - NumPy
  - SciPy
- **Frontend** : HTML, CSS, JavaScript (Bootstrap)
- **Base de données** : SQLite (par défaut)

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git

## 🚀 Installation

1. **Cloner le repository**
   ```bash
   git clone https://github.com/GOLITI/image-detector.git
   cd image-detector
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   ```

3. **Activer l'environnement virtuel**
   - Windows :
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac :
     ```bash
     source venv/bin/activate
     ```

4. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

5. **Effectuer les migrations**
   ```bash
   python manage.py migrate
   ```

6. **Créer un superutilisateur (optionnel)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

8. **Accéder à l'application**
   - Ouvrez votre navigateur et allez sur : `http://127.0.0.1:8000`

## 📁 Structure du Projet

```
image-detector/
├── config/              # Configuration Django
│   ├── settings.py      # Paramètres du projet
│   ├── urls.py          # Routes principales
│   └── wsgi.py          # Configuration WSGI
├── detector/            # Application principale
│   ├── models.py        # Modèles de données
│   ├── views.py         # Vues et logique métier
│   ├── forms.py         # Formulaires
│   ├── urls.py          # Routes de l'application
│   └── admin.py         # Configuration admin
├── services/            # Services de traitement
│   ├── forgery_detector.py    # Détection de falsification
│   ├── image_processor.py     # Traitement d'images
│   └── hash_calculator.py     # Calcul de hash
├── utils/               # Utilitaires
│   ├── helpers.py       # Fonctions d'aide
│   └── validators.py    # Validateurs personnalisés
├── templates/           # Templates HTML
├── static/              # Fichiers statiques (CSS, JS)
├── media/               # Fichiers uploadés
├── requirements.txt     # Dépendances Python
└── manage.py           # Script de gestion Django
```

## 🔧 Configuration

### Variables d'environnement (Recommandé pour la production)

Créez un fichier `.env` à la racine du projet :

```env
SECRET_KEY=votre-clé-secrète-ici
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com
```

## 🎨 Utilisation

1. **Upload d'une image**
   - Accédez à la page d'accueil
   - Téléchargez l'image à analyser
   - (Optionnel) Téléchargez une image de référence pour comparaison

2. **Analyse**
   - L'application effectue automatiquement l'analyse ELA
   - Calcule le hash de l'image
   - Compare les deux images si une référence est fournie

3. **Résultats**
   - Visualisation de l'image analysée avec l'analyse ELA
   - Statistiques et métriques de détection
   - Hash de l'image
   - Niveau de suspicion de falsification

4. **Historique**
   - Consultez toutes vos analyses précédentes
   - Filtrez et recherchez dans l'historique

## 🧪 Tests

Pour exécuter les tests :

```bash
python manage.py test
```

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👥 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 🐛 Signaler un Bug

Si vous trouvez un bug, veuillez ouvrir une issue avec :
- Une description claire du problème
- Les étapes pour reproduire le bug
- Le comportement attendu vs le comportement observé
- Votre environnement (OS, version de Python, etc.)

## 📧 Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue sur GitHub.

## 🙏 Remerciements

- OpenCV pour le traitement d'images
- Django pour le framework web
- La communauté open source

---

**Note** : Cette application est destinée à des fins éducatives et de recherche. Les résultats de détection ne doivent pas être considérés comme une preuve définitive de falsification.
