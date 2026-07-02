"""Commande `coinflip` : pile ou face."""
import random

from discord.ext import commands

from utils.i18n import t


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
        key = random.choice(["coin.heads", "coin.tails"])
        await ctx.send(t(ctx, key))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoinFlip(bot))
