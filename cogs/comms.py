import discord
import twilio
import pymongo
import configparser
import sys
import re

sys.path.append("..")
from dbinit import lt_db
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


class comms(commands.Cog):
    def __init__(self, bot, lt_db, twi_cred):
        self.bot = bot

        # credentials and db have to be passed into comms from little_thunder

        self.lt_db = lt_db
        self.twisid = twi_cred["accountsid"]
        self.twiauth = twi_cred["authtoken"]

    @commands.command()
    async def register(self, ctx):
        """
        Register a phone number for text availability.
        """

        # users can only register numbers to themselves, this information is gathered here

        ID = str(ctx.message.author.id)
        author = ctx.message.author
        Name = str(ctx.message.author)
        response = self.lt_db.get_number(ID)
        channel = ctx.channel

        # make sure the author of the original request matches the whoever speaks and it's sent in the same channel.

        def check(message):
            return message.author == author and message.channel == channel

        i = 0

        # The command will attempt three times to register a valid US number before

        while i <= 2:
            i += 1

            # If there isn't a saved number for the user, ask this question.

            if response == None:
                await ctx.send("What phone number would you like to register?")
                msg = await self.bot.wait_for("message", check=check, timeout=60)
                try:
                    int(msg.content)
                    phoneNumber = msg.content

                    # check to make sure the phone number given is a US phone number

                    if self.lt_db.is_valid(phoneNumber) == True:
                        self.lt_db.register_number(Name, ID, phoneNumber)
                        await ctx.send(
                            f"Thank you! Your registered phone number is now {phoneNumber}."
                        )

                        # Attempt to send an opt-out message to the given number. If this number is blacklisted by opting out, the message will not be sent.

                        try:
                            client = Client(self.twisid, self.twiauth)
                            message = client.messages.create(
                                to=phoneNumber,
                                from_="17572605495",
                                body="LittleThunder has registered this number as a number for use on a Discord Server. If this was in error, respond STOP to unsubscribe.",
                            )
                            print(message.sid)

                        except TwilioRestException:
                            return True

                        i = 3
                    else:
                        await ctx.send(
                            f"{phoneNumber} is not a valid US Phone number. Please try again."
                        )
                except ValueError:
                    if i == 2:
                        await ctx.send(
                            "One last shot to set your number properly numbnuts."
                        )
                    else:
                        await ctx.send(
                            f"I'm sorry, {msg.content} is not an integer value. Please try again."
                        )

            else:
                await ctx.send("What would you like to update your phone number to?")
                msg = await self.bot.wait_for("message", check=check, timeout=60)
                try:
                    int(msg.content)

                    phoneNumber = msg.content
                    if self.lt_db.is_valid(phoneNumber) == True:
                        self.lt_db.update_number(Name, ID, phoneNumber)
                        await ctx.send(
                            f"Thank you! Your registered phone number is now {phoneNumber}."
                        )

                        try:
                            client = Client(self.twisid, self.twiauth)
                            message = client.messages.create(
                                to=phoneNumber,
                                from_="17572605495",
                                body="LittleThunder has registered this number as a valid number. If this was in error, respond STOP to unsubscribe.",
                            )
                            print(message.sid)
                        except TwilioRestException:
                            return True
                        i = 3
                    else:
                        await ctx.send(
                            f"{phoneNumber} is not a valid US Phone number. Please try again."
                        )
                except ValueError:
                    if i == 2:
                        await ctx.send(
                            "One last shot to set your number properly numbnuts."
                        )
                    else:
                        await ctx.send(
                            f"I'm sorry, {msg.content} is not an integer value. Please try again."
                        )

    @commands.command(pass_context=True)
    async def unregister(self, ctx):
        """
        Unregister your username and telephone number.
        """
        ID = str(ctx.message.author.id)
        response = self.lt_db.get_number(ID)

        # If a number exists, remove it.

        if response == None:
            await ctx.send("Are you sure you've registered a number?")
        else:
            self.lt_db.remove_number(ID)
            await ctx.send("Your number has been removed from my database!")

    @commands.command(pass_context=True)
    async def message(self, ctx):
        """
        Sends the mentioned User a message, separated by #.

        Syntax:

        .message @Cayden Cailean#6438 # Hey! You're needed for the dnds!
        """
        author = ctx.message.author

        try:
            user = ctx.message.mentions[0].id
        except IndexError:
            await ctx.send("Remember to @ a user in order to send them a message.")
        response = self.lt_db.get_number(user)

        to_number = response["phoneNumber"]
        if ctx.message.content.find("#") != -1:

            msgbody = re.search(r"#(.+)", ctx.message.content)
            msgbody = msgbody.group(0).replace("#", "")

        else:
            await ctx.send("Please use # to separate the recipient from your text.")

        try:
            client = Client(self.twisid, self.twiauth)

            # build, then send the message

            message = client.messages.create(
                to=to_number,
                from_="17572605495",
                body=f"From: {author}: \n\n{msgbody}",
            )
            print(message.sid)
            await ctx.send("Your message has been sent!")

            # Blacklisted numbers return a TwilioRestException. If this occurs, the user of the command is notified.

        except TwilioRestException:
            await ctx.send(
                "This registered user's phone is not accepting messages from LittleThunder."
            )


def setup(bot):
    bot.add_cog(comms(bot))
