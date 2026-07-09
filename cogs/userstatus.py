"""Commande admin `userstatus` : historique des sanctions d'un utilisateur."""
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import checks, replies, storage
from utils.i18n import t_lang

_LABEL_KEYS = {
    "warn": "us.warns_label",
    "mute": "us.mute_label",
    "unmute": "us.unmute_label",
    "kick": "us.kick_label",
    "ban": "us.ban_label",
    "unban": "us.unban_label",
    "confine": "us.confine_label",
    "unconfine": "us.unconfine_label",
    "vmute": "us.vmute_label",
    "vunmute": "us.vunmute_label",
    "vdeafen": "us.vdeafen_label",
    "vundeafen": "us.vundeafen_label",
    "move": "us.move_label",
}


def _fmt_duration(seconds: float) -> str:
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def _label(lang: str, action_type: str) -> str:
    key = _LABEL_KEYS.get(action_type)
    return t_lang(lang, key) if key else action_type


class UserStatus(commands.Cog):
    """Récapitulatif des actions de modération reçues par un utilisateur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="userstatus",
        description="Affiche l'historique des sanctions d'un utilisateur.",
    )
    @checks.admin()
    async def userstatus(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        actions = storage.get_modlog(ctx.guild.id, member.id)
        warns = storage.get_warns(ctx.guild.id, member.id)
        muted_until = (
            member.timed_out_until
            if member.timed_out_until is not None
            and member.timed_out_until > datetime.now(timezone.utc)
            else None
        )
        confined = any(
            uid == member.id
            for gid, uid, _ in storage.get_confinements()
            if gid == ctx.guild.id
        )

        spec = replies.Embed("warn", color=discord.Color.orange())
        spec.title("us.title", user=str(member))
        spec.thumbnail(member.display_avatar.url)

        # État actuel (traduit à la volée).
        def current(lang: str) -> str:
            etats = [t_lang(lang, "us.warns_now", count=warns)]
            if muted_until is not None:
                etats.append(t_lang(lang, "us.muted_until")
                             + discord.utils.format_dt(muted_until, style="R"))
            if confined:
                etats.append(t_lang(lang, "us.confined_now"))
            return "\n".join(etats)
        spec.field_fn("us.current", current, inline=False)

        # Compteurs par type + durée totale de mute.
        counts: dict[str, int] = {}
        total_mute = 0.0
        for action in actions:
            counts[action["type"]] = counts.get(action["type"], 0) + 1
            if action["type"] == "mute" and action.get("duration"):
                total_mute += action["duration"]

        def totals(lang: str) -> str:
            if not counts:
                return t_lang(lang, "us.no_sanction")
            summary = "\n".join(
                f"{_label(lang, typ)} : **{n}**"
                for typ, n in sorted(counts.items())
            )
            if total_mute:
                summary += "\n" + t_lang(lang, "us.mute_time",
                                         duration=_fmt_duration(total_mute))
            return summary
        spec.field_fn("us.total", totals, inline=False)

        # Détail des dernières actions (10 max).
        if actions:
            recent = actions[-10:]

            def recent_lines(lang: str) -> str:
                lines = []
                for action in recent:
                    ts = discord.utils.format_dt(
                        datetime.fromtimestamp(action["ts"], tz=timezone.utc),
                        style="f",
                    )
                    label = _label(lang, action["type"]).split(" ", 1)[-1]
                    extra = f" — {action['detail']}" if action.get("detail") else ""
                    if action.get("duration"):
                        extra += f" ({_fmt_duration(action['duration'])})"
                    mod = (
                        f" {t_lang(lang, 'us.by')} <@{action['moderator']}>"
                        if action.get("moderator") else ""
                    )
                    lines.append(f"• {ts} — {label}{extra}{mod}")
                return "\n".join(lines)
            spec.field_fn("us.recent", recent_lines, inline=False)

        # Notes de dossier (texte libre : donnée non traduite).
        notes = storage.get_notes(ctx.guild.id, member.id)
        if notes:
            note_lines = []
            for i, note in enumerate(notes, start=1):
                ts = discord.utils.format_dt(
                    datetime.fromtimestamp(note["ts"], tz=timezone.utc),
                    style="d",
                )
                mod = (
                    f" — <@{note['moderator']}>" if note.get("moderator") else ""
                )
                note_lines.append(f"**{i}.** {note['text']} ({ts}{mod})")
            value = "\n".join(note_lines)
            if len(value) > 1024:
                value = value[:1013] + "\n…"
            spec.field("us.notes", value, inline=False)

        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserStatus(bot))
