"""Commande `avatar` : affiche l'avatar d'un utilisateur."""
import discord
from discord.ext import commands

from utils import replies


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

        spec = (
            replies.Embed("info")
            .title("avatar.title", user=str(member))
            .desc_text(links)
            .image(avatar.url)
            .footer("f.requested_by", user=str(ctx.author))
        )
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Avatar(bot))
