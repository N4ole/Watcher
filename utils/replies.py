"""Réponses traduisibles : rendu i18n + bouton de traduction (centralisé).

Toutes les réponses du bot passent par `reply()` / `reply_rich()` / `reply_dm()`,
qui envoient un embed rendu dans la langue par défaut du serveur (français par
défaut) et attachent un **bouton de traduction**. Un clic bascule le message
entre français et anglais **en place**, sans nouveau message.

Le bouton affiche le drapeau de l'**autre** langue :
  - message en français  -> bouton 🇬🇧 (clique pour passer en anglais) ;
  - message en anglais   -> bouton 🇫🇷 (clique pour repasser en français).

Comme la traduction reconstruit le message à partir de ses **clés i18n** (et non
en traduisant du texte libre), toute réponse qui passe par ce module bénéficie
automatiquement du bouton — actuelle ou future.

Deux niveaux :
  - `reply(ctx, key, kind=...)`      : embed simple (une description + titre).
  - `reply_rich(ctx, Embed()...)`    : embed riche multi-champs (spec `Embed`).
"""
from typing import Callable

import discord

import config
from utils import embeds
from utils.i18n import get_lang, other_lang, t_lang

# Bouton = drapeau de la langue vers laquelle on peut basculer.
_FLAG = {"fr": "🇬🇧", "en": "🇫🇷"}

# Durée de vie du bouton (24 h) : au-delà, il est retiré du message.
_TIMEOUT = 86400

# Couleur d'embed par type (repli quand une spec `Embed` ne précise rien).
_KIND_COLOR = {
    "success": embeds.COLOR_SUCCESS,
    "error": embeds.COLOR_ERROR,
    "info": embeds.COLOR_INFO,
    "warn": embeds.COLOR_WARN,
    "fun": embeds.COLOR_FUN,
}


class Embed:
    """Spécification d'embed **traduisible**, rendue à la volée dans une langue.

    Les libellés (titre, description, noms de champs, pied de page, titre de
    champ) sont des **clés i18n** ; les valeurs de champ sont soit des données
    littérales (langue-neutres : mentions, nombres, dates), soit des clés i18n
    (`field_t`). `render(lang)` produit un `discord.Embed` dans la langue voulue.
    """

    def __init__(self, kind: str = "info", *, color: discord.Color | None = None):
        self.kind = kind
        self.color = color
        self._title: tuple | None = None
        self._title_literal: str | None = None
        self._desc: tuple | None = None
        self._desc_literal: str | None = None
        self._desc_fn = None
        self._fields: list[tuple] = []
        self._footer: tuple | None = None
        self._thumb: str | None = None
        self._image: str | None = None
        self._timestamp = None

    def title(self, key: str, **kwargs) -> "Embed":
        self._title = (key, kwargs)
        return self

    def title_text(self, text: str) -> "Embed":
        """Titre littéral (donnée, non traduit — ex. nom du bot/serveur)."""
        self._title_literal = text
        return self

    def desc(self, key: str, **kwargs) -> "Embed":
        self._desc = (key, kwargs)
        return self

    def desc_text(self, text: str) -> "Embed":
        """Description littérale (donnée, non traduite)."""
        self._desc_literal = text
        return self

    def desc_fn(self, fn) -> "Embed":
        """Description calculée par langue : `fn(lang) -> str`."""
        self._desc_fn = fn
        return self

    def field(self, name_key: str, value: str, *, inline: bool = True,
              **name_kwargs) -> "Embed":
        """Champ dont la valeur est une donnée littérale (non traduite)."""
        self._fields.append((name_key, name_kwargs, value, None, inline))
        return self

    def field_t(self, name_key: str, value_key: str, *, inline: bool = True,
                name_kwargs: dict | None = None, **value_kwargs) -> "Embed":
        """Champ dont la valeur est elle-même une clé i18n (traduite)."""
        self._fields.append(
            (name_key, name_kwargs or {}, value_key, value_kwargs, inline)
        )
        return self

    def field_fn(self, name_key: str, value_fn, *, inline: bool = True,
                 **name_kwargs) -> "Embed":
        """Champ dont la valeur est calculée par langue : `value_fn(lang) -> str`.

        Utile quand la valeur mélange des libellés traduits et des données
        (ex. liste « protection : activé/désactivé »)."""
        self._fields.append((name_key, name_kwargs, value_fn, None, inline))
        return self

    def footer(self, key: str, **kwargs) -> "Embed":
        self._footer = (key, kwargs)
        return self

    def thumbnail(self, url: str | None) -> "Embed":
        self._thumb = url
        return self

    def image(self, url: str | None) -> "Embed":
        self._image = url
        return self

    def timestamp(self, dt) -> "Embed":
        self._timestamp = dt
        return self

    def render(self, lang: str) -> discord.Embed:
        color = self.color or _KIND_COLOR.get(self.kind, embeds.COLOR_INFO)
        embed = discord.Embed(color=color, timestamp=self._timestamp)
        if self._title:
            embed.title = t_lang(lang, self._title[0], **self._title[1])
        elif self._title_literal is not None:
            embed.title = self._title_literal
        if self._desc:
            embed.description = t_lang(lang, self._desc[0], **self._desc[1])
        elif self._desc_fn is not None:
            embed.description = self._desc_fn(lang)
        elif self._desc_literal is not None:
            embed.description = self._desc_literal
        for name_key, name_kwargs, value, value_kwargs, inline in self._fields:
            name = t_lang(lang, name_key, **name_kwargs)
            if callable(value):                 # field_fn : valeur par langue
                rendered = value(lang)
            elif value_kwargs is not None:       # field_t : valeur = clé i18n
                rendered = t_lang(lang, value, **value_kwargs)
            else:                                # field : valeur littérale
                rendered = value
            embed.add_field(name=name, value=rendered, inline=inline)
        if self._footer:
            embed.set_footer(text=t_lang(lang, self._footer[0],
                                         **self._footer[1]))
        else:
            suffix = f"v{config.VERSION}" + (" bêta" if config.BETA else "")
            embed.set_footer(text=f"Watcher · {suffix}")
        if self._thumb:
            embed.set_thumbnail(url=self._thumb)
        if self._image:
            embed.set_image(url=self._image)
        return embed


class TranslateView(discord.ui.View):
    """Bouton de traduction : rend le message via une fonction `lang -> Embed`."""

    def __init__(self, render_fn: Callable[[str], discord.Embed], lang: str) -> None:
        super().__init__(timeout=_TIMEOUT)
        self._render = render_fn
        self.lang = lang
        self.message: discord.Message | None = None
        self.translate.emoji = _FLAG[lang]

    def render(self) -> discord.Embed:
        return self._render(self.lang)

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def translate(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.lang = other_lang(self.lang)
        button.emoji = _FLAG[self.lang]
        await interaction.response.edit_message(embed=self.render(), view=self)

    async def on_timeout(self) -> None:
        if self.message is not None:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass


def _simple_renderer(
    kind: str, key: str, kwargs: dict, title_key: str | None
) -> Callable[[str], discord.Embed]:
    def render(lang: str) -> discord.Embed:
        builder = getattr(embeds, kind, embeds.info)
        title = t_lang(lang, title_key, **kwargs) if title_key else None
        return builder(t_lang(lang, key, **kwargs), title=title)
    return render


async def _send(ctx, render_fn, *, ephemeral, allowed_mentions,
                extra_view_items=None):
    lang = get_lang(ctx)
    view = TranslateView(render_fn, lang)
    if extra_view_items:
        for item in extra_view_items:
            view.add_item(item)
    send_kwargs: dict = {"embed": view.render(), "view": view}
    if ephemeral:
        send_kwargs["ephemeral"] = True
    if allowed_mentions is not None:
        send_kwargs["allowed_mentions"] = allowed_mentions
    message = await ctx.send(**send_kwargs)
    view.message = message
    return message


async def reply(
    ctx, key: str, *, kind: str = "info", title_key: str | None = None,
    ephemeral: bool = False, allowed_mentions: discord.AllowedMentions | None = None,
    **kwargs,
) -> discord.Message | None:
    """Réponse traduisible simple (embed : description + titre optionnel)."""
    return await _send(
        ctx, _simple_renderer(kind, key, kwargs, title_key),
        ephemeral=ephemeral, allowed_mentions=allowed_mentions,
    )


async def reply_rich(
    ctx, spec: Embed, *, ephemeral: bool = False,
    allowed_mentions: discord.AllowedMentions | None = None,
) -> discord.Message | None:
    """Réponse traduisible riche à partir d'une spec `Embed` multi-champs."""
    return await _send(
        ctx, spec.render, ephemeral=ephemeral,
        allowed_mentions=allowed_mentions,
    )


async def reply_dm(
    user: discord.abc.User, lang_source, key: str, *, kind: str = "info",
    title_key: str | None = None, spec: Embed | None = None, **kwargs,
) -> discord.Message | None:
    """MP traduisible à `user`, dans la langue de `lang_source`.

    Renvoie None si le MP échoue (MP fermés). Fournir `spec` pour un embed riche.
    """
    lang = get_lang(lang_source)
    render_fn = spec.render if spec is not None else \
        _simple_renderer(kind, key, kwargs, title_key)
    view = TranslateView(render_fn, lang)
    try:
        message = await user.send(embed=view.render(), view=view)
    except (discord.HTTPException, discord.Forbidden):
        return None
    view.message = message
    return message
