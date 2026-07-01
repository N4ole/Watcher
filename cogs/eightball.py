"""Commande `8ball` : boule magique qui répond à une question."""
import random

from discord.ext import commands

_ANSWERS = [
    "Oui, c'est certain.", "Sans aucun doute.", "Oui, absolument.",
    "C'est probable.", "Les signes disent oui.", "Peut-être.",
    "Difficile à dire, réessaie.", "Je ne peux pas prédire ça maintenant.",
    "Ne compte pas dessus.", "Ma réponse est non.", "Très douteux.",
    "C'est non.",
]


class EightBall(commands.Cog):
    """La boule magique."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="8ball",
        description="Pose une question à la boule magique.",
    )
    async def eightball(self, ctx: commands.Context, *, question: str) -> None:
        await ctx.send(f"🎱 {random.choice(_ANSWERS)}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EightBall(bot))
