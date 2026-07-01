"""Commande help : liste les commandes rangées par catégories."""
import discord
from discord.ext import commands

import config

# Catégorie et permission requise, par nom de cog.
#   nom_du_cog -> (catégorie, permission requise ou None)
_CATEGORIES = {
    "Watch": ("🛡️ Modération", "Administrateur"),
    "Confine": ("🛡️ Modération", "Administrateur"),
    "Mute": ("🛡️ Modération", "Administrateur"),
    "Warn": ("🛡️ Modération", "Administrateur"),
    "Clear": ("🛡️ Modération", "Gérer les messages"),
    "AntiBot": ("🛡️ Modération", "Administrateur"),
    "AntiRaid": ("🛡️ Modération", "Administrateur"),
    "AntiPub": ("🛡️ Modération", "Administrateur"),
    "AntiSpam": ("🛡️ Modération", "Administrateur"),
    "AntiInsulte": ("🛡️ Modération", "Administrateur"),
    "Protections": ("🛡️ Modération", "Administrateur"),
    "UserStatus": ("🛡️ Modération", "Administrateur"),
    "ContactOwner": ("👑 Propriétaire de serveur", "Propriétaire du serveur"),
}
_DEFAULT = ("🔧 Général", None)

# Ordre d'affichage des catégories.
_ORDER = ["🔧 Général", "🛡️ Modération", "👑 Propriétaire de serveur"]


class Help(commands.Cog):
    """Affiche la liste des commandes du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _category_of(self, command: commands.Command) -> tuple[str, str | None]:
        cog_name = command.cog.qualified_name if command.cog else ""
        return _CATEGORIES.get(cog_name, _DEFAULT)

    @commands.hybrid_command(
        name="help",
        description="Affiche la liste des commandes disponibles.",
    )
    async def help(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="📖 Aide",
            description=(
                f"Préfixe : `{config.PREFIX}` — les commandes sont aussi "
                "disponibles en slash `/`.\n"
                "🔒 = permission nécessaire."
            ),
            color=discord.Color.blurple(),
        )

        # Regroupe les commandes visibles par catégorie.
        grouped: dict[str, list[str]] = {}
        count = 0
        for command in sorted(self.bot.commands, key=lambda c: c.name):
            # On masque les commandes cachées et celles réservées aux owners.
            if command.hidden:
                continue
            if command.module and command.module.startswith("cogs.owner"):
                continue

            category, perm = self._category_of(command)
            description = command.description or "Pas de description."
            line = f"`{config.PREFIX}{command.name}` — {description}"
            if perm:
                line += f" 🔒 *{perm}*"
            grouped.setdefault(category, []).append(line)
            count += 1

        # Affiche les catégories dans l'ordre défini, puis les éventuelles autres.
        categories = _ORDER + [c for c in grouped if c not in _ORDER]
        for category in categories:
            if category in grouped:
                embed.add_field(
                    name=category,
                    value="\n".join(grouped[category]),
                    inline=False,
                )

        embed.set_footer(text=f"{count} commande(s) disponible(s)")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
