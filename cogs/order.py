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
import uuid
from PIL import Image, ImageFont, ImageDraw
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


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        mo0nray: discord.Member = self.client.get_user(config["settings"]["mo0nray_id"])
        message_id = payload.message_id
        guild = self.client.get_guild(payload.guild_id)
        author: discord.Member = self.client.get_user(payload.user_id)

        if author.bot:
            return
        
        p = config["settings"]["prefix"]
        bot = self.client.get_user(config["settings"]["id"])
        everyone = guild.default_role
        order_category = discord.utils.get(guild.categories, id=config["settings"]["order_category_id"])
        channel: discord.Channel = discord.utils.get(guild.channels, id=payload.channel_id)
        message: discord.Message = await channel.fetch_message(message_id)

        if message_id == config["settings"]["order_msg_id"]:
            if self.settings.find_one({"_id": "status"})["status"] == "off":
                embed = discord.Embed(colour=int("2f3136", 16))
                embed.set_image(url=f"{en['text']['disable_img']}")
                await author.send(embed=embed)
                return
            if self.orders.count_documents({"id": author.id}) == 0 or self.orders.find_one({"id": author.id})["status"] == "in_work":
                uuid_user = str(uuid.uuid4())[0:6]
                order_channel = await guild.create_text_channel(name=f"order-{author.display_name}-{uuid_user}", category=order_category)

                await order_channel.set_permissions(everyone, read_messages=False, send_messages=False, view_channel=False)
                await order_channel.set_permissions(author, read_messages=True, send_messages=True, view_channel=True, add_reactions=False)

                embed_hello = discord.Embed(colour=int("2f3136", 16))
                embed_hello.set_image(url=f"{en['text']['start_img']}")
                await order_channel.send(f"{author.mention}",embed=embed_hello)

                embed = discord.Embed(colour=int("2f3136", 16))
                embed.set_image(url=f"{en['text']['lang_img']}")
                msg = await order_channel.send(embed=embed)

                self.orders.insert_one({"_id": uuid_user,"id": author.id, "type": "discord_from_member", "queue": -1, "status": "lang_choose", "channel_id": order_channel.id,"msg_app": 0, "msg_id": msg.id, "lang": "", "product": "", "currency": "", "price_usd":"", "price_rub":"", "msg_list": [], "file_list": []})

                await msg.add_reaction("🇬🇧")
                await msg.add_reaction("🇷🇺")
                return
            else:
                embed_error = discord.Embed(colour=int("2f3136", 16))
                embed_error.set_image(url=f"{en['text']['error_active_img']}")
                await author.send(embed=embed_error)
                return

        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                if self.orders.find_one({"id": author.id})["status"] == "lang_choose":
                    msg = await channel.fetch_message(self.orders.find_one({"id": author.id})["msg_id"])
                    channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"id": author.id})["channel_id"])
                    
                    if payload.emoji.name == "🇬🇧":
                        self.orders.update_one({"id": author.id}, {"$set": {f"lang": "en"}}) 
                        await msg.delete()
                        embed = discord.Embed(description="English has been successfully selected!", colour=int("2f3136", 16))
                        embed.set_author(name="Language selection", icon_url="https://emojio.ru/images/apple-b/1f1ec-1f1e7.png")
                        await channel_order.send(embed=embed, delete_after=5) 

                    if payload.emoji.name == "🇷🇺":
                        self.orders.update_one({"id": author.id}, {"$set": {f"lang": "ru"}}) 
                        await msg.delete()
                        embed = discord.Embed(description="Успешно выбран русский язык", colour=int("2f3136", 16))
                        embed.set_author(name="Выбор языка", icon_url="https://emojio.ru/images/apple-b/1f1f7-1f1fa.png")
                        await channel_order.send(embed=embed, delete_after=5)

                    counter = 0
                    lang = self.orders.find_one({"id": author.id})["lang"]
                    for i in self.product.find({}):
                        counter += 1
                        name = i["name"]
                        url = i["image"]
                        price_usd = i["price_usd"]
                        price_rub = i["price_rub"]
                        if counter == 1:
                            embed_list = discord.Embed(colour=int("2f3136", 16))
                            embed_list.set_author(name=f"{eval(lang)['text']['prod_list']}")
                            embed_list.add_field(name=f"{eval(lang)['text']['name']}", value=f"```{counter}. {name}```", inline=False)
                            embed_list.add_field(name=f"{eval(lang)['text']['price']} USD", value=f"```{price_usd}$```", inline=True)
                            embed_list.add_field(name=f"{eval(lang)['text']['price']} РУБ", value=f"```{price_rub}₽```", inline=True)
                            embed_list.set_image(url=url)
                            await channel_order.send(embed=embed_list)
                            continue
                        
                        embed_list = discord.Embed(colour=int("2f3136", 16))
                        embed_list.add_field(name=f"{eval(lang)['text']['name']}", value=f"```{counter}. {name}```", inline=False)
                        embed_list.add_field(name=f"{eval(lang)['text']['price']} USD", value=f"```{price_usd}$```", inline=True)
                        embed_list.add_field(name=f"{eval(lang)['text']['price']} РУБ", value=f"```{price_rub}₽```", inline=True)
                        embed_list.set_image(url=url)
                        await channel_order.send(embed=embed_list)
                        continue
                    
                    embed_2 = discord.Embed(description=f"{eval(lang)['text']['msg_2']}", colour=int("2f3136", 16))
                    msg_2 = await channel_order.send(embed=embed_2)

                    counter = 0
                    emoji_list = ['1⃣','2⃣','3⃣','4⃣','5⃣','6⃣','7⃣','8⃣','9⃣','🔟']
                    for i in self.product.find({}):
                        counter += 1
                        await msg_2.add_reaction(f"{emoji_list[counter - 1]}")
                        continue

                    self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_2.id, "status": "product_choose"}}) 
                    return


        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                lang = self.orders.find_one({"id": author.id})["lang"]
                
                if self.orders.find_one({"id": author.id})["status"] == "product_choose":
                    self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                    channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"id": author.id})["channel_id"])
                    product_pos = 0
                    if payload.emoji.name == "1⃣":
                        product_pos = 1
                    elif payload.emoji.name == "2⃣":
                        product_pos = 2
                    elif payload.emoji.name == "3⃣":
                        product_pos = 3
                    elif payload.emoji.name == "4⃣":
                        product_pos = 4
                    elif payload.emoji.name == "5⃣":
                        product_pos = 5
                    elif payload.emoji.name == "6⃣":
                        product_pos = 6
                    elif payload.emoji.name == "7⃣":
                        product_pos = 7
                    elif payload.emoji.name == "8⃣":
                        product_pos = 8
                    elif payload.emoji.name == "9⃣":
                        product_pos = 9
                    elif payload.emoji.name == "🔟":
                        product_pos = 10

                    counter = 0
                    for i in self.product.find({}):
                        counter += 1
                        if counter == product_pos:
                            await channel.purge(limit=100)
                            name = i["name"]
                            url = i["image"]
                            price_usd = i["price_usd"]
                            price_rub = i["price_rub"]

                            embed_choise = discord.Embed(description=f"{eval(lang)['text']['msg_3']}",colour=int("2f3136", 16))
                            embed_choise.set_author(name=f"{eval(lang)['text']['choise']}")
                            embed_choise.add_field(name=f"{eval(lang)['text']['name']}", value=f"```{counter}. {name}```", inline=False)
                            embed_choise.add_field(name=f"{eval(lang)['text']['price']} USD", value=f"```{price_usd}$```", inline=True)
                            embed_choise.add_field(name=f"{eval(lang)['text']['price']} РУБ", value=f"```{price_rub}₽```", inline=True)
                            embed_choise.set_image(url=url)
                            msg_3 = await channel_order.send(embed=embed_choise)
                            break
                        else:
                            continue

                    self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_3.id, "status": "choice_confirmation", "product": name, "price_usd": price_usd, "price_rub": price_rub}}) 
                    await msg_3.add_reaction("✅")
                    await msg_3.add_reaction("❌")
                    return

            if self.orders.count_documents({"channel_id": channel.id}) >= 1:
                if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                    lang = self.orders.find_one({"id": author.id})["lang"]
                    if self.orders.find_one({"id": author.id})["status"] == "choice_confirmation":
                        channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"id": author.id})["channel_id"])

                        
                        if payload.emoji.name == "✅":
                            self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                            embed_desc = discord.Embed(colour=int("2f3136", 16))
                            embed_desc.set_image(url=f"{eval(lang)['text']['msg_4_img']}")
                            msg_4 = await channel_order.send(embed=embed_desc)

                            msg_3 = await channel.fetch_message(self.orders.find_one({"id": author.id})["msg_id"])
                            self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_4.id, "status": "description"}}) 
                            await msg_3.clear_reactions()
                            await msg_4.add_reaction("✉")
                            return

                        elif payload.emoji.name == "❌":
                            self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                            msg_3 = await channel.fetch_message(self.orders.find_one({"id": author.id})["msg_id"])
                            await msg_3.delete()

                            counter = 0
                            lang = self.orders.find_one({"id": author.id})["lang"]
                            for i in self.product.find({}):
                                counter += 1
                                name = i["name"]
                                url = i["image"]
                                price_usd = i["price_usd"]
                                price_rub = i["price_rub"]
                                if counter == 1:
                                    embed_list = discord.Embed(colour=int("2f3136", 16))
                                    embed_list.set_author(name=f"{eval(lang)['text']['prod_list']}")
                                    embed_list.add_field(name=f"{eval(lang)['text']['name']}", value=f"```{counter}. {name}```", inline=False)
                                    embed_list.add_field(name=f"{eval(lang)['text']['price']} USD", value=f"```{price_usd}$```", inline=True)
                                    embed_list.add_field(name=f"{eval(lang)['text']['price']} РУБ", value=f"```{price_rub}₽```", inline=True)
                                    embed_list.set_image(url=url)
                                    await channel_order.send(embed=embed_list)
                                    continue
                                
                                embed_list = discord.Embed(colour=int("2f3136", 16))
                                embed_list.add_field(name=f"{eval(lang)['text']['name']}", value=f"```{counter}. {name}```", inline=False)
                                embed_list.add_field(name=f"{eval(lang)['text']['price']} USD", value=f"```{price_usd}$```", inline=True)
                                embed_list.add_field(name=f"{eval(lang)['text']['price']} РУБ", value=f"```{price_rub}₽```", inline=True)
                                embed_list.set_image(url=url)
                                await channel_order.send(embed=embed_list)
                                continue
                            
                            embed_2 = discord.Embed(description=f"{eval(lang)['text']['msg_2']}", colour=int("2f3136", 16))
                            msg_2 = await channel_order.send(embed=embed_2)

                            counter = 0
                            emoji_list = ['1⃣','2⃣','3⃣','4⃣','5⃣','6⃣','7⃣','8⃣','9⃣','🔟']
                            for i in self.product.find({}):
                                counter += 1
                                await msg_2.add_reaction(f"{emoji_list[counter - 1]}")
                                continue

                            self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_2.id, "status": "product_choose"}}) 
                            return

        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                lang = self.orders.find_one({"id": author.id})["lang"]
                if self.orders.find_one({"id": author.id})["status"] == "description":
                    channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"id": author.id})["channel_id"])
                    channel_order_send = discord.utils.get(guild.channels, id=config["settings"]["order_channel_id"])
                    msg_sending = await channel.fetch_message(self.orders.find_one({"id": author.id})["msg_id"])

                    
                    if payload.emoji.name == "✉":
                        counter = 0
                        message_text = ""
                        msg_list = self.orders.find_one({"id": author.id})["msg_list"]
                        file_list = self.orders.find_one({"id": author.id})["file_list"]
                        secret_id = self.orders.find_one({"id": author.id})["_id"]


                        if len(msg_list) == 0:
                            await msg_sending.remove_reaction("✉", author)
                            embed_error = discord.Embed(colour=int("2f3136", 16))
                            embed_error.set_image(url=f"{eval(lang)['text']['none_active_img']}")
                            await channel_order.send(embed=embed_error, delete_after=2)
                            return

                        self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                        await msg_sending.clear_reactions()
                        for i in msg_list:
                            list_content = msg_list[counter]
                            message_text = message_text + "\n" + list_content 
                            counter += 1
                            continue
                        await channel_order_send.send(f"{mo0nray.mention}")
                        embed_order = discord.Embed(description=f"**От: {author.mention}**\n{message_text}\n\n**Статус:** Ожидание",title="Заявка на заказ" ,colour=int("2f3136", 16))
                        msg_application = await channel_order_send.send(f"{secret_id}",embed=embed_order)
                        await msg_application.add_reaction("✅")
                        await msg_application.add_reaction("❌")

                        counter = 0
                        for i in file_list:
                            embed_image = discord.Embed(colour=int("2f3136", 16))
                            embed_image.set_image(url=file_list[counter])
                            await channel_order_send.send(embed=embed_image)
                            counter += 1
                            continue
                        self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_application.id, "status": "checking", "msg_app": msg_application.id}}) 

                        embed_application_user = discord.Embed(colour=int("2f3136", 16))
                        embed_application_user.set_image(url=f"{eval(lang)['text']['msg_5_img']}")
                        await channel_order.send(embed=embed_application_user)
                        return

        channel_order_send = discord.utils.get(guild.channels, id=config["settings"]["order_channel_id"])
        if channel == channel_order_send:
            emoji_rub = self.client.get_emoji(862735448191139850)
            emoji_usd = self.client.get_emoji(862735448219844639)
            secret_id_check = str(message.content)
            if self.orders.find_one({"_id": secret_id_check})["status"] == "checking":
                lang = self.orders.find_one({"_id": secret_id_check})["lang"]
                channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"_id": secret_id_check})["channel_id"])
                author = self.client.get_user(self.orders.find_one({"_id": secret_id_check})["id"])
                
                msg_application = await channel.fetch_message(message_id)
                

                if payload.emoji.name == "✅":
                    self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                    await channel_order.purge(limit=100)
                    embed_accept = discord.Embed(colour=int("2f3136", 16))
                    embed_accept.set_image(url=f"{eval(lang)['text']['value_img']}")
                    msg_accept = await channel_order.send(f"{author.mention}",embed=embed_accept)
                    
                    counter = 0
                    message_text = ''
                    msg_list = self.orders.find_one({"id": author.id})["msg_list"]
                    for i in msg_list:
                        list_content = msg_list[counter]
                        message_text = message_text + "\n" + list_content 
                        counter += 1
                        continue

                    embed_order = discord.Embed(description=f"**От: {author.mention}**\n{message_text}\n\n**Статус:** Принята",title="Заявка на заказ" ,colour=discord.Color.green())
                    await msg_application.edit(embed=embed_order)
                    await msg_application.clear_reactions()

                    self.orders.update_one({"msg_id": message_id}, {"$set": {f"msg_id": msg_accept.id, "status": "currency_choose"}}) 

                    await msg_accept.add_reaction(emoji_usd)
                    await msg_accept.add_reaction(emoji_rub)
                    return
                if payload.emoji.name == "❌":
                    self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                    author = self.client.get_user(self.orders.find_one({"_id": secret_id_check})["id"])
                    embed_accept = discord.Embed(colour=int("2f3136", 16))
                    embed_accept.set_image(url=f"{eval(lang)['text']['msg_rejected_img']}")
                    await author.send(embed=embed_accept)

                    counter = 0
                    message_text = ''
                    msg_list = self.orders.find_one({"id": author.id})["msg_list"]
                    for i in msg_list:
                        list_content = msg_list[counter]
                        message_text = message_text + "\n" + list_content 
                        counter += 1
                        continue

                    embed_order = discord.Embed(description=f"**От: {author.mention}**\n{message_text}\n\n**Статус:** Отклонена",title="Заявка на заказ" ,colour=discord.Color.red())
                    await msg_application.edit(embed=embed_order)

                    await msg_application.clear_reactions()

                    self.orders.delete_one({"_id": secret_id_check})
                    await channel_order.delete()
                    return

        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                lang = self.orders.find_one({"id": author.id})["lang"]
                if self.orders.find_one({"id": author.id})["status"] == "currency_choose":
                    channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"id": author.id})["channel_id"])
                    msg_accept = await channel.fetch_message(self.orders.find_one({"id": author.id})["msg_id"])

                    
                    if payload.emoji.id == 862735448219844639:
                        self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                        await channel_order.purge(limit=100)
                        embed_accept = discord.Embed(colour=int("2f3136", 16))
                        embed_accept.set_image(url=f"{eval(lang)['text']['value_usd_img']}")
                        msg_value = await channel_order.send(embed=embed_accept)
                        self.orders.update_one({"msg_id": message_id}, {"$set": {f"msg_accept": msg_value.id, "status": "verify_currency", "currency": "USD"}}) 
                        await msg_value.add_reaction("✅")
                        await msg_value.add_reaction("❌")
                        return
                        

                    if payload.emoji.id == 862735448191139850:
                        self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                        await channel_order.purge(limit=100)
                        embed_accept = discord.Embed(colour=int("2f3136", 16))
                        embed_accept.set_image(url=f"{eval(lang)['text']['value_rub_img']}")
                        msg_value = await channel_order.send(embed=embed_accept)
                        self.orders.update_one({"msg_id": message_id}, {"$set": {f"msg_accept": msg_value.id, "status": "verify_currency", "currency": "RUB"}}) 
                        await msg_value.add_reaction("✅")
                        await msg_value.add_reaction("❌")
                        return
                        
        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                lang = self.orders.find_one({"id": author.id})["lang"]
                if self.orders.find_one({"id": author.id})["status"] == "verify_currency":
                    channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"id": author.id})["channel_id"])

                    
                    if payload.emoji.name == "✅":
                        await asyncio.sleep(1)
                        if self.orders.find_one({"id": author.id})["status"] == "currency_choose" or self.orders.find_one({"id": author.id})["status"] != "verify_currency":
                            return
                        self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                        await channel_order.purge(limit=100)
                        user_bd = self.orders.find_one({"id": author.id})
                        currency = user_bd["currency"]
                        price = 0
                        name = user_bd["product"]
                        url = self.settings.find_one({"_id": "url"})["url"]
                        secret_id = user_bd["_id"]
                        if currency == "USD":
                            price = str(user_bd["price_usd"]) + "$"
                        if currency == "RUB":
                            price = str(user_bd["price_rub"]) + "₽"

                        embed_pay = discord.Embed(description=f"{eval(lang)['text']['msg_6']}\n",colour=int("2f3136", 16))
                        embed_pay.set_author(name=f"{eval(lang)['text']['msg_6_title']}")
                        embed_pay.add_field(name=f"{eval(lang)['text']['name']}", value=f"```{name}```", inline=False)
                        embed_pay.add_field(name=f"{eval(lang)['text']['on_price']}", value=f"```{price}```", inline=True)
                        embed_pay.add_field(name=f"{eval(lang)['text']['secret_id']}", value=f"```{secret_id}```", inline=True)
                        embed_pay.add_field(name=f"{eval(lang)['text']['link']}", value=f"{url}", inline=False)
                        embed_pay.set_image(url="https://cdn.discordapp.com/attachments/857013998301216778/863110450811371550/unknown.png")
                        msg_payment = await channel_order.send(embed=embed_pay)
                        await msg_payment.add_reaction("💳")
                        self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_payment.id, "status": "payment"}}) 
                        return
                    

                    elif payload.emoji.name == "❌":
                        await asyncio.sleep(1)
                        if self.orders.find_one({"id": author.id})["status"] == "payment_verify" or self.orders.find_one({"id": author.id})["status"] != "verify_currency" or self.orders.find_one({"id": author.id})["status"] == "wait":
                            return
                        self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                        emoji_rub = self.client.get_emoji(862735448191139850)
                        emoji_usd = self.client.get_emoji(862735448219844639)

                        await channel_order.purge(limit=100)
                        embed_accept = discord.Embed(colour=int("2f3136", 16))
                        embed_accept.set_image(url=f"{eval(lang)['text']['value_img']}")
                        msg_accept = await channel_order.send(f"{author.mention}",embed=embed_accept)

                        self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_accept.id, "status": "currency_choose"}}) 

                        await msg_accept.add_reaction(emoji_usd)
                        await msg_accept.add_reaction(emoji_rub)
                        return

        if self.orders.count_documents({"channel_id": channel.id}) >= 1:
            if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                lang = self.orders.find_one({"id": author.id})["lang"]
                if self.orders.find_one({"id": author.id})["status"] == "payment":
                    channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"id": author.id})["channel_id"])
                    channel_order_send = discord.utils.get(guild.channels, id=config["settings"]["order_channel_id"])
                    
                    
                    if payload.emoji.name == "💳":
                        if self.orders.find_one({"id": author.id})["status"] == "in_work" or self.orders.find_one({"id": author.id})["status"] != "payment":
                            return
                        self.orders.update_one({"msg_id": message_id}, {"$set": {"status": "wait"}}) 
                        user_bd = self.orders.find_one({"id": author.id})
                        currency = user_bd["currency"]
                        price = 0
                        name = user_bd["product"]
                        url = "https://ru.piliapp.com/emoji/list/"
                        secret_id = user_bd["_id"]
                        if currency == "USD":
                            price = str(user_bd["price_usd"]) + "$"
                        if currency == "RUB":
                            price = str(user_bd["price_rub"]) + "₽"

                        await channel_order.set_permissions(author, read_messages=True, send_messages=False, view_channel=True, add_reactions=False)
                        await channel_order.purge(limit=100)
                        
                        embed_payment = discord.Embed(description=f"Пользователь {author.name} утверждает что провёл оплату!\nПроверь это. В коментарии должен быть секретный код, ука-\nзанный ниже, а в нике -  Discord ник и тэг.",colour=int("2f3136", 16))
                        embed_payment.set_author(name=f"Проверь оплату!")
                        embed_payment.add_field(name=f"Товар", value=f"```{name}```", inline=False)
                        embed_payment.add_field(name=f"Цена", value=f"```{price}```", inline=True)
                        embed_payment.add_field(name=f"Секретный id", value=f"```{secret_id}```", inline=True)
                        embed_payment.add_field(name=f"Ссылка", value=f"[Тык](https://www.donationalerts.com/dashboard)", inline=True)
                        embed_payment.add_field(name=f"Статус", value=f"```Ожидание```", inline=False)
                        await channel_order_send.send(f"{mo0nray.mention}")
                        msg_pay_2 = await channel_order_send.send(f"{secret_id}", embed=embed_payment)

                        await msg_pay_2.add_reaction("✅")
                        await msg_pay_2.add_reaction("❌")

                        self.orders.update_one({"msg_id": message_id}, {"$set": {f"msg_id": msg_pay_2.id, "status": "payment_verify"}}) 

                        embed_payment_check = discord.Embed(colour=int("2f3136", 16))
                        embed_payment_check.set_image(url=f"{eval(lang)['text']['msg_7_img']}")
                        await channel_order.send(embed=embed_payment_check)
                        return


        channel_order_send = discord.utils.get(guild.channels, id=config["settings"]["order_channel_id"])
        if channel == channel_order_send:
            secret_id_check = str(message.content)
            if self.orders.find_one({"_id": secret_id_check})["status"] == "payment_verify":
                lang = self.orders.find_one({"_id": secret_id_check})["lang"]
                channel_order = discord.utils.get(guild.channels, id=self.orders.find_one({"_id": secret_id_check})["channel_id"])
                author = self.client.get_user(self.orders.find_one({"_id": secret_id_check})["id"])
                channel_queue = discord.utils.get(guild.channels, id=config["settings"]["queue_channel_id"])

                msg_application = await channel.fetch_message(message_id)
                user_bd = self.orders.find_one({"id": author.id})
                currency = user_bd["currency"]
                price = 0
                name = user_bd["product"]
                url = "https://ru.piliapp.com/emoji/list/"
                secret_id = user_bd["_id"]
                if currency == "USD":
                    price = str(user_bd["price_usd"]) + "$"
                if currency == "RUB":
                    price = str(user_bd["price_rub"]) + "₽"
                
                if payload.emoji.name == "✅":
                    if self.orders.find_one({"id": author.id})["status"] != "payment_verify" or self.orders.find_one({"id": author.id})["status"] == "in_work":
                        return
    
                    embed_payment = discord.Embed(description=f"Пользователь {author.name} утверждает что провёл оплату!\nПроверь это. В коментарии должен быть секретный код, ука-\nзанный ниже, а в нике -  Discord ник и тэг.",colour=discord.Color.green())
                    embed_payment.set_author(name=f"Проверь оплату!")
                    embed_payment.add_field(name=f"Товар", value=f"```{name}```", inline=False)
                    embed_payment.add_field(name=f"Цена", value=f"```{price}```", inline=True)
                    embed_payment.add_field(name=f"Секретный id", value=f"```{secret_id}```", inline=True)
                    embed_payment.add_field(name=f"Ссылка", value=f"[Тык](https://www.donationalerts.com/dashboard)", inline=True)
                    embed_payment.add_field(name=f"Статус", value=f"```Принята```", inline=False)
                    await msg_application.edit(embed=embed_payment)

                    await msg_application.clear_reactions()

                    active_category = discord.utils.get(guild.categories, id=config["settings"]["active_order_category_id"])
                    await channel_order.edit(category=active_category) 

                    queue = 1
                    for i in self.orders.find({"status": "in_work"}):
                        queue += 1
                        continue
                    await channel_order.purge(limit=100)
                    embed_work = discord.Embed(colour=int("2f3136", 16))
                    embed_work.set_image(url=f"{eval(lang)['text']['msg_8_img']}")

                    way = os.path.abspath(f'images')
                    if lang == "ru":
                        img = Image.open(rf"{way}/!ru.png")
                    if lang == "en":
                        img = Image.open(rf"{way}/!en.png")


                    font_my = ImageFont.truetype(rf"{way}/!Montserrat-ExtraBold.ttf", size=40)
                    draw = ImageDraw.Draw(img)
                    draw.text((290, 100), f"{queue}", font = font_my, fill='#8277e4')
                    img.save(rf"{way}/!queue_fin.png")

                    msg_work = await channel_order.send(f"{author.mention}",embed=embed_work)
                    await channel_order.send(file=discord.File(rf"{way}/!queue_fin.png"))
                    os.remove(rf"{way}/!queue_fin.png")

                    self.orders.update_one({"msg_id": message_id}, {"$set": {f"msg_id": msg_work.id, "status": "in_work", "queue": queue, "id": f"{author.id}"}}) 

                    if self.orders.count_documents({"status": "in_work"}) == 1:
                        channel_queue = discord.utils.get(guild.channels, id=config["settings"]["queue_channel_id"])
                        channel_app = discord.utils.get(guild.channels, id=config["settings"]["order_channel_id"])

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
                            embed_queue.set_author(name=f"Новый заказ")
                            embed_queue.add_field(name=f"В канал", value=f"[Тык]({channel_url})", inline=True)
                            embed_queue.add_field(name=f"К описанию", value=f"[Тык](https://discordapp.com/channels/{guild.id}/{channel_app.id}/{msg_queue.id})", inline=True)
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
                            embed_queue.set_author(name=f"Новый заказ")
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
                            embed_queue.set_author(name=f"Новый заказ")
                            embed_queue.add_field(name=f"Перейти в канал", value=f"[Тык]({channel_url})", inline=True)
                            embed_queue.add_field(name=f"Товар", value=f"```{product_name}```", inline=False)
                            embed_queue.add_field(name=f"Секретный id", value=f"```{secret_id}```", inline=True)
                            embed_queue.add_field(name=f"Описание", value=f"```{description}```", inline=False)
                            await channel_queue.send(embed=embed_queue)
                            return

                if payload.emoji.name == "❌":
                    if self.orders.find_one({"id": author.id})["status"] != "payment_verify" or self.orders.find_one({"id": author.id})["status"] == "in_work" or self.orders.find_one({"id": author.id})["status"] == "payment":
                        return

                    embed_payment = discord.Embed(description=f"Пользователь {author.name} утверждает что провёл оплату!\nПроверь это. В коментарии должен быть секретный код, ука-\nзанный ниже, а в нике -  Discord ник и тэг.",colour=discord.Color.red())
                    embed_payment.set_author(name=f"Проверь оплату!")
                    embed_payment.add_field(name=f"Товар", value=f"```{name}```", inline=False)
                    embed_payment.add_field(name=f"Цена", value=f"```{price}```", inline=True)
                    embed_payment.add_field(name=f"Секретный id", value=f"```{secret_id}```", inline=True)
                    embed_payment.add_field(name=f"Ссылка", value=f"[Тык](https://www.donationalerts.com/dashboard)", inline=True)
                    embed_payment.add_field(name=f"Статус", value=f"```Отклонена```", inline=False)
                    await msg_application.edit(embed=embed_payment)
                    await msg_application.clear_reactions()

                    await channel_order.purge(limit=100)
                    await channel_order.set_permissions(author, read_messages=True, send_messages=True, view_channel=True, add_reactions=False)
                    user_bd = self.orders.find_one({"id": author.id})
                    currency = user_bd["currency"]
                    price = 0
                    name = user_bd["product"]
                    url = self.settings.find_one({"_id": "url"})["url"]
                    secret_id = user_bd["_id"]
                    if currency == "USD":
                        price = str(user_bd["price_usd"]) + "$"
                    if currency == "RUB":
                        price = str(user_bd["price_rub"]) + "₽"

                    embed_pay_img = discord.Embed(colour=int("2f3136", 16))
                    embed_pay_img.set_image(url=f"{eval(lang)['text']['cancel_img']}")
                    await channel_order.send(f"{author.mention}",embed=embed_pay_img)

                    embed_pay = discord.Embed(description=f"{eval(lang)['text']['msg_6']}\n",colour=int("2f3136", 16))
                    embed_pay.set_author(name=f"{eval(lang)['text']['msg_6_title']}")
                    embed_pay.add_field(name=f"{eval(lang)['text']['name']}", value=f"```{name}```", inline=False)
                    embed_pay.add_field(name=f"{eval(lang)['text']['on_price']}", value=f"```{price}```", inline=True)
                    embed_pay.add_field(name=f"{eval(lang)['text']['secret_id']}", value=f"```{secret_id}```", inline=True)
                    embed_pay.add_field(name=f"{eval(lang)['text']['link']}", value=f"{url}", inline=False)
                    embed_pay.set_image(url="https://cdn.discordapp.com/attachments/857013998301216778/863110450811371550/unknown.png")
                    msg_payment = await channel_order.send(embed=embed_pay)

                    await msg_payment.add_reaction("💳")
                    self.orders.update_one({"id": author.id}, {"$set": {f"msg_id": msg_payment.id, "status": "payment"}}) 
                    return
                    


    @commands.Cog.listener()
    async def on_message(self, message):
        author = message.author
        content = message.content
        channel = message.channel

        if self.orders.count_documents({"id": author.id}) == 1:
            if channel.id == self.orders.find_one({"id": author.id})["channel_id"]:
                lang = self.orders.find_one({"id": author.id})["lang"]
                if self.orders.find_one({"id": author.id})["status"] == "description":
                    if not message.attachments:
                        msg_list = self.orders.find_one({"id": author.id})["msg_list"]
                        msg_list.append(content)

                        self.orders.update_one({"id": author.id}, {"$set": {f"msg_list": msg_list}}) 
                    else:
                        file_list = self.orders.find_one({"id": author.id})["file_list"]
                        file_list.append(message.attachments[0].url)
                        msg_list = self.orders.find_one({"id": author.id})["msg_list"]
                        msg_list.append(content + " *+Изображение*")

                        self.orders.update_one({"id": author.id}, {"$set": {f"msg_list": msg_list,"file_list": file_list}}) 
            

def setup(client):
    client.add_cog(User(client))