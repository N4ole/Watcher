# CLAUDE.md — Watcher (bot Discord)

Guide d'orientation pour les futures instances de Claude travaillant sur ce
dépôt. **Watcher** est un bot Discord en Python (discord.py) : modération,
utilitaires, automodération, panel web et journalisation, entièrement
bilingue (français par défaut, anglais).

> ⚠️ Ce dépôt s'appelait `claude_bot` et a été renommé `Watcher` (voir la
> section « Renommage » plus bas). Il n'a **aucun** rapport avec un projet de
> benchmark de bases de données.

## Vue d'ensemble

- **Langage / lib** : Python 3.11, `discord.py` 2.7.x.
- **Commandes** : hybrides (préfixe `§` **et** slash `/`) via
  `@commands.hybrid_command`. Le préfixe est configurable
  (`COMMAND_PREFIX`, défaut `§`).
- **Point d'entrée** : `main.py` → `setup_logging()` puis `bot.run()`.
- **Classe du bot** : `Watcher(commands.Bot)` dans `bot.py`.

## Architecture

```
main.py            Point d'entrée, configuration du logging.
bot.py             Classe Watcher : intents, chargement auto des cogs,
                   sync des commandes slash, on_error global.
config.py          Variables d'environnement (.env) : TOKEN, PREFIX,
                   OWNER_ID, GUILD_ID, OAUTH_* …
cogs/              Un fichier par commande (voir convention ci-dessous).
cogs/owner/        Commandes réservées aux owners du bot (masquées du help).
utils/             Modules partagés (voir ci-dessous).
web/               Panel web aiohttp + OAuth2 Discord.
docs/              Documentation générée + guides (OAuth, systèmes).
scripts/gen_docs.py Génère docs/commands, docs/categories.
data/              JSON runtime (gitignored : data/*.json).
logs/              Journaux fichiers (gitignored).
```

### Convention cogs (IMPORTANT)

**Un fichier = une commande**, sauf commandes directement liées qui vont
ensemble (ex. `mute`/`unmute`, `confine`/`unconfine`, `warn`/`unwarn`,
`watch`/`unwatch`). Les cogs sont chargés **récursivement** depuis `cogs/`
(les fichiers commençant par `_` sont ignorés).

### Modules `utils/`

- `storage.py` — persistance JSON par serveur : réglages
  (`get_setting`/`set_setting`), warns, watched, confinements, **tempbans**,
  modlog, reminders, owners. Chaque type a son fichier + son `Lock`.
- `i18n.py` — cœur de la traduction : `t(source, key, **kwargs)` résout la
  langue via `source` (Context/guild/id → réglage `lang` du serveur,
  français par défaut). Grand `_CATALOG` fr/en. Aussi `EIGHTBALL`,
  `get_lang`.
- `categories.py` — **source unique** du mapping cog → catégorie
  (`cat.general/info/util/mod/owner_server`) + permissions. Partagé par le
  help ET le système de logs. Contient aussi `TYPE_TO_CAT` / `CAT_TO_TYPE`
  / `resolve_type` pour la commande `logs`.
- `checks.py` — `is_owner_id`, `is_owner()` (check), `all_owner_ids()`.
- `duration.py` — `parse_duration("1h30m")` → timedelta ; `human(delta)`.
- `automod.py` — escalade partagée (caps/emoji) : avertissement → mute.
- `badwords.py` — dictionnaire multilingue anti-insulte + variantes.
- `analytics.py` — séries temporelles pour la commande `analyse`.
- `logsetup.py` — journalisation fichier **triée** + console **colorée**.

### Web (`web/`)

- `web_app.py` — app aiohttp : OAuth2 Discord, sessions en mémoire, page de
  login (avec **consentement cookies bloquant** avant connexion), dashboard
  owner à 3 pages (Général / Analytics / Live), pages légales publiques
  (confidentialité / conditions) bilingues. Thème néon.
- `logbuffer.py` — handler logging → tampon circulaire pour la console
  « live » du panel.
- `prefs.py` — langue par **compte** web (`data/web_prefs.json`).
- `stats.py` — instantanés / historique pour les graphiques.

## Sous-systèmes clés

- **Modération** : `kick`, `ban` (raison + durée optionnelle → ban
  temporaire persisté dans `data/tempbans.json`, déban auto au terme, MP à
  l'utilisateur + invitation de retour), `mute`/`unmute` (timeout Discord),
  `warn` (escalade 1→5 : avert. → mute 5 min → mute 1 h → confinement 1
  semaine → ban), `confine`/`unconfine`, `clear`.
- **Automodération** : `antibot`, `antiraid` (captcha à l'arrivée),
  `antipub`, `antispam`, `antiinsulte`, anti-caps, anti-emoji. Les admins
  sont exemptés.
- **Watch** : `watch <user>` copie l'activité d'un membre dans un salon
  dédié (messages, éditions, suppressions, vocal, réactions, pseudo/statut).
- **Logs Discord** : `logs <on|off> <type>` (admin). Crée une catégorie
  `logs` + un salon par type (types = catégories du help). Consigne chaque
  commande de la catégorie activée (qui/où/via/args) et les échecs.
- **Rapport d'erreurs** : `cogs/errorreport.py` envoie un MP détaillé aux
  owners sur erreur inattendue (commande ou événement, via
  `Watcher.on_error`), avec traceback (jointe si longue), anti-spam et
  anti-récursion.
- **Owners du bot** : `cogs/owner/` — `addowner`/`rmowner`, `serveurs`,
  `invite`, `respond` (MP à un propriétaire de serveur ou `all` pour une
  annonce), `helpowner`, `central`, `reload`/`shutdown`/`say`. Réservés via
  `checks.is_owner()`, utilisables aussi en MP.

## Internationalisation

Tout texte affiché passe par `t(source, "clef", **kwargs)`. Ajouter une
chaîne = ajouter une entrée `{"fr": ..., "en": ...}` dans `_CATALOG`
(`utils/i18n.py`). Les **descriptions de commandes** du help sont traduites
via les clés `cmddesc.<nom>` (repli sur la description du décorateur si
absente). Langue résolue **par serveur** (réglage `lang`) et **par compte**
côté web.

## Journalisation

`utils/logsetup.py`, branché dans `main.setup_logging()` :
- **Console colorée** par niveau (couleurs ANSI seulement si TTY ; le
  `LogRecord` n'est jamais muté pour ne pas polluer les autres handlers).
- **Fichiers triés** (`logs/`, rotation quotidienne, 30 jours) :
  `bot.log` (tout), `actions.log` (logger `action`), `errors.log`
  (WARNING+).
- Le logger nommé `action` sert de fil des « actions » du bot.

## Décisions techniques

- **Commandes hybrides** partout pour couvrir préfixe + slash d'un seul
  tenant.
- **Persistance JSON simple** (pas de base de données) : suffisant à
  l'échelle du bot, un fichier + `Lock` par domaine dans `storage.py`.
- **i18n centralisée** dans un seul catalogue, langue portée par le serveur
  (et par compte sur le web).
- **`utils/categories.py` = source unique** des catégories, pour éviter la
  divergence entre help et logs.
- **MP avant sanction** (kick/ban) : une fois l'utilisateur exclu, le bot ne
  partage plus de serveur avec lui et ne peut plus le contacter.
- **Bans temporaires persistés** et repris au démarrage (`on_ready`), sur le
  même modèle que les confinements.
- **Exemption des admins** dans l'automodération (choix produit assumé).

## Workflow Git

- Développement sur la branche `claude/discord-bot-python-base-5klfd6`
  (repartir de `origin/main` après chaque merge).
- Messages de commit avec le trailer :
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Après push, ouvrir une **PR draft** ; la passer « ready » sur demande.
- `data/*.json` et `logs/` sont **gitignored**.

## Renommage `ClaudeBot` → `Watcher`

Le bot et le dépôt s'appelaient `claude_bot`/`ClaudeBot`. Le dépôt a été
renommé **`Watcher`** sur GitHub, puis le code rebrandé : classe
`ClaudeBot` → `Watcher`, imports (`main.py`, `scripts/gen_docs.py`), et tous
les textes affichés (botinfo, panel web, pages légales, catalogue i18n,
rapports d'erreur, README/docs).

**Point d'attention (environnement sandbox)** : le trafic git est forcé à
travers un proxy local verrouillé sur l'ancien chemin `N4ole/claude_bot`.
Pointer le remote vers `github.com/N4ole/Watcher` renvoie **403** dans ce
bac à sable. La résolution : **garder** le remote sur le chemin
`…/git/N4ole/claude_bot` — GitHub **redirige** automatiquement l'ancien nom
vers le dépôt renommé, donc fetch/push continuent de fonctionner et
atterrissent bien sur `Watcher`. Sur une machine locale (hors sandbox), on
peut faire `git remote set-url origin https://github.com/N4ole/Watcher.git`.

## État actuel

- Tronc fonctionnel : bot complet (commandes, automod, watch, web, logs,
  i18n) — voir plus haut.
- **PR #14** (branche `claude/…`, marquée *ready*) regroupe : console
  colorée, traduction des descriptions du help, commandes `kick`/`ban`
  (+ MP à l'utilisateur et invite de fin de ban), système de **logs
  Discord** par type, et le renommage `ClaudeBot → Watcher`.
- Le repo n'a **pas** de checks CI configurés.

## Prochaines étapes possibles

- Fusionner la PR #14 puis repartir de `main`.
- Éventuelle commande `unban` manuelle (aujourd'hui, seul le ban temporaire
  se lève automatiquement).
- Étendre les logs Discord aux événements non-commandes (automod, arrivées/
  départs) si souhaité.
- Régénérer la documentation (`python scripts/gen_docs.py`) après ajout de
  commandes.
