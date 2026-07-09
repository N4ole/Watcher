"""Système de bump inter-serveurs : `bumpenable` (admin) et `bump` (public).

Chaque serveur peut activer le système et choisir un salon de réception. La
commande `bump` diffuse une publicité du serveur (nom, icône, description,
invitation) dans le salon configuré de **tous les autres** serveurs
participants. Cooldown de 6 h par serveur. Tout est persisté dans les réglages
de serveur (`bump_enabled`, `bump_channel`, `bump_last`).
"""
import logging
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils import appchoices, checks, embeds, replies, storage
from utils.duration import human
from utils.i18n import t

log = logging.getLogger("action")

COOLDOWN = 6 * 3600  # 6 heures, en secondes

# Clés de réglage (guild_settings), persistées.
K_ENABLED = "bump_enabled"
K_CHANNEL = "bump_channel"
K_LAST = "bump_last"
K_COUNT = "bump_count"  # total de bumps du serveur (compteur persistant)

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}


async def _resolve_invite(guild: discord.Guild) -> str | None:
    """Renvoie un lien d'invitation permanent du serveur (ou en crée un)."""
    # 1) Réutilise une invitation permanente existante si possible.
    if guild.me.guild_permissions.manage_guild:
        try:
            for inv in await guild.invites():
                if inv.max_age == 0 and not inv.revoked:
                    return inv.url
        except discord.HTTPException:
            pass
    # 2) Sinon, en génère une (invitation permanente) sur un salon accessible.
    target = guild.system_channel
    if target is None or not target.permissions_for(guild.me).create_instant_invite:
        target = next(
            (c for c in guild.text_channels
             if c.permissions_for(guild.me).create_instant_invite),
            None,
        )
    if target is None:
        return None
    try:
        invite = await target.create_invite(
            max_age=0, unique=False, reason="Bump inter-serveurs"
        )
        return invite.url
    except discord.HTTPException:
        return None


class BumpChannelView(discord.ui.View):
    """Sélecteur de salon présenté à l'admin lors de l'activation."""

    def __init__(self, author_id: int) -> None:
        super().__init__(timeout=120)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                t(interaction.guild, "help.not_for_you"), ephemeral=True
            )
            return False
        return True

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Salon de réception des pubs / Ads channel",
        min_values=1, max_values=1,
    )
    async def pick(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ) -> None:
        guild = interaction.guild
        channel = guild.get_channel(select.values[0].id)
        if channel is None:
            await interaction.response.edit_message(
                embed=embeds.error(t(guild, "bump.bad_channel")), view=None
            )
            return
        storage.set_setting(guild.id, K_ENABLED, True)
        storage.set_setting(guild.id, K_CHANNEL, channel.id)
        self.stop()
        await interaction.response.edit_message(
            embed=embeds.success(
                t(guild, "bump.enabled", channel=channel.mention)),
            view=None,
        )


class Bump(commands.Cog):
    """Bump inter-serveurs : publicité croisée entre serveurs participants."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ #
    # Activation / configuration
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="bumpenable",
        description="Active/désactive le système de bump (choix du salon).",
    )
    @app_commands.choices(etat=appchoices.onoff())
    @checks.admin()
    async def bumpenable(
        self, ctx: commands.Context, etat: str | None = None,
        salon: discord.TextChannel | None = None,
    ) -> None:
        # Sans argument : afficher l'état actuel.
        if etat is None:
            enabled = storage.get_setting(ctx.guild.id, K_ENABLED, False)
            chan_id = storage.get_setting(ctx.guild.id, K_CHANNEL)
            channel = ctx.guild.get_channel(chan_id) if chan_id else None
            if enabled and channel:
                await replies.reply(ctx, "bump.st_on", kind="info",
                                    title_key="bump.st_title",
                                    channel=channel.mention)
            else:
                await replies.reply(ctx, "bump.st_off", kind="info",
                                    title_key="bump.st_title")
            return

        value = etat.lower()
        if value in _ON:
            if salon is not None:
                storage.set_setting(ctx.guild.id, K_ENABLED, True)
                storage.set_setting(ctx.guild.id, K_CHANNEL, salon.id)
                await replies.reply(ctx, "bump.enabled", kind="success",
                                    channel=salon.mention)
            else:
                # Demande à l'admin de choisir le salon de réception (vue
                # dédiée : pas de bouton de traduction sur ce message-ci).
                await ctx.send(
                    embed=embeds.info(t(ctx, "bump.choose_channel")),
                    view=BumpChannelView(ctx.author.id),
                )
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, K_ENABLED, False)
            await replies.reply(ctx, "bump.disabled", kind="info")
        else:
            await replies.reply(ctx, "toggle.usage", kind="error",
                                name="bumpenable")

    # ------------------------------------------------------------------ #
    # Bump — rendu de la publicité
    # ------------------------------------------------------------------ #
    def _bot_invite(self) -> str:
        """Lien d'ajout du bot (bouton « Ajouter le bot »)."""
        return discord.utils.oauth_url(
            self.bot.user.id, scopes=("bot", "applications.commands")
        )

    def _ad_embed(
        self, source: discord.Guild, dest: discord.Guild,
        author: discord.abc.User, bump_count: int, when,
    ) -> discord.Embed:
        """Embed de pub, traduit dans la langue du serveur destinataire (`dest`).

        Les données décrivent le serveur `source` (celui qui bump) ; les
        libellés sont dans la langue de `dest` (i18n par serveur).
        """
        embed = discord.Embed(
            title=t(dest, "bump.ad_title", server=source.name),
            description=source.description or t(dest, "bump.ad_no_desc"),
            color=discord.Color.blurple(),
            timestamp=when,
        )
        if source.icon:
            embed.set_thumbnail(url=source.icon.url)
        embed.add_field(name=t(dest, "bump.f_id"),
                        value=f"`{source.id}`", inline=True)
        embed.add_field(name=t(dest, "bump.f_members"),
                        value=f"**{source.member_count or 0}**", inline=True)
        embed.add_field(name=t(dest, "bump.f_bumps"),
                        value=f"**{bump_count}**", inline=True)
        embed.add_field(name=t(dest, "bump.f_by"),
                        value=f"{author.mention} (`{author}`)", inline=False)
        embed.set_footer(text=t(dest, "bump.ad_footer"))
        return embed

    def _ad_view(self, dest: discord.Guild, invite: str) -> discord.ui.View:
        """Boutons « Rejoindre le serveur » et « Ajouter le bot » (liens)."""
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label=t(dest, "bump.btn_join"), emoji="🚀",
            style=discord.ButtonStyle.link, url=invite,
        ))
        view.add_item(discord.ui.Button(
            label=t(dest, "bump.btn_addbot"), emoji="⭐",
            style=discord.ButtonStyle.link, url=self._bot_invite(),
        ))
        return view

    @commands.hybrid_command(
        name="bump",
        description="Diffuse ton serveur aux autres serveurs participants.",
    )
    @commands.guild_only()
    async def bump(self, ctx: commands.Context) -> None:
        # Ignore silencieusement les bots (y compris le bot lui-même).
        if ctx.author.bot:
            return

        # Le système doit être activé sur ce serveur.
        if not storage.get_setting(ctx.guild.id, K_ENABLED, False):
            await replies.reply(ctx, "bump.not_enabled", kind="error")
            return

        # Cooldown de 6 h par serveur.
        last = float(storage.get_setting(ctx.guild.id, K_LAST, 0) or 0)
        remaining = COOLDOWN - (time.time() - last)
        if remaining > 0:
            await replies.reply(
                ctx, "bump.cooldown", kind="warn",
                time=human(timedelta(seconds=int(remaining))),
            )
            return

        await ctx.defer()

        # Invitation du serveur source (permanente si possible, sinon créée).
        # Sans invitation, la pub n'a pas de carte ni de bouton : on abandonne.
        invite = await _resolve_invite(ctx.guild)
        if invite is None:
            await replies.reply(ctx, "bump.no_invite", kind="error")
            return

        # Compteur de bumps du serveur (persistant), incrémenté à ce bump.
        bump_count = int(storage.get_setting(ctx.guild.id, K_COUNT, 0) or 0) + 1
        storage.set_setting(ctx.guild.id, K_COUNT, bump_count)
        now = discord.utils.utcnow()

        # Diffuse aux autres serveurs participants (dans leur langue).
        sent = 0
        for guild in self.bot.guilds:
            if guild.id == ctx.guild.id:
                continue
            if not storage.get_setting(guild.id, K_ENABLED, False):
                continue
            chan_id = storage.get_setting(guild.id, K_CHANNEL)
            channel = guild.get_channel(chan_id) if chan_id else None
            # Ignore les serveurs dont le salon a disparu ou est inaccessible.
            if channel is None or not hasattr(channel, "send"):
                continue
            if not channel.permissions_for(guild.me).send_messages:
                continue
            try:
                # `content=invite` : Discord déplie la carte d'invitation
                # (aperçu du serveur + bouton Rejoindre) ; l'embed suit dessous.
                await channel.send(
                    content=invite,
                    embed=self._ad_embed(ctx.guild, guild, ctx.author,
                                         bump_count, now),
                    view=self._ad_view(guild, invite),
                )
                sent += 1
            except discord.HTTPException:
                continue

        # Cooldown consommé une fois le bump effectué.
        storage.set_setting(ctx.guild.id, K_LAST, time.time())
        log.info("Bump de %s (%s) par %s — %d serveur(s) touché(s), total %d",
                 ctx.guild.name, ctx.guild.id, ctx.author, sent, bump_count)

        if sent:
            await replies.reply(ctx, "bump.done", kind="success",
                                count=sent, total=bump_count)
        else:
            await replies.reply(ctx, "bump.done_none", kind="info",
                                total=bump_count)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bump(bot))
