"""Prévient les owners en MP après une mise à jour (déploiement).

`scripts/deploy.sh` écrit `data/pending_deploy.json` quand il applique une
nouvelle version depuis GitHub. Au démarrage suivant, ce cog lit ce fichier,
envoie un MP récapitulatif à tous les owners (PR concernées, commits,
version à jour), puis supprime le fichier.
"""
import json
import logging
import re
from pathlib import Path

import discord
from discord.ext import commands

import config
from utils import checks
from utils.i18n import t

log = logging.getLogger("action")

PENDING = Path(__file__).resolve().parents[1] / "data" / "pending_deploy.json"
_PR_RE = re.compile(r"Merge pull request #(\d+)")


class UpdateNotify(commands.Cog):
    """Notifie les owners d'une mise à jour appliquée par le déploiement auto."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._done = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        # Une seule fois par démarrage, même en cas de reconnexions.
        if self._done:
            return
        self._done = True
        if not PENDING.exists():
            return
        try:
            data = json.loads(PENDING.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            PENDING.unlink(missing_ok=True)
            return

        embed = self._build_embed(data)
        for owner_id in checks.all_owner_ids():
            try:
                user = self.bot.get_user(owner_id) or (
                    await self.bot.fetch_user(owner_id)
                )
                await user.send(embed=embed)
            except (discord.HTTPException, discord.NotFound):
                log.warning(
                    "Notif de mise à jour non délivrée à l'owner %s", owner_id
                )
        PENDING.unlink(missing_ok=True)
        log.info(
            "Notif de mise à jour envoyée (%s -> %s)",
            data.get("old"), data.get("new"),
        )

    def _build_embed(self, data: dict) -> discord.Embed:
        commits = data.get("commits") or []
        version = f"{config.VERSION} bêta" if config.BETA else config.VERSION

        embed = discord.Embed(
            title=t(None, "upd.title"),
            color=discord.Color.brand_green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=t(None, "upd.version"),
                        value=f"**{version}**", inline=True)
        embed.add_field(
            name=t(None, "upd.commit"),
            value=f"`{data.get('old', '?')}` → `{data.get('new', '?')}`",
            inline=True,
        )

        # PR référencées dans les commits de merge (dédupliquées, ordre gardé).
        prs = list(dict.fromkeys(
            m.group(1) for line in commits if (m := _PR_RE.search(line))
        ))
        if prs:
            embed.add_field(
                name=t(None, "upd.prs"),
                value=" · ".join(
                    f"[#{n}]({config.REPO_URL}/pull/{n})" for n in prs
                ),
                inline=False,
            )

        # Liste des changements (sujets de commits, hors commits de merge).
        changes = []
        for line in commits:
            subject = line.split("\t", 1)[-1]
            if subject.startswith("Merge pull request") or \
                    subject.startswith("Merge branch"):
                continue
            changes.append(f"• {subject}")
        value = "\n".join(changes) if changes else t(None, "upd.none")
        embed.add_field(name=t(None, "upd.changes"),
                        value=value[:1024], inline=False)

        embed.set_footer(text=t(None, "upd.footer"))
        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UpdateNotify(bot))
