"""Gestionnaire d'erreurs global : messages clairs, permissions manquantes."""
import logging

from discord.ext import commands

import config

log = logging.getLogger(__name__)

# Traduction des permissions Discord en français lisible.
_PERMS_FR = {
    "administrator": "Administrateur",
    "manage_messages": "Gérer les messages",
    "manage_channels": "Gérer les salons",
    "manage_roles": "Gérer les rôles",
    "manage_guild": "Gérer le serveur",
    "kick_members": "Expulser des membres",
    "ban_members": "Bannir des membres",
    "moderate_members": "Exclure des membres (timeout)",
    "manage_nicknames": "Gérer les pseudos",
    "mention_everyone": "Mentionner @everyone",
    "view_audit_log": "Voir les logs d'audit",
}


def _fr_perms(perms: list[str]) -> str:
    return ", ".join(_PERMS_FR.get(p, p.replace("_", " ")) for p in perms)


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
            await ctx.send(
                "⛔ Il te manque la permission suivante pour utiliser cette "
                f"commande : **{_fr_perms(error.missing_permissions)}**."
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                "⚠️ Il me manque la permission suivante pour exécuter cette "
                f"commande : **{_fr_perms(error.missing_permissions)}**."
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ Cette commande s'utilise sur un serveur.")
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("❌ Cette commande s'utilise en message privé.")
        elif isinstance(error, commands.CheckFailure):
            # Couvre notamment les commandes réservées aux owners.
            message = str(error) or "Tu n'as pas la permission d'utiliser cette commande."
            await ctx.send(f"⛔ {message}")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "❌ Argument manquant. Usage : "
                f"`{config.PREFIX}{ctx.command.qualified_name} "
                f"{ctx.command.signature}`"
            )
        elif isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            await ctx.send("❌ Utilisateur introuvable.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Argument invalide : {error}")
        else:
            log.exception(
                "Erreur non gérée dans la commande %s",
                ctx.command, exc_info=error,
            )
            await ctx.send("❌ Une erreur est survenue lors de l'exécution.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
