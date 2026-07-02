"""Commande `8ball` : boule magique qui répond à une question."""
import random

from discord.ext import commands

from utils.i18n import EIGHTBALL, get_lang


class EightBall(commands.Cog):
    """La boule magique."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="8ball",
        description="Pose une question à la boule magique.",
    )
    async def eightball(self, ctx: commands.Context, *, question: str) -> None:
        answers = EIGHTBALL.get(get_lang(ctx), EIGHTBALL["fr"])
        await ctx.send(f"🎱 {random.choice(answers)}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EightBall(bot))
