## PUBG Discord Bot

###
Program that maintains and updates a leaderboard for PUBG and posts that leaderboard to a discord server.

### Built With 
* Python
* [chicken-dinner](https://github.com/crflynn/chicken-dinner) (PUBG API wrapper) 
* AWS(Lambda, DynamoDB, and SQS)

### How It Works
* dinnerBotPoster.py (Poster) and dinnerBotUpdater.py (Updater) are set up as Lambda functions. 
* DynamoDB is used to host a table of individual wins and a leaderboard of totaled wins. 
* Updater runs every hour and checks PUBG for any new wins
* Once any wins are added to the wins table, Updater sends a message containing results to Poster.
* If new wins have been collected, Poster posts the leaderboard to Discord.
* If no wins have been collected, Poster does not do anything.
