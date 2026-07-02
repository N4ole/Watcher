"""Commande `uptime` : affiche depuis combien de temps le bot tourne."""
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.i18n import t


def _format_uptime(delta) -> str:
    total = int(delta.total_seconds())
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}j")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


class Uptime(commands.Cog):
    """Temps de fonctionnement du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="uptime",
        description="Affiche depuis combien de temps le bot tourne.",
    )
    async def uptime(self, ctx: commands.Context) -> None:
        delta = datetime.now(timezone.utc) - self.bot.start_time
        embed = discord.Embed(
            title=t(ctx, "uptime.title"),
            description=t(ctx, "uptime.desc", duration=_format_uptime(delta)),
            color=discord.Color.green(),
        )
        embed.add_field(
            name=t(ctx, "uptime.started"),
            value=discord.utils.format_dt(self.bot.start_time, style="F"),
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Uptime(bot))
