"""Commande `move` : déplace un membre vers un autre salon vocal."""
import discord
from discord.ext import commands

from utils import checks, replies, storage


class Move(commands.Cog):
    """Déplacement vocal d'un membre (permission « Déplacer des membres »)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="move",
        description="Déplace un membre vers un autre salon vocal.",
    )
    @checks.move_perms()
    async def move(
        self,
        ctx: commands.Context,
        member: discord.Member,
        salon: discord.VoiceChannel,
    ) -> None:
        if not checks.can_act_on(ctx.author, member):
            await replies.reply(ctx, "voice.hierarchy", kind="error")
            return
        if member.voice is None or member.voice.channel is None:
            await replies.reply(ctx, "voice.not_connected", kind="error",
                                user=member.mention)
            return
        if member.voice.channel.id == salon.id:
            await replies.reply(ctx, "move.already_there", kind="warn",
                                user=member.mention, channel=salon.mention)
            return
        try:
            await member.move_to(salon, reason=f"Déplacé par {ctx.author}")
        except discord.Forbidden:
            await replies.reply(ctx, "voice.forbidden", kind="error")
            return
        except discord.HTTPException as exc:
            await replies.reply(ctx, "voice.failed", kind="error", error=str(exc))
            return
        storage.add_modlog(
            ctx.guild.id, member.id, "move", ctx.author.id, detail=salon.name
        )
        await replies.reply(ctx, "move.done", kind="success",
                            user=member.mention, channel=salon.mention)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Move(bot))
