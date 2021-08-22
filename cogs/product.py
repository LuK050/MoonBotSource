# -*- coding: utf8 -*-
from typing import Counter
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

with open('config.json', 'r', encoding="utf-8") as file:
    config = json.load(file)


class User(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cluster = MongoClient("mongodb+srv://MoonBOT2:lxIEfbQQrPEXMBgP@cluster0.9oi72.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.product = self.cluster.MoonBOT.products


    @commands.command(aliases=['add_product'])
    @commands.has_permissions(administrator=True)
    async def product_add(self, ctx, *, name = None):
        message = ctx.message
        if name is None:
            embed = discord.Embed(description=f"Укажи название для товара",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if not message.attachments:
            embed = discord.Embed(description=f"Прикрепи картинку товара к сообщению!",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        id = 1
        for i in self.product.find({}):
            if self.product.count_documents({"_id": id}) == 0:
                break
            else:
                id += 1
                continue
        
        url = message.attachments[0].url
        p = config["settings"]["prefix"]
        self.product.insert_one({"_id": id,"name": name, "price_usd": 0, "price_rub": 0, "image": url})
        embed = discord.Embed(description=f"Товар `{name}` успешно добавлен! Его id: {id}\nНе заубдь установить стоимость - {p}price", colour=int("2f3136", 16))
        embed.set_image(url=url)
        embed.set_author(name="Новый товар!")
        await ctx.send(embed=embed)

    @commands.command(aliases=['list_product', 'list'])
    @commands.has_permissions(administrator=True)
    async def product_list(self, ctx):
        message = ctx.message
        counter = 0
        for i in self.product.find({}):
            id = i["_id"]
            name = i["name"]
            price_usd = i["price_usd"]
            price_rub = i["price_rub"]
            url = i["image"]
            counter += 1
            if counter == 1:
                embed = discord.Embed(colour=int("2f3136", 16))
                embed.set_author(name="Список товаров")
                embed.add_field(name="Название", value=f"```{name}```", inline=False)
                embed.add_field(name="id", value=f"```{id}```", inline=True)
                embed.add_field(name="Цена USD", value=f"```{price_usd}$```", inline=True)
                embed.add_field(name="Цена РУБ", value=f"```{price_rub}₽```", inline=True)
                embed.set_image(url=url)
                await ctx.send(embed=embed)
                continue

            embed = discord.Embed(colour=int("2f3136", 16))
            embed.add_field(name="Название", value=f"```{name}```", inline=False)
            embed.add_field(name="id", value=f"```{id}```", inline=True)
            embed.add_field(name="Цена USD", value=f"```{price_usd}$```", inline=True)
            embed.add_field(name="Цена РУБ", value=f"```{price_rub}₽```", inline=True)
            embed.set_image(url=url)
            await ctx.send(embed=embed)
            continue
        else:
            if counter == 0:
                embed = discord.Embed(description=f"Список товаров пуст!",colour=int("2f3136", 16))
                embed.set_author(name=f"Ошибка!")
                await ctx.send(embed=embed)
                return

    @commands.command(aliases=['remove_product'])
    @commands.has_permissions(administrator=True)
    async def removeproduct(self, ctx, id = None):
        if id is None:
            embed = discord.Embed(description=f"Укажи id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        try:
            name = self.product.find_one({"_id": int(id)})["name"]
        except:
            embed = discord.Embed(description=f"Укажи верный id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return

        counter = 1
        for i in self.product.find({}):
            id = i["_id"]
            if id < counter:
                new_id = id - 1
                self.product.update_one({"id": int(id)}, {"$set": {f"_id": new_id}}) 
            continue

        self.product.delete_one({"_id": int(id)})
        embed = discord.Embed(description=f"Товар `{name}` успешно удалён!", colour=int("2f3136", 16))
        embed.set_author(name="Удаление товара")
        await ctx.send(embed=embed)

    
    @commands.command(aliases=['set_price'])
    @commands.has_permissions(administrator=True)
    async def price(self, ctx, id = None, price = None, currency = None):
        if id is None:
            embed = discord.Embed(description=f"Укажи id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        try:
            name = self.product.find_one({"_id": int(id)})["name"]
        except:
            embed = discord.Embed(description=f"Укажи верный id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return
        if price is None:
            embed = discord.Embed(description=f"Укажи стоимость",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if currency is None:
            embed = discord.Embed(description=f"Укажи валюту\n```[usd, rub]```",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        
        if currency.lower() == "usd":
            self.product.update_one({"_id": int(id)}, {"$set": {f"price_usd": int(price)}}) 
            embed = discord.Embed(description=f"Цена для товара `{name}` установлена на {price}usd.", colour=int("2f3136", 16))
            embed.set_author(name="Цена | Доллары")
            await ctx.send(embed=embed)
            return
        elif currency.lower() == "rub":
            self.product.update_one({"_id": int(id)}, {"$set": {f"price_rub": int(price)}}) 
            embed = discord.Embed(description=f"Цена для товара `{name}` установлена на {price}руб.", colour=int("2f3136", 16))
            embed.set_author(name="Цена | Рубли")
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(description=f"Укажи верную валюту!\n```[usd, rub]```",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return

    @commands.command(aliases=['rename_product','rename'])
    @commands.has_permissions(administrator=True)
    async def product_rename(self, ctx, id = None, *, name = None):
        name_before = self.product.find_one({"_id": int(id)})["name"]
        if id is None:
            embed = discord.Embed(description=f"Укажи id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if self.product.count_documents({"_id": int(id)}) == 0:
            embed = discord.Embed(description=f"Укажи верный id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if name is None:
            embed = discord.Embed(description=f"Укажи новое название",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        
        self.product.update_one({"_id": int(id)}, {"$set": {f"name": name}}) 
        embed = discord.Embed(description=f"Название до: ```{name_before}```\nНазвание после: ```{name}```", colour=int("2f3136", 16))
        embed.set_author(name="Товар переименован")
        await ctx.send(embed=embed)
        return

    @commands.command(aliases=['image_product','image'])
    @commands.has_permissions(administrator=True)
    async def product_image(self, ctx, id = None):
        message = ctx.message
        if id is None:
            embed = discord.Embed(description=f"Укажи id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if self.product.count_documents({"_id": int(id)}) == 0:
            embed = discord.Embed(description=f"Укажи верный id",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        if not message.attachments:
            embed = discord.Embed(description=f"Прикрепи картинку товара к сообщению!",colour=int("2f3136", 16))
            embed.set_author(name=f"Ошибка!")
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=5)
            return 
        url = message.attachments[0].url
        
        self.product.update_one({"_id": int(id)}, {"$set": {f"image": url}}) 
        embed = discord.Embed(colour=int("2f3136", 16))
        embed.set_author(name="Картинка изменена!")
        embed.set_image(url=url)
        await ctx.send(embed=embed)
        return


def setup(client):
    client.add_cog(User(client))