"""Commande `choose` : le bot choisit parmi des options séparées par « | »."""
import random

from discord.ext import commands

from utils.i18n import t


class Choose(commands.Cog):
    """Choix aléatoire parmi plusieurs options."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="choose",
        description="Choisit une option parmi plusieurs (séparées par « | »).",
    )
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        choices = [o.strip() for o in options.split("|") if o.strip()]
        if len(choices) < 2:
            await ctx.send(t(ctx, "choose.need"))
            return
        await ctx.send(t(ctx, "choose.result", choice=random.choice(choices)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Choose(bot))
