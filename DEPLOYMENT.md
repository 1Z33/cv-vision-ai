# 🚀 Guide de Déploiement sur Render

Ce guide explique comment déployer CVision AI sur Render avec PostgreSQL.

## Prérequis

- Compte [Render.com](https://render.com)
- GitHub repository avec le code
- Pas de clé d'API ou secret dans le code

## Option 1: Déploiement Automatique via render.yaml (Recommandé)

### Étapes

1. **Connecter Render à GitHub**
   - Aller sur [Render Dashboard](https://dashboard.render.com)
   - Cliquer sur "New" → "Web Service"
   - Sélectionner "Deploy from GitHub"
   - Autoriser Render à accéder à tes repos

2. **Sélectionner le repo**
   - Chercher et sélectionner `cv-vision-ai`
   - Sélectionner la branche `main`

3. **Render charge automatiquement render.yaml**
   - La configuration `render.yaml` à la racine du projet est automatiquement lue
   - La base de données PostgreSQL est créée automatiquement
   - Les variables d'environnement sont définies via `fromDatabase`

4. **Vérifier les paramètres**
   ```
   Service Name:  cv-vision-ai-backend
   Runtime:       Python 3.11
   Build Command: cd backend && pip install -r requirements.txt
   Start Command: cd backend && alembic upgrade head && uvicorn ...
   Region:        EU (libre)
   Plan:          Free
   ```

5. **Déployer**
   - Cliquer "Create Web Service"
   - Render crée le service + la DB PostgreSQL
   - Le déploiement commence automatiquement (~5-10 min)

### Variables d'environnement automatiques

Render injecte automatiquement:
- `DATABASE_URL`: Connection string PostgreSQL
- `SYNC_DATABASE_URL`: Connection string synchrone (pour Alembic)
- `SECRET_KEY`: Génère une clé aléatoire
- Autres variables de `.env`

## Option 2: Déploiement Manuel (Sans render.yaml)

Si Render ne lit pas `render.yaml`:

1. **Créer le service**
   - Dashboard → New → Web Service
   - Connecter le repo GitHub

2. **Configurer manuellement**
   ```
   Build Command:  cd backend && pip install -r requirements.txt
   Start Command:  cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Créer la base de données PostgreSQL**
   - Dashboard → New → PostgreSQL Database
   - Nom: `cv_vision_db`
   - Plan: Free
   - Region: EU

4. **Ajouter les variables d'environnement**
   - Dans les paramètres du service Web
   - Ajouter chaque variable:
     ```
     DATABASE_URL         = (Copier depuis PostgreSQL connexion interne)
     SYNC_DATABASE_URL    = (Copier depuis PostgreSQL)
     SECRET_KEY           = (Générer: openssl rand -hex 32)
     ENVIRONMENT          = production
     DEBUG                = false
     ALGORITHM            = HS256
     ACCESS_TOKEN_EXPIRE_MINUTES = 30
     REFRESH_TOKEN_EXPIRE_DAYS   = 7
     ```

5. **Connecter la base de données**
   - Dans PostgreSQL, copier l'URL interne
   - Coller dans `DATABASE_URL` du service Web

## Architecture du Déploiement

```
┌─────────────────────────────────────────┐
│         Render Dashboard                │
├──────────────────┬──────────────────────┤
│  Web Service     │   PostgreSQL DB      │
│  (cv-vision-ai)  │   (cv_vision_db)     │
│  Python 3.11     │   Free Plan          │
│  Port: $PORT     │   EU Region          │
│  Memory: 512MB   │                      │
└──────────────────┴──────────────────────┘
        ↓ Uvicorn ↓
        App Server (8000)
        │
        ├─ SQLAlchemy ORM
        ├─ Alembic Migrations
        └─ FastAPI Routes
```

## Configuration PostgreSQL

Render crée automatiquement une base PostgreSQL avec:
- **Utilisateur**: Aléatoire (fourni par Render)
- **Mot de passe**: Aléatoire (sécurisé)
- **URL Interne**: Pour les services sur Render
- **URL Publique**: Optionnelle (désactivée par défaut)

La migration s'exécute au démarrage:
```bash
alembic upgrade head
```

## Dépannage

### ❌ `sqlalchemy.exc.OperationalError: could not connect to server`

**Cause**: La DB n'existe pas ou l'URL est incorrecte

**Solution**:
1. Vérifier que la DB PostgreSQL est créée dans Render
2. Copier l'URL de la DB dans `DATABASE_URL`
3. Redémarrer le service

### ❌ `ModuleNotFoundError: No module named 'app'`

**Cause**: Working directory incorrect dans build command

**Solution**:
```bash
# Corriger le Build Command:
pip install -r backend/requirements.txt

# Corriger le Start Command:
alembic -c backend/alembic.ini upgrade head && \
cd backend && \
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### ❌ `PendingDeprecationWarning: alembic version`

**Non bloquant** - Juste un warning. Le service fonctionne quand même.

### ✅ Service déployé mais page blanche

**Possible causes**:
- Frontend n'est pas déployé (déploie le frontend séparément)
- CORS mal configuré (vérifier `app.main:app` CORSMiddleware)
- API n'écoute pas sur le bon port (Render utilise `$PORT`)

## Mise à jour du Code

### Déployer une nouvelle version

```bash
git add .
git commit -m "Description du changement"
git push origin main
```

Render redéploie automatiquement (environ 5-10 minutes).

### Supprimer un déploiement

Dashboard → Service → Settings → Danger Zone → Delete Service

## Alertes et Monitoring

- Render envoie des alertes par email pour:
  - Crashes du service
  - Déploiements échoués
  - Limite de ressources atteinte
  - Outages de la DB

## Limites du Plan Gratuit

- **Web Service**: 512 MB RAM, 0,1 CPU
- **PostgreSQL**: 256 MB stockage, Hibernation après 15 min d'inactivité
- **Déploiement**: Gratuit
- **Bande passante**: 100 GB/mois

⚠️ **Note**: Render mettra en hibernation les services inactifs pendant plus de 15 minutes.

## Passage en Plan Payant

Si tu dépasses les limites du gratuit:
1. Dashboard → Service → Settings → Plan
2. Choisir le plan approprié
3. Les frais sont facturés mensuellement

## Alternatives

- **Heroku**: Arrêt du plan gratuit (novembre 2022)
- **Railway.app**: Alternative populaire, support gratuit limité
- **Fly.io**: Docker-first, plan gratuit généreux
- **PythonAnywhere**: Python spécialisé, UI moins moderne

---

**Questions?** Consulte la [Documentation Render](https://render.com/docs) ou ouvre une issue sur GitHub.
