"""Envoie un message de présentation lorsque le bot est mentionné seul."""
import discord
from discord.ext import commands

import config
from utils.i18n import t


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
            title=t(message, "mention.title"),
            description=t(message, "mention.desc"),
            color=discord.Color.blurple(),
        )
        embed.add_field(name=t(message, "mention.prefix"),
                        value=f"`{config.PREFIX}`", inline=True)
        embed.add_field(
            name=t(message, "mention.help"),
            value=f"`{config.PREFIX}help` ou `/help`",
            inline=True,
        )
        embed.add_field(
            name=t(message, "mention.features"),
            value=t(message, "mention.features_val"),
            inline=False,
        )
        if self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await message.channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Mention(bot))
