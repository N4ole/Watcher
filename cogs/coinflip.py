"""Commande `coinflip` : pile ou face."""
import random

from discord.ext import commands


class CoinFlip(commands.Cog):
    """Pile ou face."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="coinflip",
        aliases=["pileouface"],
        description="Lance une pièce : pile ou face.",
    )
    async def coinflip(self, ctx: commands.Context) -> None:
        result = random.choice(["🪙 Pile", "🪙 Face"])
        await ctx.send(result)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoinFlip(bot))
