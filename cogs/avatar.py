"""Commande `avatar` : affiche l'avatar d'un utilisateur."""
import discord
from discord.ext import commands

from utils.i18n import t


class Avatar(commands.Cog):
    """Récupère l'avatar d'un utilisateur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="avatar",
        description="Affiche l'avatar d'un utilisateur.",
    )
    async def avatar(
        self, ctx: commands.Context, member: discord.Member = None
    ) -> None:
        member = member or ctx.author
        avatar = member.display_avatar

        # Liens vers les différents formats disponibles.
        formats = ["png", "jpg", "webp"]
        if avatar.is_animated():
            formats.append("gif")
        links = " | ".join(
            f"[{fmt.upper()}]({avatar.replace(format=fmt, size=1024).url})"
            for fmt in formats
        )

        embed = discord.Embed(
            title=t(ctx, "avatar.title", user=member),
            description=links,
            color=discord.Color.blurple(),
        )
        embed.set_image(url=avatar.url)
        embed.set_footer(text=t(ctx, "f.requested_by", user=ctx.author))
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Avatar(bot))
