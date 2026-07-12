"""Réponses du bot : embeds français centralisés.

Toutes les réponses passent par `reply()` / `reply_rich()` / `reply_dm()`, qui
envoient un embed rendu en **français** (le bot est unilingue). Point d'entrée
unique pour garder un rendu cohérent sur tout le bot.

Deux niveaux :
  - `reply(ctx, key, kind=...)`   : embed simple (une description + titre).
  - `reply_rich(ctx, Embed()...)` : embed riche multi-champs (spec `Embed`).
"""
import discord

import config
from utils import embeds
from utils.i18n import t

# Couleur d'embed par type (repli quand une spec `Embed` ne précise rien).
_KIND_COLOR = {
    "success": embeds.COLOR_SUCCESS,
    "error": embeds.COLOR_ERROR,
    "info": embeds.COLOR_INFO,
    "warn": embeds.COLOR_WARN,
    "fun": embeds.COLOR_FUN,
}


class Embed:
    """Spécification d'embed riche, rendue en français via `render()`.

    Les libellés (titre, description, noms de champs, pied de page) sont des
    **clés i18n** ; les valeurs de champ sont soit des données littérales
    (mentions, nombres, dates), soit des clés i18n (`field_t`), soit calculées
    (`field_fn` / `desc_fn`). `render()` produit un `discord.Embed`.
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
        """Titre littéral (donnée, non traduite — ex. nom du bot/serveur)."""
        self._title_literal = text
        return self

    def desc(self, key: str, **kwargs) -> "Embed":
        self._desc = (key, kwargs)
        return self

    def desc_text(self, text: str) -> "Embed":
        """Description littérale (donnée)."""
        self._desc_literal = text
        return self

    def desc_fn(self, fn) -> "Embed":
        """Description calculée : `fn() -> str`."""
        self._desc_fn = fn
        return self

    def field(self, name_key: str, value: str, *, inline: bool = True,
              **name_kwargs) -> "Embed":
        """Champ dont la valeur est une donnée littérale."""
        self._fields.append((name_key, name_kwargs, value, None, inline))
        return self

    def field_t(self, name_key: str, value_key: str, *, inline: bool = True,
                name_kwargs: dict | None = None, **value_kwargs) -> "Embed":
        """Champ dont la valeur est elle-même une clé i18n."""
        self._fields.append(
            (name_key, name_kwargs or {}, value_key, value_kwargs, inline)
        )
        return self

    def field_fn(self, name_key: str, value_fn, *, inline: bool = True,
                 **name_kwargs) -> "Embed":
        """Champ dont la valeur est calculée : `value_fn() -> str`.

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

    def render(self) -> discord.Embed:
        color = self.color or _KIND_COLOR.get(self.kind, embeds.COLOR_INFO)
        embed = discord.Embed(color=color, timestamp=self._timestamp)
        if self._title:
            embed.title = t(None, self._title[0], **self._title[1])
        elif self._title_literal is not None:
            embed.title = self._title_literal
        if self._desc:
            embed.description = t(None, self._desc[0], **self._desc[1])
        elif self._desc_fn is not None:
            embed.description = self._desc_fn()
        elif self._desc_literal is not None:
            embed.description = self._desc_literal
        for name_key, name_kwargs, value, value_kwargs, inline in self._fields:
            name = t(None, name_key, **name_kwargs)
            if callable(value):                 # field_fn : valeur calculée
                rendered = value()
            elif value_kwargs is not None:       # field_t : valeur = clé i18n
                rendered = t(None, value, **value_kwargs)
            else:                                # field : valeur littérale
                rendered = value
            embed.add_field(name=name, value=rendered, inline=inline)
        if self._footer:
            embed.set_footer(text=t(None, self._footer[0], **self._footer[1]))
        else:
            suffix = f"v{config.VERSION}" + (" bêta" if config.BETA else "")
            embed.set_footer(text=f"Watcher · {suffix}")
        if self._thumb:
            embed.set_thumbnail(url=self._thumb)
        if self._image:
            embed.set_image(url=self._image)
        return embed


def _simple_embed(kind: str, key: str, kwargs: dict,
                  title_key: str | None) -> discord.Embed:
    builder = getattr(embeds, kind, embeds.info)
    title = t(None, title_key, **kwargs) if title_key else None
    return builder(t(None, key, **kwargs), title=title)


async def _send(ctx, embed, *, ephemeral, allowed_mentions):
    send_kwargs: dict = {"embed": embed}
    if ephemeral:
        send_kwargs["ephemeral"] = True
    if allowed_mentions is not None:
        send_kwargs["allowed_mentions"] = allowed_mentions
    return await ctx.send(**send_kwargs)


async def reply(
    ctx, key: str, *, kind: str = "info", title_key: str | None = None,
    ephemeral: bool = False, allowed_mentions: discord.AllowedMentions | None = None,
    **kwargs,
) -> discord.Message | None:
    """Réponse simple (embed : description + titre optionnel), en français."""
    return await _send(
        ctx, _simple_embed(kind, key, kwargs, title_key),
        ephemeral=ephemeral, allowed_mentions=allowed_mentions,
    )


async def reply_rich(
    ctx, spec: Embed, *, ephemeral: bool = False,
    allowed_mentions: discord.AllowedMentions | None = None,
) -> discord.Message | None:
    """Réponse riche à partir d'une spec `Embed` multi-champs, en français."""
    return await _send(
        ctx, spec.render(), ephemeral=ephemeral, allowed_mentions=allowed_mentions,
    )


async def reply_dm(
    user: discord.abc.User, lang_source, key: str, *, kind: str = "info",
    title_key: str | None = None, spec: Embed | None = None, **kwargs,
) -> discord.Message | None:
    """MP à `user`, en français. `lang_source` est conservé par compatibilité.

    Renvoie None si le MP échoue (MP fermés). Fournir `spec` pour un embed riche.
    """
    embed = spec.render() if spec is not None else \
        _simple_embed(kind, key, kwargs, title_key)
    try:
        return await user.send(embed=embed)
    except (discord.HTTPException, discord.Forbidden):
        return None
