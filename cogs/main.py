# -*- coding: utf8 -*-
import discord
from discord.ext import commands
from discord.ext import *
import json
import datetime

from discord.ext.commands import errors
with open('config.json', 'r', encoding="utf-8") as file:
    config = json.load(file)

class User(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.Cog.listener()
    async def on_ready(self):    
        await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Minecraft"))
        print("\n|-----------------------------------|")
        print("| MoonBOT ready! Author: _LuK__     |")
        print("|-----------------------------------|")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error): 
        author = ctx.author
        if isinstance(error, commands.MemberNotFound):
            if ctx.channel == author.dm_channel:
                return
            embed = discord.Embed(description=f"Указанный пользователь не найден",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
        elif isinstance(error, commands.MissingPermissions):
            if ctx.channel == author.dm_channel:
                return
            embed = discord.Embed(description=f"У вас нет прав",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)

    @commands.Cog.listener()
    async def on_member_join(self, member): 
        guild = member.guild
        role = discord.utils.get(guild.roles, id=config["settings"]["member_role_id"])
        await member.add_roles(role)
            
def setup(client):
    client.add_cog(User(client))