"""Commande `membercount` : nombre de membres du serveur."""
from discord.ext import commands

from utils import replies


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
        await replies.reply(
            ctx, "mc.desc", kind="success", title_key="mc.title",
            total=guild.member_count, humans=humans, bots=bots,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberCount(bot))
