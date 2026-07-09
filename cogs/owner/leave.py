"""Commande owner `leave <id>` : fait quitter un serveur au bot."""
import logging

import discord
from discord.ext import commands

from utils import checks, replies

log = logging.getLogger("action")


class Leave(commands.Cog):
    """Fait quitter un serveur au bot (owners uniquement)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="leave",
        description="Fait quitter un serveur au bot (par ID).",
    )
    @checks.is_owner()
    async def leave(self, ctx: commands.Context, guild_id: str) -> None:
        if not guild_id.isdigit():
            await replies.reply(ctx, "leave.bad_id", kind="error")
            return
        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            await replies.reply(ctx, "leave.not_found", kind="error")
            return
        name = guild.name
        try:
            await guild.leave()
        except discord.HTTPException as exc:
            await replies.reply(ctx, "leave.failed", kind="error",
                                error=str(exc))
            return
        log.info("Bot retiré du serveur %s (%s) par %s", name, guild_id,
                 ctx.author)
        await replies.reply(ctx, "leave.done", kind="success",
                            name=name, id=guild_id)

    @leave.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await replies.reply(ctx, "error.owner_only", kind="error")
        elif isinstance(error, commands.MissingRequiredArgument):
            await replies.reply(ctx, "leave.usage", kind="error")
        else:
            await replies.reply(ctx, "error.generic", kind="error")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leave(bot))
