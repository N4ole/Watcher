"""Commande `botinfo` : informations générales sur le bot."""
from datetime import datetime, timezone

from discord.ext import commands

import config
from utils import replies
from utils.duration import human


class BotInfo(commands.Cog):
    """Présentation et statistiques du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="botinfo",
        description="Affiche des informations sur le bot.",
    )
    async def botinfo(self, ctx: commands.Context) -> None:
        uptime = datetime.now(timezone.utc) - self.bot.start_time
        members = sum((g.member_count or 0) for g in self.bot.guilds)

        spec = (
            replies.Embed("info")
            .title_text("🤖 Watcher")
            .desc("bi.desc")
            .thumbnail(self.bot.user.display_avatar.url if self.bot.user else None)
        )
        if config.BETA:
            spec.field_t("bi.version", "bi.version_val", version=config.VERSION)
        else:
            spec.field("bi.version", config.VERSION)
        spec.field("bi.servers", str(len(self.bot.guilds)))
        spec.field("f.members", str(members))
        spec.field("bi.ping", f"{round(self.bot.latency * 1000)} ms")
        spec.field("bi.uptime", human(uptime))
        spec.field("bi.commands", str(len(self.bot.commands)))
        spec.field("bi.prefix", f"`{config.PREFIX}`")
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BotInfo(bot))
