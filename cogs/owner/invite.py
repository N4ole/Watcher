"""Commande owner `invite` : génère une invitation vers un serveur du bot."""
import discord
from discord.ext import commands

from utils import checks


class Invite(commands.Cog):
    """Génération d'invitations vers les serveurs du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="invite",
        description="Génère une invitation vers un serveur du bot.",
    )
    @checks.is_owner()
    async def invite(self, ctx: commands.Context, server_id: str) -> None:
        if not server_id.isdigit():
            await ctx.send("❌ ID de serveur invalide.")
            return

        guild = self.bot.get_guild(int(server_id))
        if guild is None:
            await ctx.send("❌ Le bot n'est pas présent sur ce serveur.")
            return

        # Cherche un salon où le bot peut créer une invitation.
        channel = next(
            (
                c
                for c in guild.text_channels
                if c.permissions_for(guild.me).create_instant_invite
            ),
            None,
        )
        if channel is None:
            await ctx.send(
                "❌ Aucun salon ne permet au bot de créer une invitation "
                f"sur **{guild.name}**."
            )
            return

        try:
            invite = await channel.create_invite(
                max_age=0, max_uses=0, unique=True,
                reason=f"Demandé par {ctx.author}",
            )
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Impossible de créer l'invitation : {exc}")
            return

        await ctx.send(f"🔗 Invitation vers **{guild.name}** : {invite.url}")

    @invite.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Précisez l'ID du serveur.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Invite(bot))
