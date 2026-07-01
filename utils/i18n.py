"""Internationalisation (i18n) du bot : français (défaut) et anglais.

Utilisation :
    from utils.i18n import t
    await ctx.send(t(ctx, "ping.result", ms=42))

La langue est déterminée par le serveur (réglage `lang`, voir storage), ou
français par défaut. `t()` accepte un `Context`, un `guild` (ou son id), ou
None (→ français).
"""
from utils import storage

DEFAULT = "fr"
LANGS = ("fr", "en")

# Catalogue des chaînes : clé -> {lang: modèle}. Les modèles utilisent la
# syntaxe str.format (ex. "{ms}").
_CATALOG: dict[str, dict[str, str]] = {
    # --- Commande langue ---
    "lang.set": {
        "fr": "✅ Langue du serveur définie sur **Français**.",
        "en": "✅ Server language set to **English**.",
    },
    "lang.current": {
        "fr": "🌍 Langue actuelle : **Français**. Utilise `langue fr` ou "
              "`langue en`.",
        "en": "🌍 Current language: **English**. Use `langue fr` or `langue en`.",
    },
    "lang.invalid": {
        "fr": "❌ Langue invalide. Choix : `fr` (français) ou `en` (anglais).",
        "en": "❌ Invalid language. Choose: `fr` (French) or `en` (English).",
    },
    # --- Général ---
    "ping.result": {
        "fr": "🏓 Pong ! Latence : **{ms} ms**",
        "en": "🏓 Pong! Latency: **{ms} ms**",
    },
    "bonjour": {
        "fr": "👋 Bonjour {user} !",
        "en": "👋 Hello {user}!",
    },
    # --- Erreurs communes ---
    "error.missing_perms": {
        "fr": "⛔ Il te manque la permission suivante pour utiliser cette "
              "commande : **{perms}**.",
        "en": "⛔ You are missing the following permission to use this "
              "command: **{perms}**.",
    },
    "error.bot_missing_perms": {
        "fr": "⚠️ Il me manque la permission suivante pour exécuter cette "
              "commande : **{perms}**.",
        "en": "⚠️ I am missing the following permission to run this "
              "command: **{perms}**.",
    },
    "error.no_dm": {
        "fr": "❌ Cette commande s'utilise sur un serveur.",
        "en": "❌ This command can only be used in a server.",
    },
    "error.dm_only": {
        "fr": "❌ Cette commande s'utilise en message privé.",
        "en": "❌ This command can only be used in direct messages.",
    },
    "error.check_failure": {
        "fr": "⛔ Tu n'as pas la permission d'utiliser cette commande.",
        "en": "⛔ You don't have permission to use this command.",
    },
    "error.member_not_found": {
        "fr": "❌ Utilisateur introuvable.",
        "en": "❌ User not found.",
    },
    "error.bad_argument": {
        "fr": "❌ Argument invalide : {error}",
        "en": "❌ Invalid argument: {error}",
    },
    "error.missing_argument": {
        "fr": "❌ Argument manquant. Usage : `{usage}`",
        "en": "❌ Missing argument. Usage: `{usage}`",
    },
    "error.generic": {
        "fr": "❌ Une erreur est survenue lors de l'exécution.",
        "en": "❌ An error occurred while running the command.",
    },
    "error.owner_only": {
        "fr": "⛔ Cette commande est réservée aux owners du bot.",
        "en": "⛔ This command is restricted to the bot owners.",
    },
    # --- Mute ---
    "mute.bad_duration": {
        "fr": "❌ Durée invalide. Exemples : `30s`, `5m`, `2h`, `1d`, `1h30m`.",
        "en": "❌ Invalid duration. Examples: `30s`, `5m`, `2h`, `1d`, `1h30m`.",
    },
    "mute.too_long": {
        "fr": "❌ La durée maximale d'un mute est de 28 jours.",
        "en": "❌ The maximum mute duration is 28 days.",
    },
    "mute.forbidden": {
        "fr": "⛔ Impossible de mute ce membre (permissions ou hiérarchie).",
        "en": "⛔ Cannot mute this member (permissions or role hierarchy).",
    },
    "mute.failed": {
        "fr": "❌ Échec du mute : {error}",
        "en": "❌ Mute failed: {error}",
    },
    "mute.title": {"fr": "🔇 Mute", "en": "🔇 Mute"},
    "mute.done": {
        "fr": "{user} est mute.",
        "en": "{user} has been muted.",
    },
    "mute.until": {"fr": "Jusqu'à", "en": "Until"},
    "mute.relative": {"fr": "Soit", "en": "That is"},
    "unmute.not_muted": {
        "fr": "{user} n'est pas mute.",
        "en": "{user} is not muted.",
    },
    "unmute.failed": {
        "fr": "❌ Échec du unmute : {error}",
        "en": "❌ Unmute failed: {error}",
    },
    "unmute.done": {
        "fr": "🔊 {user} n'est plus mute.",
        "en": "🔊 {user} is no longer muted.",
    },
    # --- Clear ---
    "clear.bad_number": {
        "fr": "❌ Indique un nombre supérieur à 0.",
        "en": "❌ Provide a number greater than 0.",
    },
    "clear.done": {
        "fr": "🧹 {count} message(s) supprimé(s).",
        "en": "🧹 {count} message(s) deleted.",
    },
    # --- Remindme ---
    "remind.bad_duration": {
        "fr": "❌ Durée invalide. Exemples : `30s`, `5m`, `2h`, `1d`, `1h30m`.",
        "en": "❌ Invalid duration. Examples: `30s`, `5m`, `2h`, `1d`, `1h30m`.",
    },
    "remind.set": {
        "fr": "✅ Je te le rappellerai en MP dans **{duration}** ({when}).",
        "en": "✅ I'll remind you in DM in **{duration}** ({when}).",
    },
    "remind.fire": {
        "fr": "⏰ Rappel : {message}",
        "en": "⏰ Reminder: {message}",
    },
    # --- Toggle générique (anti*) ---
    "toggle.usage": {
        "fr": "❌ Utilise `{name} on` ou `{name} off`.",
        "en": "❌ Use `{name} on` or `{name} off`.",
    },
    # --- Anti-bot ---
    "antibot.on": {
        "fr": "🤖 **Anti-bot activé** : les bots qui rejoignent seront "
              "automatiquement expulsés.",
        "en": "🤖 **Anti-bot enabled**: bots that join will be automatically "
              "kicked.",
    },
    "antibot.off": {
        "fr": "🤖 **Anti-bot désactivé**.",
        "en": "🤖 **Anti-bot disabled**.",
    },
    # --- Anti-raid ---
    "antiraid.on": {
        "fr": "🛡️ **Anti-raid activé** : les nouveaux membres devront valider "
              "un captcha dans #{channel} pour accéder au serveur.",
        "en": "🛡️ **Anti-raid enabled**: new members must solve a captcha in "
              "#{channel} to access the server.",
    },
    "antiraid.off": {
        "fr": "🛡️ **Anti-raid désactivé** : plus de captcha à l'arrivée.",
        "en": "🛡️ **Anti-raid disabled**: no more captcha on join.",
    },
    "antiraid.welcome": {
        "fr": "👋 Bienvenue {user} ! Pour accéder au serveur, recopie ce code : "
              "**`{code}`**\n(tu as {minutes} minutes et {attempts} essais).",
        "en": "👋 Welcome {user}! To access the server, type this code: "
              "**`{code}`**\n(you have {minutes} minutes and {attempts} tries).",
    },
    "antiraid.verified": {
        "fr": "✅ {user} vérifié, bienvenue !",
        "en": "✅ {user} verified, welcome!",
    },
    "antiraid.wrong": {
        "fr": "❌ {user} code incorrect, réessaie.",
        "en": "❌ {user} wrong code, try again.",
    },
    "antiraid.kicked": {
        "fr": "⛔ {user} n'a pas validé le captcha à temps.",
        "en": "⛔ {user} did not solve the captcha in time.",
    },
    # --- Anti-pub ---
    "antipub.on": {
        "fr": "🚫 **Anti-pub activé** : les invitations Discord seront "
              "supprimées.",
        "en": "🚫 **Anti-ad enabled**: Discord invites will be deleted.",
    },
    "antipub.off": {
        "fr": "🚫 **Anti-pub désactivé**.",
        "en": "🚫 **Anti-ad disabled**.",
    },
    "antipub.warn": {
        "fr": "🚫 {user} les invitations Discord sont interdites ici.",
        "en": "🚫 {user} Discord invites are not allowed here.",
    },
    # --- Anti-spam ---
    "antispam.on": {
        "fr": "⏱️ **Anti-spam activé** : au-delà de {max} messages en {window}s, "
              "l'utilisateur est mute {minutes} min.",
        "en": "⏱️ **Anti-spam enabled**: beyond {max} messages in {window}s, the "
              "user is muted for {minutes} min.",
    },
    "antispam.off": {
        "fr": "⏱️ **Anti-spam désactivé**.",
        "en": "⏱️ **Anti-spam disabled**.",
    },
    "antispam.warn": {
        "fr": "⏱️ {user} arrête de spammer — tu es mute {minutes} minute(s).",
        "en": "⏱️ {user} stop spamming — you are muted for {minutes} minute(s).",
    },
    # --- Anti-insulte ---
    "antiinsulte.on": {
        "fr": "🤬 **Anti-insulte activé** : les messages insultants seront "
              "supprimés.",
        "en": "🤬 **Anti-insult enabled**: insulting messages will be deleted.",
    },
    "antiinsulte.off": {
        "fr": "🤬 **Anti-insulte désactivé**.",
        "en": "🤬 **Anti-insult disabled**.",
    },
    "antiinsulte.warn": {
        "fr": "🤬 {user} les insultes ne sont pas tolérées ici.",
        "en": "🤬 {user} insults are not tolerated here.",
    },
}


def _resolve_lang(source) -> str:
    """Détermine la langue depuis un Context / guild / id / None."""
    guild_id = None
    if source is None:
        return DEFAULT
    guild = getattr(source, "guild", source)
    guild_id = getattr(guild, "id", guild)
    if not isinstance(guild_id, int):
        return DEFAULT
    lang = storage.get_setting(guild_id, "lang", DEFAULT)
    return lang if lang in LANGS else DEFAULT


def t(source, key: str, **kwargs) -> str:
    """Traduit `key` selon la langue de `source`, avec formatage `kwargs`."""
    entry = _CATALOG.get(key)
    if entry is None:
        return key
    lang = _resolve_lang(source)
    template = entry.get(lang) or entry.get(DEFAULT) or key
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template


def get_lang(source) -> str:
    """Renvoie la langue résolue ('fr' ou 'en')."""
    return _resolve_lang(source)
