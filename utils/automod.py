"""Logique partagée d'automodération (détection + escalation des sanctions).

Escalation par infraction (compteur par utilisateur et par type) :
    1re  -> suppression + message d'avertissement
    2e   -> suppression + avertissement officiel
    3e+  -> suppression + mute (timeout) de 5, 10, 15... minutes
"""
import logging
import re
from datetime import timedelta

import discord

from utils.i18n import t

log = logging.getLogger("action")

# --- Détection majuscules -------------------------------------------------- #
# On ignore les messages trop courts pour éviter les faux positifs.
_MIN_LETTERS = 8
CAPS_THRESHOLD = 0.75


def caps_ratio(text: str) -> float:
    """Proportion de lettres majuscules (0.0 si trop peu de lettres)."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) < _MIN_LETTERS:
        return 0.0
    uppercase = sum(1 for c in letters if c.isupper())
    return uppercase / len(letters)


def is_caps_spam(text: str) -> bool:
    return caps_ratio(text) > CAPS_THRESHOLD


# --- Détection emojis ------------------------------------------------------ #
_MIN_EMOJIS = 5
EMOJI_THRESHOLD = 0.75

_CUSTOM_EMOJI = re.compile(r"<a?:\w+:\d+>")
_UNICODE_EMOJI = re.compile(
    "["
    "\U0001f000-\U0001faff"  # pictogrammes, supplément, extended-A
    "\U00002600-\U000027bf"  # symboles divers + dingbats
    "\U00002b00-\U00002bff"  # symboles et flèches divers
    "\U0001f1e6-\U0001f1ff"  # indicateurs régionaux (drapeaux)
    "]"
)


def emoji_stats(content: str) -> tuple[int, int]:
    """Renvoie (nombre d'emojis, nombre d'autres caractères non-espaces)."""
    n_custom = len(_CUSTOM_EMOJI.findall(content))
    rest = _CUSTOM_EMOJI.sub("", content)
    n_unicode = len(_UNICODE_EMOJI.findall(rest))
    others = sum(
        1 for c in _UNICODE_EMOJI.sub("", rest) if not c.isspace()
    )
    return n_custom + n_unicode, others


def is_emoji_spam(content: str) -> bool:
    emojis, others = emoji_stats(content)
    if emojis < _MIN_EMOJIS:
        return False
    return emojis / (emojis + others) > EMOJI_THRESHOLD


# --- Escalation ------------------------------------------------------------ #
def mute_minutes(count: int) -> int:
    """Durée du mute (min) pour la 3e infraction et au-delà : 5, 10, 15..."""
    return (count - 2) * 5


async def apply_escalation(
    message: discord.Message, count: int, label_key: str
) -> None:
    """Applique la sanction correspondant au niveau d'infraction.

    `label_key` est une clé i18n (ex. "am.caps"), traduite selon le serveur.
    """
    member = message.author
    channel = message.channel
    guild = message.guild
    label = t(guild, label_key)

    # Suppression du message fautif.
    try:
        await message.delete()
    except discord.HTTPException:
        pass

    if count == 1:
        action = "suppression"
        await channel.send(
            t(guild, "am.warn1", user=member.mention, label=label),
            delete_after=10,
        )
    elif count == 2:
        action = "avertissement"
        await channel.send(t(guild, "am.warn2", user=member.mention, label=label))
    else:
        minutes = mute_minutes(count)
        action = f"mute {minutes} min"
        try:
            await member.timeout(timedelta(minutes=minutes), reason=label)
        except discord.HTTPException:
            pass
        await channel.send(
            t(guild, "am.mute", user=member.mention, label=label, minutes=minutes)
        )

    where = f"#{getattr(channel, 'name', '?')} / {guild.name} ({guild.id})"
    log.info(
        "Automod %s — %s sur %s (%s) dans %s",
        label_key.split(".")[-1], action, member, member.id, where,
    )
