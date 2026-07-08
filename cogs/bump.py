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

from utils import appchoices, checks, embeds, storage
from utils.duration import human
from utils.i18n import t

log = logging.getLogger("action")

COOLDOWN = 6 * 3600  # 6 heures, en secondes

# Clés de réglage (guild_settings), persistées.
K_ENABLED = "bump_enabled"
K_CHANNEL = "bump_channel"
K_LAST = "bump_last"

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
            state = t(ctx, "bump.st_on", channel=channel.mention) if (
                enabled and channel) else t(ctx, "bump.st_off")
            await ctx.send(embed=embeds.info(state, title=t(ctx, "bump.st_title")))
            return

        value = etat.lower()
        if value in _ON:
            if salon is not None:
                storage.set_setting(ctx.guild.id, K_ENABLED, True)
                storage.set_setting(ctx.guild.id, K_CHANNEL, salon.id)
                await ctx.send(embed=embeds.success(
                    t(ctx, "bump.enabled", channel=salon.mention)))
            else:
                # Demande à l'admin de choisir le salon de réception.
                await ctx.send(
                    embed=embeds.info(t(ctx, "bump.choose_channel")),
                    view=BumpChannelView(ctx.author.id),
                )
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, K_ENABLED, False)
            await ctx.send(embed=embeds.info(t(ctx, "bump.disabled")))
        else:
            await ctx.send(embed=embeds.error(
                t(ctx, "toggle.usage", name="bumpenable")))

    # ------------------------------------------------------------------ #
    # Bump
    # ------------------------------------------------------------------ #
    def _ad_embed(self, guild: discord.Guild, invite: str | None) -> discord.Embed:
        embed = discord.Embed(
            title=f"📢 {guild.name}",
            description=guild.description or t(guild, "bump.ad_no_desc"),
            color=discord.Color.blurple(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(
            name=t(guild, "bump.ad_members"),
            value=str(guild.member_count or 0), inline=True,
        )
        if invite:
            embed.add_field(name=t(guild, "bump.ad_invite"),
                            value=invite, inline=False)
        embed.set_footer(text=t(guild, "bump.ad_footer"))
        return embed

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
            await ctx.send(embed=embeds.error(t(ctx, "bump.not_enabled")))
            return

        # Cooldown de 6 h par serveur.
        last = float(storage.get_setting(ctx.guild.id, K_LAST, 0) or 0)
        remaining = COOLDOWN - (time.time() - last)
        if remaining > 0:
            await ctx.send(embed=embeds.warn(
                t(ctx, "bump.cooldown",
                  time=human(timedelta(seconds=int(remaining))))))
            return

        await ctx.defer()
        invite = await _resolve_invite(ctx.guild)
        ad = self._ad_embed(ctx.guild, invite)

        # Diffuse aux autres serveurs participants.
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
                await channel.send(embed=ad)
                sent += 1
            except discord.HTTPException:
                continue

        # Cooldown consommé une fois le bump effectué.
        storage.set_setting(ctx.guild.id, K_LAST, time.time())
        log.info("Bump de %s (%s) par %s — %d serveur(s) touché(s)",
                 ctx.guild.name, ctx.guild.id, ctx.author, sent)

        if sent:
            await ctx.send(embed=embeds.success(t(ctx, "bump.done", count=sent)))
        else:
            await ctx.send(embed=embeds.info(t(ctx, "bump.done_none")))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bump(bot))
