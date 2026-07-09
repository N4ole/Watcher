"""Réponses traduisibles : rendu i18n + bouton de traduction (centralisé).

Toutes les réponses du bot passent par `reply()` (ou `reply_dm()`), qui envoie
un embed rendu dans la langue par défaut du serveur (français par défaut) et
attache un **bouton de traduction**. Un clic bascule le message entre français
et anglais **en place**, sans nouveau message.

Le bouton affiche le drapeau de l'**autre** langue :
  - message en français  -> bouton 🇬🇧 (clique pour passer en anglais) ;
  - message en anglais   -> bouton 🇫🇷 (clique pour repasser en français).

Comme la traduction reconstruit le message à partir de sa **clé i18n** (et non
en traduisant du texte libre), toute commande qui répond via `reply()` bénéficie
automatiquement du bouton — actuelle ou future.
"""
import discord

from utils import embeds
from utils.i18n import get_lang, other_lang, t_lang

# Bouton = drapeau de la langue vers laquelle on peut basculer.
_FLAG = {"fr": "🇬🇧", "en": "🇫🇷"}

# Durée de vie du bouton (24 h) : au-delà, il est retiré du message.
_TIMEOUT = 86400


class TranslateView(discord.ui.View):
    """Bouton de traduction attaché à un message rendu à partir d'une clé i18n."""

    def __init__(
        self, kind: str, key: str, kwargs: dict, lang: str,
        title_key: str | None = None,
    ) -> None:
        super().__init__(timeout=_TIMEOUT)
        self.kind = kind
        self.key = key
        self.kwargs = kwargs
        self.title_key = title_key
        self.lang = lang
        self.message: discord.Message | None = None
        self.translate.emoji = _FLAG[lang]

    def render(self) -> discord.Embed:
        """Construit l'embed dans la langue courante de la vue."""
        builder = getattr(embeds, self.kind, embeds.info)
        title = (
            t_lang(self.lang, self.title_key, **self.kwargs)
            if self.title_key else None
        )
        return builder(
            t_lang(self.lang, self.key, **self.kwargs), title=title
        )

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def translate(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        # Bascule la langue du message et met à jour le drapeau du bouton.
        self.lang = other_lang(self.lang)
        button.emoji = _FLAG[self.lang]
        await interaction.response.edit_message(embed=self.render(), view=self)

    async def on_timeout(self) -> None:
        if self.message is not None:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass


async def reply(
    ctx, key: str, *, kind: str = "info", title_key: str | None = None,
    ephemeral: bool = False, allowed_mentions: discord.AllowedMentions | None = None,
    **kwargs,
) -> discord.Message | None:
    """Envoie une réponse traduisible (embed + bouton) dans le salon courant.

    `kind` ∈ {success, error, info, warn, fun} (couleur de l'embed).
    `key` / `title_key` sont des clés i18n ; `kwargs` leur formatage.
    """
    lang = get_lang(ctx)
    view = TranslateView(kind, key, kwargs, lang, title_key)
    # `ephemeral` n'existe que sur les Context/interactions : on ne le passe
    # que si demandé, pour rester compatible avec un simple salon.
    send_kwargs: dict = {"embed": view.render(), "view": view}
    if ephemeral:
        send_kwargs["ephemeral"] = True
    if allowed_mentions is not None:
        send_kwargs["allowed_mentions"] = allowed_mentions
    message = await ctx.send(**send_kwargs)
    view.message = message
    return message


async def reply_dm(
    user: discord.abc.User, lang_source, key: str, *, kind: str = "info",
    title_key: str | None = None, **kwargs,
) -> discord.Message | None:
    """Envoie un MP traduisible à `user`, dans la langue de `lang_source`.

    Renvoie None si le MP échoue (MP fermés). `lang_source` est un serveur /
    contexte / id servant à résoudre la langue par défaut.
    """
    lang = get_lang(lang_source)
    view = TranslateView(kind, key, kwargs, lang, title_key)
    try:
        message = await user.send(embed=view.render(), view=view)
    except (discord.HTTPException, discord.Forbidden):
        return None
    view.message = message
    return message
