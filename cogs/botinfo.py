"""Commande `botinfo` : informations générales sur le bot."""
from datetime import datetime, timezone

import discord
from discord.ext import commands

import config
from utils.duration import human


class BotInfo(commands.Cog):
    """Présentation et statistiques du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="botinfo",
        description="Affiche des informations sur le bot.",
    )
    async def botinfo(self, ctx: commands.Context) -> None:
        uptime = datetime.now(timezone.utc) - self.bot.start_time
        members = sum((g.member_count or 0) for g in self.bot.guilds)

        embed = discord.Embed(
            title="🤖 ClaudeBot",
            description="Bot de modération et d'utilitaires.",
            color=discord.Color.blurple(),
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Version", value=config.VERSION, inline=True)
        embed.add_field(
            name="Serveurs", value=str(len(self.bot.guilds)), inline=True
        )
        embed.add_field(name="Membres", value=str(members), inline=True)
        embed.add_field(
            name="Ping", value=f"{round(self.bot.latency * 1000)} ms", inline=True
        )
        embed.add_field(name="Uptime", value=human(uptime), inline=True)
        embed.add_field(
            name="Commandes", value=str(len(self.bot.commands)), inline=True
        )
        embed.add_field(
            name="Préfixe", value=f"`{config.PREFIX}`", inline=True
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BotInfo(bot))
