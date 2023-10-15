import discord

# Replace TOKEN with your Discord bot's token
client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    # Get the server object for the server you want to unban all users in
    server = client.get_guild(1144676407541235722)

    # Get a list of all banned users in the server
    async for ban_entry in server.bans():
        user = ban_entry.user
        await server.unban(user)

client.run('MTE2MzA5MjAwMzE4NjI5MDY5OA.GmSVNA.9WYTltDXc7LSAHW5P05Hr3QxTolbNXanG9OZEw')