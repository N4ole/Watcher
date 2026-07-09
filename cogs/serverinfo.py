"""Commande `serverinfo` : informations sur le serveur."""
import discord
from discord.ext import commands

from utils import replies


class ServerInfo(commands.Cog):
    """Informations détaillées sur le serveur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="serverinfo",
        description="Affiche les informations du serveur.",
    )
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        bots = sum(1 for m in guild.members if m.bot) if guild.members else 0
        humans = (guild.member_count or 0) - bots

        spec = replies.Embed("info").title_text(guild.name)
        if guild.icon:
            spec.thumbnail(guild.icon.url)
        spec.field("f.id", f"`{guild.id}`")
        spec.field("f.owner", guild.owner.mention if guild.owner else "?")
        spec.field("f.created",
                   discord.utils.format_dt(guild.created_at, style="D"))
        spec.field_t("f.members", "si.members_val",
                     total=guild.member_count, humans=humans, bots=bots)
        spec.field("f.channels", str(len(guild.channels)))
        spec.field("f.roles", str(len(guild.roles)))
        spec.field_t("f.boosts", "si.boosts_val",
                     count=guild.premium_subscription_count,
                     tier=guild.premium_tier)
        spec.field("f.emojis", str(len(guild.emojis)))
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerInfo(bot))
