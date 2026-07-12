"""Commande `8ball` : boule magique qui répond à une question (embed)."""
import random

from discord.ext import commands

from utils import replies
from utils.i18n import EIGHTBALL


def _answer(idx: int) -> str:
    return EIGHTBALL[idx % len(EIGHTBALL)]


class EightBall(commands.Cog):
    """La boule magique."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="8ball",
        description="Pose une question à la boule magique.",
    )
    async def eightball(self, ctx: commands.Context, *, question: str) -> None:
        # Indice figé : la réponse reste « la même » quand on traduit le message
        # (on ne re-tire pas au sort à chaque bascule de langue).
        idx = random.randrange(len(EIGHTBALL))
        spec = (
            replies.Embed("fun")
            .title("8ball.title")
            .desc_text(f"🎱 {_answer(idx)}")
            .field("8ball.question", question[:1024], inline=False)
        )
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EightBall(bot))
