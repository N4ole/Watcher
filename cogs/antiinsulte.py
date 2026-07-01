"""Commande admin `antiinsulte on/off` : supprime les messages insultants."""
import discord
from discord.ext import commands

from utils import badwords
from utils import storage
from utils.i18n import t

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}


class AntiInsulte(commands.Cog):
    """Supprime les messages contenant une insulte détectée (si activé)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="antiinsulte",
        description="Active/désactive la suppression des insultes (on/off).",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def antiinsulte(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            storage.set_setting(ctx.guild.id, "antiinsulte", True)
            await ctx.send(t(ctx, "antiinsulte.on"))
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, "antiinsulte", False)
            await ctx.send(t(ctx, "antiinsulte.off"))
        else:
            await ctx.send(t(ctx, "toggle.usage", name="antiinsulte"))

    async def _handle(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        if message.author.guild_permissions.administrator:
            return
        if not storage.get_setting(message.guild.id, "antiinsulte", False):
            return
        if badwords.find_insult(message.content) is None:
            return

        try:
            await message.delete()
        except discord.HTTPException:
            pass
        await message.channel.send(
            t(message, "antiinsulte.warn", user=message.author.mention),
            delete_after=10,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self._handle(message)

    @commands.Cog.listener()
    async def on_message_edit(
        self, _before: discord.Message, after: discord.Message
    ) -> None:
        await self._handle(after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiInsulte(bot))
