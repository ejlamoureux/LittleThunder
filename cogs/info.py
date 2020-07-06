import discord
from discord.ext import commands


class info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        """
        The goodest boi.

        Prints a small snippet about the bot to the channel.
        """
        embed = discord.Embed(
            title="Little Thunder", description="The Goodest Boi", color=0xFF8822
        )
        embed.add_field(name="Author", value="Cayden Cailean")
        embed.add_field(
            name="Purpose",
            value="I'm just a generally good boi. I like to roll dice, and text people.",
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(info(bot))
