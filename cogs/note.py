"""Commandes `note` / `delnote` : notes libres au dossier d'un utilisateur.

Les notes sont affichées par `userstatus` (dossier). Utile pour consigner un
contexte qui n'est pas une sanction (ex. « déjà prévenu en MP », « ami de X »).
"""
import discord
from discord.ext import commands

from utils import checks, replies, storage

# Longueur maximale d'une note (pour rester lisible dans l'embed userstatus).
MAX_NOTE_LEN = 500


class Note(commands.Cog):
    """Notes de dossier d'un utilisateur (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="note",
        description="Ajoute une note au dossier d'un utilisateur (userstatus).",
    )
    @checks.admin()
    async def note(
        self, ctx: commands.Context, member: discord.Member, *, texte: str
    ) -> None:
        texte = texte.strip()
        if not texte:
            await replies.reply(ctx, "note.empty", kind="error")
            return
        if len(texte) > MAX_NOTE_LEN:
            await replies.reply(ctx, "note.too_long", kind="error",
                                max=MAX_NOTE_LEN)
            return
        storage.add_note(ctx.guild.id, member.id, ctx.author.id, texte)
        count = len(storage.get_notes(ctx.guild.id, member.id))
        await replies.reply(ctx, "note.added", kind="success",
                            user=member.mention, index=count)

    @commands.hybrid_command(
        name="delnote",
        description="Supprime une note du dossier d'un utilisateur (par numéro).",
    )
    @checks.admin()
    async def delnote(
        self, ctx: commands.Context, member: discord.Member, numero: int
    ) -> None:
        # Les notes sont numérotées à partir de 1 côté utilisateur.
        removed = storage.remove_note(ctx.guild.id, member.id, numero - 1)
        if removed is None:
            await replies.reply(ctx, "note.bad_index", kind="error",
                                user=member.mention)
            return
        await replies.reply(ctx, "note.removed", kind="success",
                            user=member.mention, index=numero)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Note(bot))
