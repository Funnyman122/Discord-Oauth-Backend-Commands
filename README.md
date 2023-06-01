# Discord Oauth Backend + Commands

This tool is used to interact with Discord OAuth tokens to retrieve information about a user as well as forcfully adding them to any of your Discord servers.


Force rejoin - Prevents users from leaving the server as long as they have granted the oauth
Force Join - Force users to join a server

It uses mongodb to store the tokens, so you'll have to add your own connection uri where specified in the py file
There are 6 commands, 

Search: Allows you to search the db for information about the relevant user
Invitespecific: Forcefully adds a specified user to the current discord
Stat: Returns the number of users who have authorised the oauth
getallauthed: Returns a brief summary of all the user's information
Revokeoauth: Revokes the authorisation of a user's oauth
Inviteall: Forcefully adds all users to the current discord server.


You'll also need to create an application and bot within that same application then replace the commented lines with the relevant information.
You'll also need to have a domain pointed towards the ip which the bot is being hosted on, it creates a server on port 80 to interact with incoming oauth completion redirects, this domain has to be entered as the redirect url for the application and specified in the appropriate variable within the py file.

