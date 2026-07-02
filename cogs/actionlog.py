"""Journalise chaque action du bot (qui, où, quand) dans la console/live."""
import logging

import discord
from discord.ext import commands

log = logging.getLogger("action")


def _where(ctx: commands.Context) -> str:
    if ctx.guild is None:
        return "MP"
    channel = getattr(ctx.channel, "name", "?")
    return f"#{channel} / {ctx.guild.name} ({ctx.guild.id})"


class ActionLog(commands.Cog):
    """Trace les commandes et événements importants du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context) -> None:
        params = " ".join(str(v) for v in ctx.kwargs.values()) if ctx.kwargs else ""
        via = "slash" if ctx.interaction is not None else "préfixe"
        log.info(
            "Commande /%s %s— par %s (%s) via %s dans %s",
            ctx.command.qualified_name, (params + " ") if params else "",
            ctx.author, ctx.author.id, via, _where(ctx),
        )

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        cmd = ctx.command.qualified_name if ctx.command else "?"
        log.warning(
            "Échec commande /%s par %s (%s) dans %s : %s",
            cmd, ctx.author, ctx.author.id, _where(ctx),
            type(error).__name__,
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        log.info(
            "Serveur rejoint : %s (%s) — %s membres",
            guild.name, guild.id, guild.member_count,
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        log.info("Serveur quitté : %s (%s)", guild.name, guild.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActionLog(bot))
