"""Commande admin `ban` : bannit un utilisateur, avec raison et durée option.

    ban <utilisateur> [durée] [raison]

Si une durée est fournie (format court : 30s, 5m, 2h, 1d, 1h30m…), le
bannissement est temporaire : le membre est débanni automatiquement à
l'échéance. La temporisation est persistée sur disque et reprise au
redémarrage du bot. Sans durée, le bannissement est définitif.
"""
import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import checks, replies, storage
from utils.duration import parse_duration
from utils.i18n import t

log = logging.getLogger("action")


class Ban(commands.Cog):
    """Bannissement (permission « Bannir des membres »), permanent ou temporisé."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._resumed = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Reprend les bans temporaires persistés (une seule fois)."""
        if self._resumed:
            return
        self._resumed = True
        for guild_id, user_id, release_ts in storage.get_tempbans():
            self.bot.loop.create_task(
                self._schedule_unban(guild_id, user_id, release_ts)
            )

    async def _schedule_unban(
        self, guild_id: int, user_id: int, release_ts: float
    ) -> None:
        """Attend l'échéance puis débannit. Robuste au redémarrage."""
        delay = release_ts - datetime.now(timezone.utc).timestamp()
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            storage.clear_tempban(guild_id, user_id)
            return
        unbanned = False
        try:
            await guild.unban(
                discord.Object(id=user_id), reason="Fin du ban temporaire"
            )
            unbanned = True
            log.info(
                "Ban temporaire expiré — %s débanni de %s (%s)",
                user_id, guild.name, guild.id,
            )
        except discord.NotFound:
            pass  # déjà débanni manuellement.
        except discord.HTTPException:
            pass
        finally:
            storage.clear_tempban(guild_id, user_id)

        # Ban terminé : on prévient l'utilisateur et on lui envoie une invite.
        if unbanned:
            await self._notify_unban(guild, user_id)

    async def _make_invite(self, guild: discord.Guild) -> str | None:
        """Crée une invitation (7 j, usage unique) sur le 1er salon possible."""
        channel = guild.system_channel or next(
            iter(guild.text_channels), None
        )
        channels = [channel] if channel else []
        channels += [c for c in guild.text_channels if c is not channel]
        for chan in channels:
            if chan and chan.permissions_for(guild.me).create_instant_invite:
                try:
                    invite = await chan.create_invite(
                        max_age=7 * 86400, max_uses=1, unique=True,
                        reason="Fin du ban temporaire",
                    )
                    return invite.url
                except discord.HTTPException:
                    continue
        return None

    async def _notify_unban(self, guild: discord.Guild, user_id: int) -> None:
        """MP à l'utilisateur : fin de ban + invitation pour revenir."""
        try:
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(
                user_id
            )
        except (discord.HTTPException, discord.NotFound):
            return
        invite_url = await self._make_invite(guild)
        spec = replies.Embed("success").title("ban.unban_dm_title").desc(
            "ban.unban_dm_desc" if invite_url else "ban.unban_dm_no_invite",
            server=guild.name,
        )
        if invite_url:
            spec.field("🔗", invite_url, inline=False)
        await replies.reply_dm(user, guild, "", spec=spec)

    @commands.hybrid_command(
        name="ban",
        description="Bannit un utilisateur (raison et durée optionnelle).",
    )
    @checks.ban_perms()
    async def ban(
        self, ctx: commands.Context, cible: discord.User,
        duree: str | None = None, *, raison: str | None = None,
    ) -> None:
        # La durée est optionnelle : si le 1er mot n'en est pas une, il fait
        # partie de la raison (ex: `ban @x spam` = ban définitif, raison spam).
        delta = None
        if duree is not None:
            delta = parse_duration(duree)
            if delta is None:
                raison = f"{duree} {raison}".strip() if raison else duree
                duree = None
        reason = raison or t(ctx, "mod.no_reason")

        # La cible peut être hors du serveur (ban par ID). Si elle est
        # présente, on applique les garde-fous de hiérarchie.
        member = ctx.guild.get_member(cible.id)

        # Garde-fous : soi-même et hiérarchie des rôles.
        if cible.id == ctx.author.id:
            await replies.reply(ctx, "ban.self", kind="error")
            return
        if member is not None and not checks.can_act_on(
            ctx.author, member
        ):
            await replies.reply(ctx, "ban.hierarchy", kind="error")
            return

        until = discord.utils.utcnow() + delta if delta is not None else None

        # Prévenir l'utilisateur en MP AVANT le ban (après, le bot ne partage
        # plus de serveur avec lui). On indique serveur, raison et durée.
        dm_spec = (
            replies.Embed("error", color=discord.Color.red())
            .title("ban.dm_title")
            .desc("ban.dm_temp" if delta else "ban.dm_perm",
                  server=ctx.guild.name)
            .field("mod.reason_label", reason, inline=False)
        )
        if until is not None:
            dm_spec.field(
                "mod.duration_label",
                f"{discord.utils.format_dt(until, style='F')} "
                f"({discord.utils.format_dt(until, style='R')})", inline=False,
            )
        else:
            dm_spec.field_t("mod.duration_label", "mod.permanent", inline=False)
        dm_sent = await replies.reply_dm(cible, ctx.guild, "", spec=dm_spec) \
            is not None

        try:
            await ctx.guild.ban(
                cible, reason=f"{ctx.author} : {reason}",
                delete_message_days=0,
            )
        except discord.Forbidden:
            await replies.reply(ctx, "ban.forbidden", kind="error")
            return
        except discord.HTTPException as exc:
            await replies.reply(ctx, "ban.failed", kind="error", error=str(exc))
            return

        storage.add_modlog(
            ctx.guild.id, cible.id, "ban", ctx.author.id,
            duration=delta.total_seconds() if delta else None,
            detail=reason,
        )

        spec = replies.Embed("error", color=discord.Color.red()).title("ban.title")
        if delta is not None:
            release_ts = until.timestamp()
            storage.set_tempban(ctx.guild.id, cible.id, release_ts)
            self.bot.loop.create_task(
                self._schedule_unban(ctx.guild.id, cible.id, release_ts)
            )
            spec.desc("ban.temp_desc", user=str(cible), reason=reason)
            spec.field("ban.until", discord.utils.format_dt(until, style="F"))
            spec.field("ban.relative", discord.utils.format_dt(until, style="R"))
            log.info(
                "Ban temporaire — %s (%s) banni par %s (%s) sur %s (%s) "
                "jusqu'au %s : %s",
                cible, cible.id, ctx.author, ctx.author.id,
                ctx.guild.name, ctx.guild.id, until.isoformat(), reason,
            )
        else:
            spec.desc("ban.perm_desc", user=str(cible), reason=reason)
            log.info(
                "Ban définitif — %s (%s) banni par %s (%s) sur %s (%s) : %s",
                cible, cible.id, ctx.author, ctx.author.id,
                ctx.guild.name, ctx.guild.id, reason,
            )
        if not dm_sent:
            spec.footer("mod.dm_failed")
        await replies.reply_rich(ctx, spec)

    @commands.hybrid_command(
        name="unban",
        description="Débannit un utilisateur par son ID.",
    )
    @checks.ban_perms()
    async def unban(
        self, ctx: commands.Context, utilisateur: str,
        *, raison: str | None = None,
    ) -> None:
        # On accepte un ID brut ou une mention <@id>.
        raw = utilisateur.strip().strip("<@!>")
        if not raw.isdigit():
            await replies.reply(ctx, "unban.bad_id", kind="error")
            return
        user_id = int(raw)
        reason = raison or t(ctx, "mod.no_reason")

        try:
            await ctx.guild.unban(
                discord.Object(id=user_id), reason=f"{ctx.author} : {reason}"
            )
        except discord.NotFound:
            await replies.reply(ctx, "unban.not_banned", kind="error", id=user_id)
            return
        except discord.Forbidden:
            await replies.reply(ctx, "ban.forbidden", kind="error")
            return
        except discord.HTTPException as exc:
            await replies.reply(ctx, "ban.failed", kind="error", error=str(exc))
            return

        # Retire une éventuelle temporisation persistée.
        storage.clear_tempban(ctx.guild.id, user_id)
        storage.add_modlog(ctx.guild.id, user_id, "unban", ctx.author.id,
                           detail=reason)
        log.info(
            "Déban manuel — %s débanni par %s (%s) sur %s (%s) : %s",
            user_id, ctx.author, ctx.author.id,
            ctx.guild.name, ctx.guild.id, reason,
        )
        await replies.reply(ctx, "unban.done", kind="success", id=user_id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
