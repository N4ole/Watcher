"""Commande owner `central` : tableau de bord global du bot."""
from datetime import datetime, timezone

import discord
from discord.ext import commands

import config
from utils import checks, storage
from utils.duration import human

_PROTECTIONS = {
    "antibot": "Anti-bot",
    "antiraid": "Anti-raid",
    "antipub": "Anti-pub",
    "antispam": "Anti-spam",
    "antiinsulte": "Anti-insulte",
}


class Central(commands.Cog):
    """Centralisation des statistiques du bot (owners)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="central",
        description="Tableau de bord global du bot (owners).",
    )
    @checks.is_owner()
    async def central(self, ctx: commands.Context) -> None:
        guilds = self.bot.guilds

        # Membres.
        total_members = sum((g.member_count or 0) for g in guilds)
        bots = sum(1 for g in guilds for m in g.members if m.bot)
        humans = total_members - bots

        # Mutes (timeouts actifs) et confinements (salons confin-*).
        now = datetime.now(timezone.utc)
        muted = 0
        confined = 0
        for g in guilds:
            for m in g.members:
                if m.timed_out_until and m.timed_out_until > now:
                    muted += 1
            category = discord.utils.get(g.categories, name="confinement")
            if category:
                confined += sum(
                    1 for c in category.text_channels
                    if c.name.startswith("confin-")
                )

        watched = storage.total_watched()
        warned_users, warn_points = storage.warn_totals()
        reminders = len(storage.get_reminders())
        timed_confinements = len(storage.get_confinements())
        owners = len(storage.get_owners()) + (1 if config.OWNER_ID else 0)
        uptime = human(now - self.bot.start_time)

        embed = discord.Embed(
            title="🛰️ Centralisation ClaudeBot",
            color=discord.Color.gold(),
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="🌐 Serveurs",
            value=(
                f"**{len(guilds)}** serveurs\n"
                f"**{total_members}** membres\n"
                f"👤 {humans} · 🤖 {bots}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🛡️ Modération active",
            value=(
                f"🔇 {muted} mute(s)\n"
                f"🔒 {confined} confiné(s)\n"
                f"👁️ {watched} surveillé(s)"
            ),
            inline=True,
        )
        embed.add_field(
            name="⚠️ Avertissements",
            value=(
                f"{warned_users} utilisateur(s)\n"
                f"{warn_points} point(s) au total\n"
                f"⏳ {timed_confinements} confinement(s) temporisé(s)"
            ),
            inline=True,
        )

        prot = "\n".join(
            f"{label} : **{storage.count_setting_enabled(key)}** serveur(s)"
            for key, label in _PROTECTIONS.items()
        )
        embed.add_field(name="🚨 Protections activées", value=prot, inline=False)

        embed.add_field(name="⏰ Rappels en attente", value=str(reminders), inline=True)
        embed.add_field(name="👑 Owners", value=str(owners), inline=True)
        embed.add_field(
            name="⚙️ Bot",
            value=(
                f"v{config.VERSION} · {round(self.bot.latency * 1000)} ms\n"
                f"Uptime : {uptime}"
            ),
            inline=True,
        )
        await ctx.send(embed=embed)

    @central.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Central(bot))
