"""Gestionnaire d'erreurs global : messages clairs, permissions manquantes."""
import logging

from discord.ext import commands

import config
from utils.i18n import get_lang, t

log = logging.getLogger(__name__)

# Traduction des permissions Discord (fr / en).
_PERMS = {
    "administrator": ("Administrateur", "Administrator"),
    "manage_messages": ("Gérer les messages", "Manage Messages"),
    "manage_channels": ("Gérer les salons", "Manage Channels"),
    "manage_roles": ("Gérer les rôles", "Manage Roles"),
    "manage_guild": ("Gérer le serveur", "Manage Server"),
    "kick_members": ("Expulser des membres", "Kick Members"),
    "ban_members": ("Bannir des membres", "Ban Members"),
    "moderate_members": ("Exclure des membres (timeout)", "Timeout Members"),
    "manage_nicknames": ("Gérer les pseudos", "Manage Nicknames"),
    "mention_everyone": ("Mentionner @everyone", "Mention @everyone"),
    "view_audit_log": ("Voir les logs d'audit", "View Audit Log"),
}


def _perms(perms: list[str], lang: str) -> str:
    idx = 1 if lang == "en" else 0
    return ", ".join(
        _PERMS.get(p, (p.replace("_", " "),) * 2)[idx] for p in perms
    )


class Errors(commands.Cog):
    """Traite les erreurs de commandes de façon centralisée."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        # On laisse la main aux gestionnaires locaux (@cmd.error) s'ils existent.
        if ctx.command is not None and ctx.command.has_error_handler():
            return
        if isinstance(error, commands.CommandNotFound):
            return

        lang = get_lang(ctx)
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(t(ctx, "error.missing_perms",
                             perms=_perms(error.missing_permissions, lang)))
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(t(ctx, "error.bot_missing_perms",
                             perms=_perms(error.missing_permissions, lang)))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(t(ctx, "error.no_dm"))
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(t(ctx, "error.dm_only"))
        elif isinstance(error, commands.CheckFailure):
            message = str(error) or t(ctx, "error.check_failure")
            await ctx.send(f"⛔ {message}" if str(error) else message)
        elif isinstance(error, commands.MissingRequiredArgument):
            usage = (
                f"{config.PREFIX}{ctx.command.qualified_name} "
                f"{ctx.command.signature}"
            )
            await ctx.send(t(ctx, "error.missing_argument", usage=usage))
        elif isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            await ctx.send(t(ctx, "error.member_not_found"))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(t(ctx, "error.bad_argument", error=error))
        else:
            log.exception(
                "Erreur non gérée dans la commande %s",
                ctx.command, exc_info=error,
            )
            await ctx.send(t(ctx, "error.generic"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
