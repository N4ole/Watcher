"""Gestionnaire d'erreurs global : messages clairs, permissions manquantes.

Note (audit Q1) : plusieurs cogs écoutent `on_command_error`, chacun avec un
rôle distinct et non redondant :
  - `errors`      (ici)          → message utilisateur clair et traduit ;
  - `errorreport` (owners)       → MP détaillé aux owners sur bug inattendu ;
  - `logs`        (salon Discord) → trace l'échec dans le salon de catégorie ;
  - `actionlog`                  → journalise l'échec (fichiers/console).
Les listeners d'un même événement coexistent volontairement.
"""
import logging

from discord.ext import commands

import config
from utils import checks, replies
from utils.i18n import t

log = logging.getLogger(__name__)


def _perms(source, perms: list[str]) -> str:
    """Traduit une liste de permissions Discord via i18n (clés `dperm.*`)."""
    labels = []
    for p in perms:
        key = f"dperm.{p}"
        label = t(source, key)
        labels.append(label if label != key else p.replace("_", " "))
    return ", ".join(labels)


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

        if isinstance(error, commands.MissingPermissions):
            await replies.reply(ctx, "error.missing_perms", kind="error",
                                 perms=_perms(ctx, error.missing_permissions))
        elif isinstance(error, commands.BotMissingPermissions):
            await replies.reply(ctx, "error.bot_missing_perms", kind="error",
                                 perms=_perms(ctx, error.missing_permissions))
        elif isinstance(error, commands.NoPrivateMessage):
            await replies.reply(ctx, "error.no_dm", kind="error")
        elif isinstance(error, commands.PrivateMessageOnly):
            await replies.reply(ctx, "error.dm_only", kind="error")
        elif isinstance(error, checks.OwnerOnly):
            await replies.reply(ctx, "error.owner_only", kind="error")
        elif isinstance(error, checks.ServerOwnerOnly):
            await replies.reply(ctx, "co.not_owner", kind="error")
        elif isinstance(error, commands.CheckFailure):
            # Message i18n uniquement : ne jamais relayer str(error) brut.
            await replies.reply(ctx, "error.check_failure", kind="error")
        elif isinstance(error, commands.MissingRequiredArgument):
            usage = (
                f"{config.PREFIX}{ctx.command.qualified_name} "
                f"{ctx.command.signature}"
            )
            await replies.reply(ctx, "error.missing_argument", kind="error",
                                 usage=usage)
        elif isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            await replies.reply(ctx, "error.member_not_found", kind="error")
        elif isinstance(error, commands.BadArgument):
            await replies.reply(ctx, "error.bad_argument", kind="error",
                                 error=str(error))
        else:
            log.exception(
                "Erreur non gérée dans la commande %s",
                ctx.command, exc_info=error,
            )
            await replies.reply(ctx, "error.generic", kind="error")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
