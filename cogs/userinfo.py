"""Commande `userinfo` : affiche toutes les informations d'un utilisateur."""
import discord
from discord.ext import commands

from utils import replies
from utils.i18n import t_lang

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

        color = member.color if member.color.value else None
        spec = replies.Embed("info", color=color)
        spec.title("ui.title", user=str(member))
        spec.thumbnail(member.display_avatar.url)

        # Identité.
        spec.field("ui.name", str(member))
        spec.field_fn("ui.nick",
                      lambda l, m=member: m.nick or t_lang(l, "ui.none"))
        spec.field("f.id", f"`{member.id}`")
        spec.field_fn(
            "ui.bot",
            lambda l, m=member: t_lang(l, "ui.yes" if m.bot else "ui.no"),
        )

        # Statut et activité.
        status_key = _STATUS_KEYS.get(member.status)
        spec.field_fn(
            "ui.status",
            lambda l, k=status_key, s=member.status: (
                t_lang(l, k) if k else str(s)),
        )
        if member.activity is not None:
            spec.field("ui.activity", str(member.activity.name))

        # Dates.
        spec.field("ui.created",
                   discord.utils.format_dt(member.created_at, style="F"),
                   inline=False)
        if member.joined_at is not None:
            spec.field("ui.joined",
                       discord.utils.format_dt(member.joined_at, style="F"),
                       inline=False)
        if member.premium_since is not None:
            spec.field("ui.boosting",
                       discord.utils.format_dt(member.premium_since, style="F"),
                       inline=False)

        # Rôles (hors @everyone).
        roles = [r.mention for r in reversed(member.roles)
                 if r.name != "@everyone"]
        spec.field_fn(
            "ui.roles",
            lambda l, r=roles: ", ".join(r) if r else t_lang(l, "ui.none"),
            inline=False, count=len(roles),
        )
        spec.field("ui.top_role", member.top_role.mention)
        spec.footer("f.requested_by", user=str(ctx.author))
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserInfo(bot))
