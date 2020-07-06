import discord
import re
import dice
import asyncio
from discord.ext import commands
import sys

sys.path.append("..")
from dbinit import lt_db


class rpg(commands.Cog):
    def __init__(self, bot, lt_db):
        self.bot = bot
        self.lt_db = lt_db

    def ctx_info(self, ctx):
        Category = ctx.channel.category.id
        Guild = ctx.message.guild.id
        ID = ctx.message.author.id
        return Category, Guild, ID
        

    @commands.command(pass_context=True, aliases=["dice", "r", "roll"])
    async def d(self, ctx, input: str):

        """
        Rolls dice using #d# format, with a maximum of 100d100.
        
        You may add or subtract flat modifiers or dice by appending them to your initial #d# roll.
        """

        try:
            isPlus = input.find("+")
            isMinus = input.find("-")

            outList = "placeHolder"
            outResults = []
            Total = 0

            if isPlus == -1 and isMinus == -1:
                try:
                    diceNum, diceVal = input.split("d")
                except ValueError as e:
                    raise Exception("Make sure your expression is in #d# format.")

                if int(diceNum) > 100 or int(diceVal) > 100:
                    raise Exception(
                        "That's too many numbers. The limit to this value is 100d100."
                    )
                else:
                    outList = dice.roll(input)
                    for i in outList:
                        Total += i
                        outResults.append(i)

            if isPlus != -1 or isMinus != -1:

                expr = re.split("[+-]", input)[0]

                diceNum, diceVal = expr.split("d")

                outResults = dice.roll(expr)

                posmod = 0
                negmod = 0

                bonus = re.findall(r"(\+\d+)(?:(?!d))", input)

                for i in bonus:
                    posmod += int(i)

                bonusDice = re.findall(r"\+\d+d\d+", input)
                for i in bonusDice:
                    idiceNum, idiceVal = i.split("d")
                    if int(idiceNum) > 100 or int(idiceVal) > 100:
                        raise Exception(
                            "That's too many numbers. The limit to this value is 100d100."
                        )
                    else:
                        outResults.extend(dice.roll(i))

                malus = re.findall(r"(\-\d+)(?:(?!d))", input)

                for i in malus:
                    negmod += int(i)

                malusDice = re.findall(r"\-\d+d\d+", input)
                for i in malusDice:
                    output = dice.roll(i)
                    idiceNum, idiceVal = i.split("d")
                    if int(idiceNum) > 100 or int(idiceVal) > 100:
                        raise Exception(
                            "That's too many numbers. The limit to this value is 100d100."
                        )
                    else:
                        for i in output:
                            outResults.append(str(i))

                for i in outResults:
                    Total += int(i)
                Total += posmod
                Total += negmod

                if int(diceNum) > 100 or int(diceVal) > 100:
                    raise Exception(
                        "That's too many numbers. The limit to this value is 100d100."
                    )

            if ctx.message.content.find("#") != -1:
                commentText = re.search(r"#(.+)", ctx.message.content)
                commentText = commentText.group(0).replace("#", "")
            else:
                commentText = "Rolling some dice"

            if hasattr(ctx.message.author, "nick") == True:
                if ctx.message.author.nick != None:
                    discName = ctx.message.author.nick
                else:
                    discName = ctx.message.author.name
            else:
                discName = ctx.message.author.name

            embed = discord.Embed(
                title=f"Results for {discName}",
                description=commentText,
                color=ctx.message.author.color,
            )
            embed.add_field(name="Results", value=outResults)
            embed.add_field(name="Total", value=Total)
            await ctx.send(embed=embed)
            return int(Total)
        except Exception as e:
            if str(e).find("not enough values") != -1:
                await ctx.send("Make sure your expression is in #d# format.")
            elif str(e).find("literal") != -1:
                await ctx.send("Make sure your expression is in #d# format.")
            elif str(e).find("400 bad request"):
                await ctx.send(
                    "The output is too large. Try with fewer combined dice in your expression."
                )
            return Total

    @commands.group()
    async def init(self, ctx):
        """
        The init command keeps track of initiative within a channel category. In order to use this with multiple games simultaneously, you will need to separate the games into different text channel categories.
        
        In order to add combatants, use .init add.
        To remove a combatant, use .init remove.
        To end combat/clear the initiative table, use .init endcombat
        To show initiative order, use .init.
        """
        if ctx.invoked_subcommand is None:
            Category, Guild, ID = self.ctx_info(ctx)
            initraw = self.lt_db.init_get(Guild, Category)
            turnNum = int(self.lt_db.turn_get(Guild, Category))

            for i in range(turnNum - 1):
                moveEntry = initraw[0]
                del initraw[0]
                initraw.append(moveEntry)
            try:
                mentionMe = initraw[0].get("ID")
            except:
                await ctx.send(
                    "Before requesting an initiative table, make sure initiative has been added."
                )

            output = ""
            for i in initraw:
                del i["ID"]
                outstring = f"{list(i.values())[0]} : {list(i.values())[1]}"
                output += outstring + "\n"
            embed = discord.Embed(
                Title=f"Initiative for {ctx.channel.category}", colour=0x00FF00
            )
            embed.add_field(name="Initiative", value=output)

            try:
                await ctx.send(embed=embed)
            except:
                await ctx.send(
                    "Before requesting an initiative table, make sure initiative has been added."
                )
            if mentionMe != None:
                await ctx.send(f"Hey, <@{mentionMe}>, you're up.")

    @init.command(pass_context=True)
    async def add(self, ctx, name, dieRoll):
        """
        Add a Combatant to the initiative table.

        Syntax:
        .init add [name] [dice]
        """
        Category, Guild, ID = self.ctx_info(ctx)
        if dieRoll.find("d") == True:
            outcome = await rpg.d(self, ctx, dieRoll)
        else:
            outcome = int(dieRoll)
        try:
            ID = ctx.message.mentions[0].id
        except:
            ID = ctx.message.author.id
        await ctx.send(f"{name} has been added to the initiative counter.")
        self.lt_db.init_add(Guild, Category, name, ID, outcome)

    @init.command(pass_context=True)
    async def remove(self, ctx, Name):
        """
        Removes a single combatant from the Initiative Tracker.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        self.lt_db.init_remove(Guild, Category, Name)
        await ctx.send(f"{Name} has been removed from the initiative count.")

    @init.command(pass_context=True)
    async def endcombat(self, ctx):
        """
        Clears the initiative table altogether. This cannot be undone.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        check = self.lt_db.owner_check(Guild, Category, ID)
        if check == True:
            self.lt_db.init_clear(Guild, Category)
            await ctx.send(
                "Combat has ended, and the initiative table has been wiped clean!"
            )
        else:
            await ctx.send(
                "It doesn't look like you're the DM here, so you probably don't need to worry about this one."
            )

    @init.command(pass_context=True, aliases=["pass", "start"])
    async def next(self, ctx):
        Category, Guild, ID = self.ctx_info(ctx)
        current = self.lt_db.current_init(Guild, Category)
        # print(current)
        print(ID)
        dmCheck = self.lt_db.owner_check(Guild, Category, ID)
        if int(ID) == int(current) or dmCheck == True:
            self.lt_db.turn_next(Guild, Category)
            print("I'm working")
        else:
            await ctx.send("I don't think it's your turn yet!")
        await self.init(ctx)

    @commands.group(pass_context=True)
    async def dm(self, ctx):
        """
        Select a subcommand to use with this command.
        """

    @dm.command(pass_context=True)
    async def register(self, ctx):
        """
        Register the user as a Dungeon Master within the current channel category.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        output = self.lt_db.add_owner(Guild, Category, ID)
        await ctx.send(output)

    @dm.command(pass_context=True)
    async def unregister(self, ctx):
        """
        Unregister current DM for Category. Only usable by 
        """
        Category, Guild, ID = self.ctx_info(ctx)
        override = ctx.message.author.permissions_in(ctx.channel).administrator
        output = self.lt_db.remove_owner(Guild, Category, ID, override)
        await ctx.send(output)

    @commands.group(pass_context=True)
    async def char(self, ctx):
        """
        todo: update docstring with useful things.
        """

    @char.command(pass_context=True)
    async def register(self, ctx, Name):
        """
        Register a user's character.
        """
        Category, Guild, ID = self.ctx_info(ctx)

        try:
            ID = ctx.message.mentions[0].id
        except:
            ID = ctx.message.author.id

        output = self.lt_db.add_char(Guild, Category, ID, Name)
        await ctx.send(output)
        
    @char.command(pass_context=True)
    async def unregister(self, ctx, Name):
        """
        Unregister a user's character.
        """
        Category, Guild, ID = self.ctx_info(ctx)

        output = self.lt_db.remove_char(Guild, Category, ID, Name)
        await ctx.send(output)

def setup(bot):
    bot.add_cog(rpg(bot))
