# -*- coding: utf8 -*-
import discord
import json
import datetime
from discord import colour
from discord.embeds import *
from discord.ext import commands
from discord.ext import *
from discord.utils import *
from discord import *
import asyncio
from pymongo import MongoClient
import os
from PIL import Image, ImageFont, ImageDraw
import uuid

from pymongo.message import query


with open('config.json', 'r', encoding="utf-8") as file:
    config = json.load(file)
with open('en.json', 'r', encoding="utf-8") as en_file:
    en = json.load(en_file)
with open('ru.json', 'r', encoding="utf-8") as ru_file:
    ru = json.load(ru_file)

class User(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cluster = MongoClient("mongodb+srv://MoonBOT2:lxIEfbQQrPEXMBgP@cluster0.9oi72.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.orders = self.cluster.MoonBOT.orders
        self.product = self.cluster.MoonBOT.products
        self.settings = self.cluster.MoonBOT.settings


    @commands.command(aliases=['finish'])
    @commands.has_permissions(administrator=True)
    async def close(self, ctx):
        channel = ctx.channel
        guild = ctx.guild
        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if self.orders.find_one({"channel_id": channel.id})["status"] == "in_work":
                position = self.orders.find_one({"channel_id": channel.id})["queue"] 
                channel_queue = discord.utils.get(guild.channels, id=config["settings"]["queue_channel_id"])
                channel_app = discord.utils.get(guild.channels, id=config["settings"]["order_channel_id"])
                lang = self.orders.find_one({"channel_id": channel.id})["lang"]
                embed_complete = discord.Embed(colour=int("2f3136", 16))
                embed_complete.set_image(url=f"{eval(lang)['text']['order_complete']}") 

                if self.orders.find_one({"channel_id": channel.id})["type"] == "discord_from_member" or self.orders.find_one({"channel_id": channel.id})["type"] == "discord_from_author":
                    member = discord.utils.get(guild.members, id=int(self.orders.find_one({"channel_id": channel.id})["id"]))
                    await member.send(embed=embed_complete)

                counter = 1 
                for i in self.orders.find({"status": "in_work"}):
                    if position < counter: 
                        user_bd = i
                        pos_queue = user_bd["queue"] - 1
                        channel_id = user_bd["channel_id"]
                        channel_user = discord.utils.get(guild.channels, id=channel_id)
                        way = os.path.abspath(f'images')
                        lang = user_bd["lang"]
                        if lang == "ru":
                            img = Image.open(rf"{way}/!ru.png")
                        if lang == "en":
                            img = Image.open(rf"{way}/!en.png")


                        font_my = ImageFont.truetype(rf"{way}/!Montserrat-ExtraBold.ttf", size=40)
                        draw = ImageDraw.Draw(img)
                        draw.text((290, 100), f"{pos_queue}", font = font_my, fill='#8277e4')
                        img.save(rf"{way}/!queue_fin.png")

                        await channel_user.send(file=discord.File(rf"{way}/!queue_fin.png"))
                        os.remove(rf"{way}/!queue_fin.png")

                        self.orders.update_one({"channel_id": channel_user.id}, {"$set": {"queue": pos_queue}}) 
                    counter += 1
                    continue

                await channel.delete()
                self.orders.delete_one({"channel_id": channel.id})
                counter = 0

                if self.orders.count_documents({"queue": 1}) == 0:
                    embed_ura = discord.Embed(description=f"Все заказы выполнены! Отдыхай!",colour=int("2f3136", 16))
                    embed_ura.set_author(name=f"Ура!")
                    await channel_queue.send(embed=embed_ura)
                    return
                queue_1 = self.orders.find_one({"queue": 1})
                type = queue_1["type"]

                if type == "discord_from_member":
                    queue_1_channel = discord.utils.get(guild.channels, id=queue_1["channel_id"])
                    msg_queue = await channel_app.fetch_message(queue_1["msg_app"])
                    channel_url = await queue_1_channel.create_invite()
                    author = self.client.get_user(int(queue_1["id"]))
                    product_name = queue_1["product"]
                    secret_id = queue_1["_id"]
                    currency = queue_1["currency"]
                    lang = queue_1["lang"]
                    
                    price = 0
                    if currency == "USD":
                        price = str(queue_1["price_usd"]) + "$"
                    if currency == "RUB":
                        price = str(queue_1["price_rub"]) + "₽"

                    embed_queue = discord.Embed(description=f"Заказ от пользователя {author.mention}",colour=int("2f3136", 16))
                    embed_queue.set_author(name=f"Следующий заказ")
                    embed_queue.add_field(name=f"В канал", value=f"[Тык]({channel_url})", inline=True)
                    embed_queue.add_field(name=f"К описанию", value=f"[Тык](https://discordapp.com/channels/{ctx.guild.id}/{channel_app.id}/{msg_queue.id})", inline=True)
                    embed_queue.add_field(name=f"Товар", value=f"```{product_name}```", inline=False)
                    embed_queue.add_field(name=f"Стоимость", value=f"```{price}```", inline=False)
                    embed_queue.add_field(name=f"Секретный id", value=f"```{secret_id}```", inline=True)
                    embed_queue.add_field(name=f"Язык", value=f"```{lang}```", inline=True)
                    await channel_queue.send(embed=embed_queue)
                elif type == "discord_from_author":
                    queue_1_channel = discord.utils.get(guild.channels, id=queue_1["channel_id"])
                    channel_url = await queue_1_channel.create_invite()
                    author = self.client.get_user(int(queue_1["id"]))
                    product_name = queue_1["product"]
                    secret_id = queue_1["_id"]
                    lang = queue_1["lang"]
                    description = queue_1["description"]

                    embed_queue = discord.Embed(description=f"Заказ от пользователя {author.mention}. Он создан вручную.",colour=int("2f3136", 16))
                    embed_queue.set_author(name=f"Следующий заказ")
                    embed_queue.add_field(name=f"Перейти в канал", value=f"[Тык]({channel_url})", inline=True)
                    embed_queue.add_field(name=f"Товар", value=f"```{product_name}```", inline=False)
                    embed_queue.add_field(name=f"Секретный id", value=f"```{secret_id}```", inline=True)
                    embed_queue.add_field(name=f"Язык", value=f"```{lang}```", inline=True)
                    embed_queue.add_field(name=f"Описание", value=f"```{description}```", inline=False)
                    await channel_queue.send(embed=embed_queue)
                else:
                    queue_1_channel = discord.utils.get(guild.channels, id=queue_1["channel_id"])
                    channel_url = await queue_1_channel.create_invite()
                    product_name = queue_1["product"]
                    secret_id = queue_1["_id"]
                    name = queue_1["id"]
                    description = queue_1["description"]

                    embed_queue = discord.Embed(description=f"Название заказа - {name}. Он создан в ручную, не привязан\nк пользователю Discord.",colour=int("2f3136", 16))
                    embed_queue.set_author(name=f"Следующий заказ")
                    embed_queue.add_field(name=f"Перейти в канал", value=f"[Тык]({channel_url})", inline=True)
                    embed_queue.add_field(name=f"Товар", value=f"```{product_name}```", inline=False)
                    embed_queue.add_field(name=f"Секретный id", value=f"```{secret_id}```", inline=True)
                    embed_queue.add_field(name=f"Описание", value=f"```{description}```", inline=False)
                    await channel_queue.send(embed=embed_queue)

    @commands.command(aliases=['отмена'])
    async def cancel(self, ctx):
        channel = ctx.channel
        guild = ctx.guild
        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if self.orders.find_one({"channel_id": channel.id})["status"] == "in_work":
                return
            elif self.orders.find_one({"channel_id": channel.id})["status"] == "payment_verify":
                return
            else:
                author = discord.utils.get(guild.members, id=int(self.orders.find_one({"channel_id": channel.id})["id"]))
                await channel.delete()
                self.orders.delete_one({"channel_id": channel.id})
                embed = discord.Embed(colour=int("2f3136", 16))
                embed.set_image(url=f"{en['text']['cancel_img_command']}")
                await author.send(embed=embed)
                return

    @commands.command(aliases=['add_queue'])
    @commands.has_permissions(administrator=True)
    async def queue_add(self, ctx, name = None, id = None, *,description = None):
        if name is None:
            embed = discord.Embed(description=f"Укажи имя владельца заказа",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if id is None:
            embed = discord.Embed(description=f"Укажи id товара",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if self.product.count_documents({"_id": int(id)}) == 0:
            embed = discord.Embed(description=f"Укажи верный id товара",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if description is None:
            embed = discord.Embed(description=f"Укажи описание",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        channel = ctx.channel
        guild = ctx.guild
        uuid_user = str(uuid.uuid4())[0:6]
        everyone = guild.default_role

        position = 1
        for i in self.orders.find({"status": "in_work"}):
            position += 1
            continue
        
        active_category = discord.utils.get(guild.categories, id=config["settings"]["active_order_category_id"])
        order_channel = await guild.create_text_channel(name=f"order-{name}-{uuid_user}", category=active_category)
        await order_channel.set_permissions(everyone, read_messages=False, send_messages=False, view_channel=False)
        product_name = self.product.find_one({"_id": int(id)})["name"]

        embed = discord.Embed(description=f"Заказ успешно создан! Он не привязан к пользователю\nDiscord и был создан вручную.",colour=int("2f3136", 16))
        embed.set_author(name=f"Заказ создан")
        embed.add_field(name=f"Товар", value=f"```{product_name}```", inline=False)
        embed.add_field(name=f"Название заказа", value=f"```{name}```", inline=False)
        embed.add_field(name=f"В очереди", value=f"```{position}```", inline=True)
        embed.add_field(name=f"Секретный id", value=f"```{uuid_user}```", inline=True)
        embed.add_field(name=f"Описание", value=f"```{description}```", inline=False)

        await order_channel.send(embed=embed)
        await ctx.send(embed=embed)

        self.orders.insert_one({"_id": uuid_user, "id": name,"queue": position, "status": "in_work", "channel_id": order_channel.id, "product": product_name, "type": "none_discord", "lang": "ru", "description": description})
        if self.orders.count_documents({"status": "in_work"}) == 1:
            embed_2 = discord.Embed(description=f"Заказ успешно создан! Он не привязан к пользователю\nDiscord и был создан вручную.",colour=int("2f3136", 16))
            embed_2.set_author(name=f"Новый заказ")
            embed_2.add_field(name=f"Товар", value=f"```{product_name}```", inline=False)
            embed_2.add_field(name=f"Название заказа", value=f"```{name}```", inline=False)
            embed_2.add_field(name=f"В очереди", value=f"```{position}```", inline=True)
            embed_2.add_field(name=f"Секретный id", value=f"```{uuid_user}```", inline=True)
            embed_2.add_field(name=f"Описание", value=f"```{description}```", inline=False)
            channel_queue = discord.utils.get(guild.channels, id=config["settings"]["queue_channel_id"])
            await channel_queue.send(embed=embed_2)
        return

    @commands.command(aliases=['discord_add_queue'])
    @commands.has_permissions(administrator=True)
    async def queue_discord_add(self, ctx, member: discord.Member = None, id = None, lang = None, *,description = None):
        if member is None:
            embed = discord.Embed(description=f"Пингани владельца заказа",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if id is None:
            embed = discord.Embed(description=f"Укажи id товара",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if self.product.count_documents({"_id": int(id)}) == 0:
            embed = discord.Embed(description=f"Укажи верный id товара",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if lang is None:
            embed = discord.Embed(description=f"Укажи язык\n```[en, ru]```",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        langs = ["en", "ru"]
        if lang.lower() not in langs:
            embed = discord.Embed(description=f"Укажи верный язык\n```[en, ru]```",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if description is None:
            embed = discord.Embed(description=f"Укажи описание",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        channel = ctx.channel
        guild = ctx.guild
        uuid_user = str(uuid.uuid4())[0:6]
        everyone = guild.default_role

        position = 1
        for i in self.orders.find({"status": "in_work"}):
            position += 1
            continue
        
        active_category = discord.utils.get(guild.categories, id=config["settings"]["active_order_category_id"])
        order_channel = await guild.create_text_channel(name=f"order-{member.name}-{uuid_user}", category=active_category)
        await order_channel.set_permissions(everyone, read_messages=False, send_messages=False, view_channel=False)
        await order_channel.set_permissions(member, read_messages=True, send_messages=True, view_channel=True)
        product_name = self.product.find_one({"_id": int(id)})["name"]

        embed = discord.Embed(description=f"{eval(lang)['text']['msg_discord_create']}{member.mention}",colour=int("2f3136", 16))
        embed.set_author(name=f"{eval(lang)['text']['create']}")
        embed.add_field(name=f"{eval(lang)['text']['product']}", value=f"```{product_name}```", inline=False)
        embed.add_field(name=f"{eval(lang)['text']['member']}", value=f"```{member.name}```", inline=False)
        embed.add_field(name=f"{eval(lang)['text']['queue']}", value=f"```{position}```", inline=True)
        embed.add_field(name=f"{eval(lang)['text']['secret_id']}", value=f"```{uuid_user}```", inline=True)
        embed.add_field(name=f"{eval(lang)['text']['description']}", value=f"```{description}```", inline=False)

        embed_ctx = discord.Embed(description=f"{ru['text']['msg_discord_create']}{member.name}",colour=int("2f3136", 16))
        embed_ctx.set_author(name=f"{ru['text']['create']}")
        embed_ctx.add_field(name=f"{ru['text']['product']}", value=f"```{product_name}```", inline=False)
        embed_ctx.add_field(name=f"{ru['text']['member']}", value=f"```{member.name}```", inline=False)
        embed_ctx.add_field(name=f"{ru['text']['queue']}", value=f"```{position}```", inline=True)
        embed_ctx.add_field(name=f"{ru['text']['secret_id']}", value=f"```{uuid_user}```", inline=True)
        embed_ctx.add_field(name=f"{eval(lang)['text']['description']}", value=f"```{description}```", inline=False)

        await order_channel.send(f"{member.mention}",embed=embed)
        await ctx.send(embed=embed_ctx)

        self.orders.insert_one({"_id": uuid_user, "id": f"{member.id}","queue": position, "status": "in_work", "channel_id": order_channel.id, "product": product_name, "type": "discord_from_author", "lang": lang, "description": description})
        if self.orders.count_documents({"status": "in_work"}) == 1:
            embed_2 = discord.Embed(description=f"Этот заказ был создан вручную и привязан\nк пользователю Discord - {member.mention}",colour=int("2f3136", 16))
            embed_2.set_author(name=f"Новый заказ")
            embed_2.add_field(name=f"Товар", value=f"```{product_name}```", inline=False)
            embed_2.add_field(name=f"Участник", value=f"```{member.name}```", inline=False)
            embed_2.add_field(name=f"В очереди", value=f"```{position}```", inline=True)
            embed_2.add_field(name=f"Секретный id", value=f"```{uuid_user}```", inline=True)
            embed_2.add_field(name=f"Описание", value=f"```{description}```", inline=False)
            channel_queue = discord.utils.get(guild.channels, id=config["settings"]["queue_channel_id"])
            await channel_queue.send(embed=embed_2)
        return


    @commands.command(aliases=['Orders'])
    @commands.has_permissions(administrator=True)
    async def orders(self, ctx, status):
        guild = ctx.guild
        if status.lower() not in ["on", "off"]:
            embed = discord.Embed(description=f"Укажи верный статус\n```[on, off]```",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 

        if status.lower() == "on":
            if self.settings.find_one({"_id": "status"})["status"] == "on":
                embed = discord.Embed(description=f"Приём заказов уже включен!",colour=int("2f3136", 16))
                embed.set_author(name=f"Ошибка!")
                await ctx.message.delete()
                await ctx.send(embed=embed, delete_after=5)
                return 
            self.settings.update_one({"_id": "status"}, {"$set": {"status": "on"}}) 
            embed = discord.Embed(description=f"Приём заказов успешно включён!",colour=int("2f3136", 16))
            embed.set_author(name=f"Статус заказов")
            await ctx.send(embed=embed)

        if status.lower() == "off":
            if self.settings.find_one({"_id": "status"})["status"] == "off":
                embed = discord.Embed(description=f"Приём заказов уже выключен!",colour=int("2f3136", 16))
                embed.set_author(name=f"Ошибка!")
                await ctx.message.delete()
                await ctx.send(embed=embed, delete_after=5)
                return 
            self.settings.update_one({"_id": "status"}, {"$set": {"status": "off"}}) 
            embed = discord.Embed(description=f"Приём заказов успешно выключен!",colour=int("2f3136", 16))
            embed.set_author(name=f"Статус заказов")
            await ctx.send(embed=embed)



def setup(client):
    client.add_cog(User(client))
