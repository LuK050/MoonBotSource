import discord
from discord.ext import commands
import json
import os

print("MoonBOT loading...\n")

with open('config.json', 'r') as file:
	config = json.load(file)

client = commands.Bot(command_prefix = config["settings"]["prefix"], intents = discord.Intents.all(), description="The description")
client.remove_command("help")

@client.command()
@commands.is_owner()
async def load(ctx, extension):
	client.load_extension(f"cogs.{extension}")


@client.command()
@commands.is_owner()
async def unload(ctx, extension):
	client.unload_extension(f"cogs.{extension}")


@client.command()
@commands.is_owner()
async def reload(ctx, extension):
	client.unload_extension(f"cogs.{extension}")
	client.load_extension(f"cogs.{extension}")

print("Starting to connect cogs...")
for filename in os.listdir("./cogs"):
	if filename.endswith(".py"):
		client.load_extension(f"cogs.{filename[:-3]}")
		print(f"File {filename} connected!")
print(f'All {len(os.listdir("./cogs"))} cog-files successfully connected!')

print("MoonBOT started launch...")
client.run(config["settings"]["token"])