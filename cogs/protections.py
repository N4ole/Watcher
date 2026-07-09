"""Commande admin `protections` : état de toutes les protections du serveur."""
from discord.ext import commands

from utils import checks, replies, storage
from utils.i18n import t_lang

# Protections activables via commande (clé de réglage -> clé de libellé i18n).
_TOGGLES = {
    "antibot": "prot.antibot",
    "antiraid": "prot.antiraid",
    "antipub": "prot.antipub",
    "antispam": "prot.antispam",
    "antiinsulte": "prot.antiinsulte",
}


class Protections(commands.Cog):
    """Vue d'ensemble des protections du serveur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="protections",
        description="Affiche l'état des protections du serveur.",
    )
    @checks.admin()
    async def protections(self, ctx: commands.Context) -> None:
        # État figé des réglages ; les libellés se traduisent à la volée.
        states = {
            key: storage.get_setting(ctx.guild.id, key, False)
            for key in _TOGGLES
        }

        def toggle_lines(lang: str) -> str:
            out = []
            for key, label_key in _TOGGLES.items():
                state = t_lang(lang, "prot.on" if states[key] else "prot.off")
                out.append(f"{t_lang(lang, label_key)} : **{state}**")
            return "\n".join(out)

        spec = (
            replies.Embed("info")
            .title("prot.title")
            .field_fn("prot.toggleable", toggle_lines, inline=False)
            .field_t("prot.always", "prot.always_val", inline=False)
            .footer("prot.footer")
        )
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Protections(bot))
