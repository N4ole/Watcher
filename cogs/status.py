"""Commande `status` : version, ping, nombre de serveurs et mode debug."""
from discord.ext import commands

import config
from utils import replies


class Status(commands.Cog):
    """État général du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="status",
        description="Version, ping et nombre de serveurs.",
    )
    async def status(self, ctx: commands.Context) -> None:
        spec = replies.Embed("info").title("st.title")
        if config.BETA:
            spec.field_t("bi.version", "bi.version_val", version=config.VERSION)
        else:
            spec.field("bi.version", config.VERSION)
        spec.field("bi.ping", f"{round(self.bot.latency * 1000)} ms")
        spec.field("bi.servers", str(len(self.bot.guilds)))
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Status(bot))
