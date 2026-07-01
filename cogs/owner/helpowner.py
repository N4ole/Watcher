"""Commande owner `helpowner` (préfixe uniquement) : liste les commandes owner."""
import discord
from discord.ext import commands

from utils import checks
import config


class HelpOwner(commands.Cog):
    """Aide dédiée aux commandes d'owner."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _owner_commands(self) -> list[commands.Command]:
        return sorted(
            (
                cmd
                for cmd in self.bot.commands
                if cmd.module and cmd.module.startswith("cogs.owner")
            ),
            key=lambda c: c.qualified_name,
        )

    def _detail(self, command: commands.Command) -> discord.Embed:
        signature = command.signature.strip()
        usage = f"{config.PREFIX}{command.qualified_name}"
        if signature:
            usage += f" {signature}"
        embed = discord.Embed(
            title=f"👑 {config.PREFIX}{command.qualified_name}",
            description=command.description or command.help or "Pas de description.",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        embed.add_field(
            name="Disponible en",
            value="préfixe `" + config.PREFIX + "` et slash `/`"
            if isinstance(command, commands.HybridCommand)
            else "préfixe uniquement",
            inline=True,
        )
        if command.aliases:
            embed.add_field(
                name="Alias",
                value=", ".join(f"`{a}`" for a in command.aliases),
                inline=True,
            )
        embed.add_field(
            name="En message privé",
            value="✅ oui (réservé aux owners)",
            inline=True,
        )
        embed.set_footer(
            text="⟨ ⟩ = obligatoire · [ ] = facultatif · réservé aux owners"
        )
        return embed

    @commands.command(name="helpowner")
    @checks.is_owner()
    async def helpowner(
        self, ctx: commands.Context, commande: str | None = None
    ) -> None:
        owner_commands = self._owner_commands()

        # Détail d'une commande owner précise.
        if commande:
            name = commande.lower().lstrip(config.PREFIX).strip()
            command = self.bot.get_command(name)
            if command is None or command not in owner_commands:
                await ctx.send(f"❌ Commande owner introuvable : `{commande}`")
                return
            await ctx.send(embed=self._detail(command))
            return

        embed = discord.Embed(
            title="👑 Commandes d'owner",
            description=(
                f"Préfixe : `{config.PREFIX}` — commandes réservées aux owners "
                f"du bot.\nDétail d'une commande : `{config.PREFIX}helpowner "
                "<commande>`."
            ),
            color=discord.Color.gold(),
        )
        for cmd in owner_commands:
            description = cmd.description or cmd.help or "Pas de description."
            signature = cmd.signature.strip()
            usage = f"{config.PREFIX}{cmd.qualified_name}"
            if signature:
                usage += f" {signature}"
            embed.add_field(
                name=f"`{usage}`",
                value=description,
                inline=False,
            )
        embed.set_footer(text=f"{len(owner_commands)} commande(s) d'owner")
        await ctx.send(embed=embed)

    @helpowner.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpOwner(bot))
