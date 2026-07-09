"""Commande admin `kick` : expulse un utilisateur du serveur, avec raison."""
import logging

import discord
from discord.ext import commands

from utils import checks, replies, storage
from utils.i18n import t, t_lang

log = logging.getLogger("action")


class Kick(commands.Cog):
    """Expulsion d'utilisateurs (permission « Expulser des membres »)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Expulse un utilisateur du serveur (avec raison).",
    )
    @checks.kick_perms()
    async def kick(
        self, ctx: commands.Context, member: discord.Member,
        *, raison: str | None = None,
    ) -> None:
        reason = raison or t(ctx, "mod.no_reason")

        # Garde-fous : soi-même et hiérarchie des rôles.
        if member.id == ctx.author.id:
            await replies.reply(ctx, "kick.self", kind="error")
            return
        if not checks.can_act_on(ctx.author, member):
            await replies.reply(ctx, "kick.hierarchy", kind="error")
            return

        # Prévenir l'utilisateur en MP AVANT l'expulsion (après, le bot ne
        # partage plus forcément de serveur avec lui). Sans invitation.
        dm_spec = (
            replies.Embed("warn", color=discord.Color.orange())
            .title("kick.dm_title")
            .desc("kick.dm_desc", server=ctx.guild.name)
            .field("mod.reason_label", reason, inline=False)
        )
        dm_sent = await replies.reply_dm(member, ctx.guild, "", spec=dm_spec) \
            is not None

        try:
            await member.kick(reason=f"{ctx.author} : {reason}")
        except discord.Forbidden:
            await replies.reply(ctx, "kick.forbidden", kind="error")
            return
        except discord.HTTPException as exc:
            await replies.reply(ctx, "kick.failed", kind="error", error=str(exc))
            return

        storage.add_modlog(
            ctx.guild.id, member.id, "kick", ctx.author.id, detail=reason
        )
        log.info(
            "Kick — %s (%s) expulsé par %s (%s) sur %s (%s) : %s",
            member, member.id, ctx.author, ctx.author.id,
            ctx.guild.name, ctx.guild.id, reason,
        )
        spec = replies.Embed("success").desc_fn(
            lambda l: t_lang(l, "kick.done", user=str(member), reason=reason)
            + ("" if dm_sent else "\n" + t_lang(l, "mod.dm_failed"))
        )
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Kick(bot))
