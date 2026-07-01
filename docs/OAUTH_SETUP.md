# Guide : configurer l'OAuth2 pour accéder au panel web

Ce guide explique, étape par étape, tout ce qu'il faut pour activer et accéder
au **panel web d'administration** du bot (connexion via compte Discord).

---

## Étape 1 — Ouvrir l'application du bot

1. Va sur le [portail développeur Discord](https://discord.com/developers/applications).
2. Connecte-toi, puis clique sur **l'application** de ton bot (celle qui contient
   le bot). Si tu n'en as pas encore, clique sur **New Application**, donne un
   nom, puis ouvre-la.

---

## Étape 2 — Récupérer le Client ID et le Client Secret

1. Dans le menu de gauche, ouvre l'onglet **OAuth2**.
2. Note le **Client ID** (`OAUTH_CLIENT_ID`).
3. Clique sur **Reset Secret** (ou **Copy** si déjà généré) pour obtenir le
   **Client Secret** (`OAUTH_CLIENT_SECRET`).
   > ⚠️ Le secret ne s'affiche qu'une fois : copie-le immédiatement. Ne le
   > partage jamais et ne le mets pas dans un dépôt public.

---

## Étape 3 — Déclarer l'URL de redirection (Redirect)

Le panel utilise l'URL `/callback` pour recevoir la réponse de Discord.

1. Toujours dans **OAuth2**, section **Redirects**, clique sur **Add Redirect**.
2. Ajoute l'URL **exacte** qui sera utilisée pour joindre le panel, suivie de
   `/callback`. Exemples :
   - En local : `http://localhost:8080/callback`
   - Sur un serveur/domaine : `https://ton-domaine.tld/callback`
3. Clique sur **Save Changes**.

> L'URL déclarée ici doit correspondre **au caractère près** à la variable
> `OAUTH_REDIRECT_URI` du bot (même schéma http/https, même hôte, même port,
> même chemin).

---

## Étape 4 — Renseigner le fichier `.env` du bot

Dans le fichier `.env` du bot, remplis :

```env
OAUTH_CLIENT_ID=xxxxxxxxxxxxxxxxxx
OAUTH_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OAUTH_REDIRECT_URI=http://localhost:8080/callback
WEB_HOST=0.0.0.0
WEB_PORT=8080
# Optionnel : secret de signature des sessions (généré si laissé vide).
WEB_SECRET=
```

- `OAUTH_REDIRECT_URI` doit être **identique** à l'URL déclarée à l'étape 3.
- `WEB_HOST=0.0.0.0` écoute sur toutes les interfaces ; utilise `127.0.0.1`
  pour n'écouter qu'en local.
- `WEB_PORT` est le port d'écoute (doit correspondre au port de l'URL).

> Le panel **ne démarre que si** `OAUTH_CLIENT_ID` et `OAUTH_CLIENT_SECRET`
> sont renseignés.

---

## Étape 5 — (Recommandé) Définir l'owner du bot

Pour avoir accès à **toutes** les données du panel, renseigne ton identifiant
Discord comme owner principal :

```env
OWNER_ID=ton_identifiant_discord
```

> Pour obtenir ton ID : active le **Mode développeur** dans Discord
> (Paramètres → Avancés → Mode développeur), puis clic droit sur ton profil →
> **Copier l'identifiant**.

---

## Étape 6 — Lancer le bot et ouvrir le panel

1. Démarre le bot :
   ```bash
   python main.py
   ```
   Tu dois voir dans les logs : `Panel web démarré sur http://0.0.0.0:8080`.
2. Ouvre un navigateur sur l'URL du panel (sans `/callback`) :
   - En local : `http://localhost:8080`
3. Clique sur **Se connecter avec Discord**, autorise l'application.
4. Tu es redirigé vers le tableau de bord avec les graphiques.

---

## Qui a accès au panel ?

- **Owners du bot** (`OWNER_ID` + owners ajoutés via `addowner`) : accès à
  **toutes** les données (nombre de serveurs, membres, utilisation).
- **Administrateurs** d'un serveur où le bot est présent : accès aux données
  **des serveurs qu'ils administrent** uniquement.
- Les autres utilisateurs sont **refusés**.

---

## Dépannage

| Symptôme | Cause probable / solution |
|----------|---------------------------|
| `Invalid OAuth2 redirect_uri` | L'URL de l'étape 3 ne correspond pas à `OAUTH_REDIRECT_URI`. Vérifie schéma, hôte, port et `/callback`. |
| Le panel ne démarre pas | `OAUTH_CLIENT_ID` ou `OAUTH_CLIENT_SECRET` manquant dans `.env`. |
| « Accès refusé » après connexion | Tu n'es ni owner, ni administrateur d'un serveur où le bot est présent. |
| Page inaccessible | Vérifie que le `WEB_PORT` est ouvert/non bloqué et que l'hôte est joignable. |
| Déconnecté à chaque redémarrage | Normal si `WEB_SECRET` est vide (sessions en mémoire). Définis un `WEB_SECRET` fixe pour les conserver. |

---

## En production (exposer le panel sur Internet)

- Place le panel derrière un **reverse proxy** (nginx, Caddy...) avec **HTTPS**.
- Utilise une URL de redirection en `https://` et déclare-la à l'étape 3.
- Définis un `WEB_SECRET` fixe et garde `OAUTH_CLIENT_SECRET` confidentiel.
