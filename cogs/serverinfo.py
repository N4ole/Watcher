"""Commande `serverinfo` : informations sur le serveur."""
import discord
from discord.ext import commands


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

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name="Propriétaire",
            value=guild.owner.mention if guild.owner else "?",
            inline=True,
        )
        embed.add_field(
            name="Créé le",
            value=discord.utils.format_dt(guild.created_at, style="D"),
            inline=True,
        )
        embed.add_field(
            name="Membres",
            value=f"{guild.member_count} ({humans} 👤 / {bots} 🤖)",
            inline=True,
        )
        embed.add_field(name="Salons", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Rôles", value=str(len(guild.roles)), inline=True)
        embed.add_field(
            name="Boosts",
            value=f"{guild.premium_subscription_count} (niveau {guild.premium_tier})",
            inline=True,
        )
        embed.add_field(
            name="Émojis", value=str(len(guild.emojis)), inline=True
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerInfo(bot))
