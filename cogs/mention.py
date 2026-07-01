"""Envoie un message de présentation lorsque le bot est mentionné seul."""
import discord
from discord.ext import commands

import config


class Mention(commands.Cog):
    """Réponse de présentation à la mention du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.bot.user is None:
            return
        if self.bot.user not in message.mentions:
            return

        # On ne répond que si le message est *uniquement* la mention du bot
        # (pour ne pas interférer avec « @bot <commande> »).
        content = message.content
        for form in (f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"):
            content = content.replace(form, "")
        if content.strip():
            return

        embed = discord.Embed(
            title="👋 Bonjour, je suis ClaudeBot !",
            description=(
                "Un bot de modération et d'utilitaires pour ton serveur."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Préfixe", value=f"`{config.PREFIX}`", inline=True)
        embed.add_field(
            name="Aide",
            value=f"`{config.PREFIX}help` ou `/help`",
            inline=True,
        )
        embed.add_field(
            name="Fonctionnalités",
            value=(
                "• Modération (warn, mute, confine, clear...)\n"
                "• Automodération (anti-majuscules, anti-emojis)\n"
                "• Surveillance et infos utilisateurs"
            ),
            inline=False,
        )
        if self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await message.channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Mention(bot))
