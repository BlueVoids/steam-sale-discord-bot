import discord
import requests
from discord.ext import commands, tasks
import asyncio

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_steam_info(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
    page = requests.get(url)
    json_file = page.json()

    if json_file[str(appid)]["success"]:
        info = json_file[str(appid)]["data"]
        if "price_overview" in info:
            price = info["price_overview"]
            return {
                "name": info["name"],
                "original": price["initial"] / 100,
                "discounted": price["final"] / 100,
                "discount_percent": price["discount_percent"]
            }
        else:
            return {"name": info["name"], "free": True}
    return None

def grab_appid(web_url):
    parts = web_url.strip("/").split("/")
    if "app" in parts:
        idx = parts.index("app")
        return parts[idx+1]
    else:
        return None
    
def save_records(username, appid, lastprice):
    with open(f"{username}.txt", "a") as file:
        file.write(f"{appid}\n{lastprice}\n")
    return

def read_records(username, appid):
    with open(f"{username}.txt", "r") as file:
        lines = [line.strip() for line in file]
        if appid in lines:
            return None
    return lines

def replace_price_record(username, appid, newprice):
    with open(f"{username}.txt", "r") as file:
        lines = [line.strip() for line in file]
        for i in range(len(lines)):
            if lines[i] == appid:
                lines[i + 1] = newprice
    with open(f"{username}.txt", "w") as file:
        for item in lines:
            file.write(f"{item}\n")


@bot.slash_command(name="channel", description="Change what channel I ping in!")
async def channel(ctx, id = str):
    with open("channelid.txt", "w") as file:
        file.write(id)
    await ctx.respond("🎉 Successfully changed channel!", ephemeral = True)


@bot.slash_command(name="price", description="Check the price of a steam game!")
async def price(ctx, url = str):
    await ctx.defer()

    appid = grab_appid(url)
    if appid == None:
        await ctx.respond("❗ I Couldn't find info using that link, please try another.", ephemeral = True)
        return
    data = get_steam_info(appid)

    if data.get("free"):
        await ctx.respond(f"🎉 This game is free! There is no need for me to track it, just download it!\nhttps://tenor.com/EhSX.gif")
    else:
        if data['discount_percent'] == 0:
            await ctx.respond(
                f"🎮 **{data['name']}**\n"
                f"💲 Original: ${data['original']:.2f}\n"
                f"This game is currently not on sale 😭"
            )
        else:    
            await ctx.respond(
                f"🎮 **{data['name']}**\n"
                f"💲 Original: ${data['original']:.2f}\n"
                f"🔥 Sale: ${data['discounted']:.2f} (-{data['discount_percent']}%)"
            )

@bot.slash_command(name="track", description="Add a game that I can check for sales for you!")
async def track(ctx, url = str):
    await ctx.defer()

    appid = grab_appid(url)
    if appid == None:
        await ctx.respond("❗ I Couldn't find info using that link, please try another.", ephemeral = True)
        return
    data = get_steam_info(appid)
    
    username = ctx.author.name

    if username not in users:
        users.append(username)
    check = read_records(username, appid)
    if check == None:
        await ctx.respond(f"👀 **{data['name']}** is already on your list!\n📣 I will ping you if the price drops!")
    elif data.get("free"):
        await ctx.respond("❗ This game is free! There is no reason for me to track it!", ephemeral = True)
    else:
        save_records(username, appid, data['discounted'])
        await ctx.respond(f"🎉 Added **{data['name']}** to your list!\n📣 I will ping you if the price drops!")


    

@tasks.loop(minutes=10)
async def check_sales():
    
    for people in users:
        
        records = read_records(people, "00000")
        
        game_ids = []
        prices = []
        for i in range(len(records)):
            if i % 2 == 0:
                game_ids.append(records[i])
            else:
                prices.append(records[i])
        for i in range(len(game_ids)):
            data = get_steam_info(game_ids[i])
            current_price_float = float(data['discounted'])
            record_price_float = float(prices[i])
            if current_price_float != record_price_float:
                replace_price_record(people, game_ids[i], data['discounted'])
                if current_price_float < record_price_float:
                    channel = bot.get_channel(ping_channel_id)
                    if channel:
                        user = discord.utils.get(bot.get_all_members(), name=people)
                        await channel.send(
                            f"📣 @{user.mention} **{data['name']}** has had a price drop!"
                            f"💲 Original: ${data['original']:.2f}\n"
                            f"🔥 Sale: ${data['discounted']:.2f} (-{data['discount_percent']}%)"                    
                        )
                    
                    
                
    

@bot.event
async def on_ready():
    with open("channelid.txt", "r") as file:
        global ping_channel_id
        ping_channel_id = int(file.readline().strip())
    global users
    users = ["blu_void"]
    print(f"Logged in as {bot.user}")
    print(f"Ping channel is {ping_channel_id}")
    check_sales.start()

bot.run("MTM5OTEwOTgxNDY3MTM3NjU1NA.GsiJJK.YoxoRb3euVf7eUUcScOFcKxKZnENblDxPey9QI")

