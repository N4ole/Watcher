"""Commande ping : affiche la latence du bot."""
from discord.ext import commands

from utils import replies


class Ping(commands.Cog):
    """Vérifie que le bot répond et mesure sa latence."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Affiche la latence du bot.")
    async def ping(self, ctx: commands.Context) -> None:
        latency_ms = round(self.bot.latency * 1000)
        await replies.reply(ctx, "ping.result", kind="success", ms=latency_ms)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))
