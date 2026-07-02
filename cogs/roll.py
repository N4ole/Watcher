"""Commande `roll` : lance des dés au format NdM (ex: 2d6)."""
import random
import re

import discord
from discord.ext import commands

from utils.i18n import t

_DICE_RE = re.compile(r"^\s*(\d*)\s*d\s*(\d+)\s*$", re.IGNORECASE)


class Roll(commands.Cog):
    """Lancer de dés."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="roll",
        description="Lance des dés au format NdM (ex: 2d6, d20).",
    )
    async def roll(self, ctx: commands.Context, des: str = "1d6") -> None:
        match = _DICE_RE.match(des)
        if not match:
            await ctx.send(t(ctx, "roll.bad"))
            return

        count = int(match.group(1) or 1)
        faces = int(match.group(2))
        if not (1 <= count <= 100) or not (2 <= faces <= 1000):
            await ctx.send(t(ctx, "roll.limits"))
            return

        rolls = [random.randint(1, faces) for _ in range(count)]
        total = sum(rolls)
        detail = " + ".join(map(str, rolls)) if count > 1 else str(total)
        await ctx.send(f"🎲 **{des}** → {detail}" + (f" = **{total}**" if count > 1 else ""))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roll(bot))
