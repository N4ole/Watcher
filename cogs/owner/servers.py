"""Commande owner `serveurs` : détail de chaque serveur, une page par serveur."""
import discord
from discord.ext import commands

from utils import checks

_VERIF = {
    discord.VerificationLevel.none: "Aucune",
    discord.VerificationLevel.low: "Basse",
    discord.VerificationLevel.medium: "Moyenne",
    discord.VerificationLevel.high: "Haute",
    discord.VerificationLevel.highest: "Très haute",
}


def _guild_embed(guild: discord.Guild, index: int, total: int) -> discord.Embed:
    """Construit l'embed détaillé d'un serveur."""
    bots = sum(1 for m in guild.members if m.bot)
    humans = (guild.member_count or 0) - bots

    embed = discord.Embed(
        title=guild.name,
        description=guild.description or None,
        color=discord.Color.blurple(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    embed.add_field(name="ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(
        name="Propriétaire",
        value=f"{guild.owner} (`{guild.owner_id}`)" if guild.owner
        else f"`{guild.owner_id}`",
        inline=True,
    )
    embed.add_field(
        name="Créé le",
        value=discord.utils.format_dt(guild.created_at, style="D"),
        inline=True,
    )

    embed.add_field(
        name="Membres",
        value=f"**{guild.member_count}**\n👤 {humans} · 🤖 {bots}",
        inline=True,
    )
    embed.add_field(
        name="Salons",
        value=(
            f"💬 {len(guild.text_channels)} · 🔊 {len(guild.voice_channels)}\n"
            f"📁 {len(guild.categories)} · 🎙️ {len(guild.stage_channels)} · "
            f"📑 {len(guild.forums)}"
        ),
        inline=True,
    )
    embed.add_field(
        name="Rôles / Émojis / Stickers",
        value=(
            f"{len(guild.roles)} rôles\n"
            f"{len(guild.emojis)}/{guild.emoji_limit} émojis\n"
            f"{len(guild.stickers)}/{guild.sticker_limit} stickers"
        ),
        inline=True,
    )

    embed.add_field(
        name="Boosts",
        value=f"{guild.premium_subscription_count} (niveau {guild.premium_tier})",
        inline=True,
    )
    embed.add_field(
        name="Vérification",
        value=_VERIF.get(guild.verification_level, str(guild.verification_level)),
        inline=True,
    )
    joined = guild.me.joined_at if guild.me else None
    embed.add_field(
        name="Bot présent depuis",
        value=discord.utils.format_dt(joined, style="R") if joined else "?",
        inline=True,
    )

    # Salon système, AFK, langue.
    extras = []
    if guild.system_channel:
        extras.append(f"Salon système : {guild.system_channel.mention}")
    if guild.afk_channel:
        extras.append(
            f"AFK : {guild.afk_channel.name} ({guild.afk_timeout // 60} min)"
        )
    extras.append(f"Langue : {guild.preferred_locale}")
    if guild.vanity_url_code:
        extras.append(f"Vanity : `/{guild.vanity_url_code}`")
    embed.add_field(name="Divers", value="\n".join(extras), inline=False)

    if guild.features:
        embed.add_field(
            name="Fonctionnalités",
            value=", ".join(f"`{f.lower()}`" for f in guild.features)[:1000],
            inline=False,
        )

    embed.set_footer(
        text=f"Serveur {index + 1}/{total} · trié par nombre de membres"
    )
    return embed


class ServersView(discord.ui.View):
    """Navigation entre les serveurs (une page par serveur)."""

    def __init__(self, guilds: list[discord.Guild], author_id: int) -> None:
        super().__init__(timeout=180)
        self.guilds = guilds
        self.index = 0
        self.author_id = author_id
        self._refresh()

    def _refresh(self) -> None:
        self.prev.disabled = self.index == 0
        self.next.disabled = self.index == len(self.guilds) - 1
        self.counter.label = f"{self.index + 1}/{len(self.guilds)}"

    def current_embed(self) -> discord.Embed:
        return _guild_embed(self.guilds[self.index], self.index, len(self.guilds))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Ce menu n'est pas pour toi.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev(
        self, interaction: discord.Interaction, _b: discord.ui.Button
    ) -> None:
        self.index = max(0, self.index - 1)
        self._refresh()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.primary, disabled=True)
    async def counter(
        self, interaction: discord.Interaction, _b: discord.ui.Button
    ) -> None:  # pragma: no cover
        pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next(
        self, interaction: discord.Interaction, _b: discord.ui.Button
    ) -> None:
        self.index = min(len(self.guilds) - 1, self.index + 1)
        self._refresh()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)


class Servers(commands.Cog):
    """Détail des serveurs du bot (owners)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="serveurs",
        description="Détaille chaque serveur du bot (une page par serveur).",
    )
    @checks.is_owner()
    async def serveurs(self, ctx: commands.Context) -> None:
        guilds = sorted(
            self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True
        )
        if not guilds:
            await ctx.send("Le bot n'est sur aucun serveur.")
            return
        view = ServersView(guilds, ctx.author.id)
        await ctx.send(embed=view.current_embed(), view=view)

    @serveurs.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Servers(bot))
