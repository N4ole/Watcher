"""Commande `membercount` : nombre de membres du serveur."""
import discord
from discord.ext import commands


class MemberCount(commands.Cog):
    """Compteur de membres."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="membercount",
        description="Affiche le nombre de membres du serveur.",
    )
    @commands.guild_only()
    async def membercount(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        bots = sum(1 for m in guild.members if m.bot)
        humans = (guild.member_count or 0) - bots
        embed = discord.Embed(
            title="👥 Membres",
            description=(
                f"**{guild.member_count}** au total\n"
                f"👤 {humans} humains · 🤖 {bots} bots"
            ),
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberCount(bot))
