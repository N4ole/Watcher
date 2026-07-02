"""Commande `userinfo` : affiche toutes les informations d'un utilisateur."""
import discord
from discord.ext import commands

from utils.i18n import t

_STATUS_KEYS = {
    discord.Status.online: "status.online",
    discord.Status.idle: "status.idle",
    discord.Status.dnd: "status.dnd",
    discord.Status.offline: "status.offline",
}


class UserInfo(commands.Cog):
    """Informations détaillées sur un utilisateur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="userinfo",
        description="Affiche les informations d'un utilisateur.",
    )
    @commands.guild_only()
    async def userinfo(
        self, ctx: commands.Context, member: discord.Member = None
    ) -> None:
        member = member or ctx.author
        # Un membre résolu via une commande slash ne porte pas la présence :
        # on récupère la version en cache pour obtenir le vrai statut.
        member = ctx.guild.get_member(member.id) or member

        embed = discord.Embed(
            title=t(ctx, "ui.title", user=member),
            color=member.color if member.color.value else discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Identité.
        none = t(ctx, "ui.none")
        embed.add_field(name=t(ctx, "ui.name"), value=str(member), inline=True)
        embed.add_field(name=t(ctx, "ui.nick"),
                        value=member.nick or none, inline=True)
        embed.add_field(name=t(ctx, "f.id"), value=f"`{member.id}`", inline=True)
        embed.add_field(
            name=t(ctx, "ui.bot"),
            value=t(ctx, "ui.yes") if member.bot else t(ctx, "ui.no"),
            inline=True,
        )

        # Statut et activité.
        status_key = _STATUS_KEYS.get(member.status)
        status = t(ctx, status_key) if status_key else str(member.status)
        embed.add_field(name=t(ctx, "ui.status"), value=status, inline=True)
        if member.activity is not None:
            embed.add_field(
                name=t(ctx, "ui.activity"),
                value=str(member.activity.name), inline=True,
            )

        # Dates.
        embed.add_field(
            name=t(ctx, "ui.created"),
            value=discord.utils.format_dt(member.created_at, style="F"),
            inline=False,
        )
        if member.joined_at is not None:
            embed.add_field(
                name=t(ctx, "ui.joined"),
                value=discord.utils.format_dt(member.joined_at, style="F"),
                inline=False,
            )
        if member.premium_since is not None:
            embed.add_field(
                name=t(ctx, "ui.boosting"),
                value=discord.utils.format_dt(member.premium_since, style="F"),
                inline=False,
            )

        # Rôles (hors @everyone).
        roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
        embed.add_field(
            name=t(ctx, "ui.roles", count=len(roles)),
            value=", ".join(roles) if roles else none,
            inline=False,
        )
        embed.add_field(
            name=t(ctx, "ui.top_role"), value=member.top_role.mention, inline=True
        )

        embed.set_footer(text=t(ctx, "f.requested_by", user=ctx.author))
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserInfo(bot))
