"""Commandes `mutecasque` / `unmutecasque` : coupe/rend le son en vocal.

Applique un « server deafen » Discord : le membre n'entend plus le vocal (et
ne peut plus parler tant qu'il est sourd). Le membre doit être connecté à un
salon vocal.
"""
import discord
from discord.ext import commands

from utils import checks, replies, storage


class VoiceDeafen(commands.Cog):
    """Mute casque d'un membre en vocal (permission « Rendre sourd »)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="mutecasque",
        description="Coupe le son d'un membre en vocal (server deafen).",
    )
    @checks.deafen_voice_perms()
    async def mutecasque(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        if not checks.can_act_on(ctx.author, member):
            await replies.reply(ctx, "voice.hierarchy", kind="error")
            return
        if member.voice is None or member.voice.channel is None:
            await replies.reply(ctx, "voice.not_connected", kind="error",
                                user=member.mention)
            return
        if member.voice.deaf:
            await replies.reply(ctx, "voice.already_deafened", kind="warn",
                                user=member.mention)
            return
        try:
            await member.edit(deafen=True, reason=f"Mute casque par {ctx.author}")
        except discord.Forbidden:
            await replies.reply(ctx, "voice.forbidden", kind="error")
            return
        except discord.HTTPException as exc:
            await replies.reply(ctx, "voice.failed", kind="error", error=str(exc))
            return
        storage.add_modlog(ctx.guild.id, member.id, "vdeafen", ctx.author.id)
        await replies.reply(ctx, "voice.deafened", kind="success",
                            user=member.mention)

    @commands.hybrid_command(
        name="unmutecasque",
        description="Rend le son à un membre en vocal.",
    )
    @checks.deafen_voice_perms()
    async def unmutecasque(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        if member.voice is None or member.voice.channel is None:
            await replies.reply(ctx, "voice.not_connected", kind="error",
                                user=member.mention)
            return
        if not member.voice.deaf:
            await replies.reply(ctx, "voice.not_deafened", kind="warn",
                                user=member.mention)
            return
        try:
            await member.edit(deafen=False, reason=f"Unmute casque par {ctx.author}")
        except discord.HTTPException as exc:
            await replies.reply(ctx, "voice.failed", kind="error", error=str(exc))
            return
        storage.add_modlog(ctx.guild.id, member.id, "vundeafen", ctx.author.id)
        await replies.reply(ctx, "voice.undeafened", kind="success",
                            user=member.mention)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceDeafen(bot))
