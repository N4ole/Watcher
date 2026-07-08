# Déploiement automatique depuis GitHub

Ce guide explique comment faire en sorte que **tout push sur GitHub se
déploie sur le serveur** qui héberge Watcher, à l'aide du script
[`scripts/deploy.sh`](../scripts/deploy.sh).

Principe : le serveur exécute périodiquement `deploy.sh`, qui compare la
version locale à celle de GitHub. S'il y a du nouveau, il **remplace le code
local par celui de GitHub** (`git reset --hard`), réinstalle les dépendances
si `requirements.txt` a changé, puis redémarre le bot.

> Les fichiers **non suivis par git** (`data/*.json`, `logs/`, `.env`) ne
> sont **jamais** écrasés par le déploiement : la configuration et les
> données runtime sont préservées.

> 📬 **Notification** : à chaque mise à jour, `deploy.sh` écrit une note
> (`data/pending_deploy.json`) que le bot lit au redémarrage pour envoyer un
> **MP aux owners** (PR concernées, commits, version à jour), via le cog
> `updatenotify`. Les liens de PR utilisent `REPO_URL` (`.env`,
> défaut `https://github.com/N4ole/Watcher`).

## 1. Prérequis

- Le dépôt est cloné sur le serveur et la branche de production est
  suivie (par défaut `main`).
- Python et `pip` sont installés (idéalement un virtualenv).
- Le bot tourne comme un **process Python autonome** (§2, recommandé — pas
  besoin de systemd) ou, si vous préférez, comme un **service systemd**
  (§2 bis, alternative avancée).

## 2. Lancer le bot en process Python simple (sans systemd)

Le bot tourne directement via `python3 main.py`, géré par
[`scripts/watcher-ctl.sh`](../scripts/watcher-ctl.sh) : démarrage, arrêt
propre, et surtout **relance automatique en cas de plantage** (le bot est
relancé après 2 secondes s'il s'arrête ou crashe).

```bash
cd /opt/watcher
scripts/watcher-ctl.sh start      # démarre le bot (boucle de relance)
scripts/watcher-ctl.sh status     # « En cours » ou « Arrêté »
scripts/watcher-ctl.sh stop       # arrêt propre (TERM, puis KILL après 10s)
scripts/watcher-ctl.sh restart    # utilisé automatiquement par deploy.sh
```

Détails :
- La sortie du bot va dans `logs/runtime.log`.
- Le PID de la boucle de relance est suivi dans `.watcher.pid` (gitignoré).
- `deploy.sh` (§3) appelle **automatiquement** `watcher-ctl.sh restart`
  après une mise à jour, dès lors qu'**aucun** service systemd
  `${DEPLOY_SERVICE}` n'est configuré — rien à faire de plus pour que le
  redémarrage après déploiement fonctionne.
- Pour démarrer le bot automatiquement après un redémarrage du serveur,
  ajoutez à la crontab : `@reboot cd /opt/watcher && scripts/watcher-ctl.sh start`.

## 2 bis. Alternative : service systemd

Si vous préférez déléguer la supervision du process à systemd plutôt qu'à
`watcher-ctl.sh`, créez `/etc/systemd/system/watcher.service` :

```ini
[Unit]
Description=Watcher (bot Discord)
After=network-online.target

[Service]
Type=simple
User=watcher
WorkingDirectory=/opt/watcher
ExecStart=/opt/watcher/.venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activez-le :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now watcher
```

Tant qu'un service nommé `${DEPLOY_SERVICE}` (défaut `watcher`) existe,
`deploy.sh` l'utilise en priorité (`systemctl restart`) plutôt que
`watcher-ctl.sh`.

## 3. Déploiement manuel

```bash
cd /opt/watcher
scripts/deploy.sh
```

Variables disponibles :

| Variable         | Défaut     | Rôle                                                     |
|------------------|------------|-----------------------------------------------------------|
| `DEPLOY_BRANCH`  | `main`     | Branche GitHub à déployer                                |
| `DEPLOY_SERVICE` | `watcher`  | Service systemd à redémarrer (ignoré s'il n'existe pas — repli automatique sur `watcher-ctl.sh`) |
| `DEPLOY_PYTHON`  | `python3`  | Interpréteur utilisé pour `pip install` et pour lancer `main.py` |

## 4. Lancement périodique « à chaque push » (installation clé en main)

Pour que le déploiement s'exécute **automatiquement** (et déploie donc les
nouveaux commits sans intervention), un lancement périodique de `deploy.sh`
est fourni prêt à l'emploi :

```bash
# Timer systemd (recommandé, journaux via journalctl) — toutes les minutes :
scripts/install-autodeploy.sh systemd

# ou via cron :
scripts/install-autodeploy.sh cron

# intervalle personnalisable (minutes) :
DEPLOY_INTERVAL_MIN=2 scripts/install-autodeploy.sh systemd
```

L'installeur détecte automatiquement le **chemin du dépôt** et
l'**utilisateur** courant (rien n'est codé en dur), rend les unités
[`watcher-deploy.service`](../scripts/watcher-deploy.service) /
[`watcher-deploy.timer`](../scripts/watcher-deploy.timer) (ou la ligne cron),
et active le tout. Ces unités ne servent qu'à **exécuter `deploy.sh`
périodiquement** (indépendant de la façon dont le bot lui-même tourne) : le
déploiement ne redémarre le bot **que** s'il y a de nouveaux commits.

> En mode « process Python simple » (§2), `watcher-ctl.sh` tourne avec le
> même utilisateur que le bot : **aucun sudo n'est nécessaire**. La règle
> sudoers ci-dessous ne concerne que le mode systemd (§2 bis).

Si le bot tourne comme service systemd (§2 bis), le redémarrage `systemctl`
nécessite les droits : autorisez l'utilisateur à redémarrer **uniquement**
ce service, via sudoers (commande rappelée en fin d'installation) :

```sudoers
# /etc/sudoers.d/watcher-deploy
watcher ALL=(root) NOPASSWD: /usr/bin/systemctl restart watcher
```

### Mise en place manuelle (équivalent)

Si vous préférez installer sans le script :

```cron
# crontab -e  (utilisateur qui possède le dépôt)
* * * * * cd /opt/watcher && DEPLOY_BRANCH=main DEPLOY_SERVICE=watcher \
  scripts/deploy.sh >> /opt/watcher/logs/deploy.log 2>&1
```

ou, côté systemd, en copiant les deux unités fournies dans
`/etc/systemd/system/` puis `systemctl enable --now watcher-deploy.timer`.

## 5. Variante : déploiement instantané par webhook

Le cron introduit un délai (jusqu'à 1 min). Pour un déploiement **immédiat**
au push, exposez un petit endpoint qui exécute `deploy.sh` à la réception
d'un webhook GitHub « push » (vérifiez la signature `X-Hub-Signature-256`
avec un secret partagé). Cette voie demande un port public et davantage de
durcissement ; le cron reste l'option la plus simple et sans surface réseau
supplémentaire.

## Notes de sécurité

- `git reset --hard` **écrase** toute modification locale suivie par git :
  ne modifiez jamais le code directement sur le serveur, faites-le via
  GitHub.
- Limitez le `NOPASSWD` sudo au **seul** `systemctl restart <service>`.
- Gardez `.env` (token, secrets) hors du dépôt : il est déjà `gitignored`
  et préservé par le déploiement.
