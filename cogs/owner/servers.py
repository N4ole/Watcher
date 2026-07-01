"""Commande owner `serveurs` : liste les serveurs du bot."""
import discord
from discord.ext import commands

from utils import checks


class Servers(commands.Cog):
    """Liste des serveurs du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="serveurs",
        description="Liste les serveurs du bot, triés par nombre de membres.",
    )
    @checks.is_owner()
    async def serveurs(self, ctx: commands.Context) -> None:
        guilds = sorted(
            self.bot.guilds,
            key=lambda g: g.member_count or 0,
            reverse=True,
        )

        embed = discord.Embed(
            title=f"🌐 Serveurs du bot ({len(guilds)})",
            color=discord.Color.blurple(),
        )
        for guild in guilds[:25]:  # Limite d'embed : 25 champs.
            joined = guild.me.joined_at if guild.me else None
            since = (
                discord.utils.format_dt(joined, style="R") if joined else "inconnu"
            )
            embed.add_field(
                name=f"{guild.name}",
                value=(
                    f"ID : `{guild.id}`\n"
                    f"Membres : **{guild.member_count}**\n"
                    f"Présent depuis : {since}"
                ),
                inline=False,
            )
        if len(guilds) > 25:
            embed.set_footer(text=f"... et {len(guilds) - 25} autre(s) serveur(s)")
        await ctx.send(embed=embed)

    @serveurs.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Servers(bot))
