from prettytable import PrettyTable
from discord_webhook import DiscordWebhook, DiscordEmbed
import boto3
import config

dynamodb = boto3.resource('dynamodb')
dinnerBoardTable = dynamodb.Table(config.dinnerBoardTable)

#get dinnerboard from db and format 
entries = dinnerBoardTable.scan()['Items']
dinner_board = PrettyTable()

dinner_board.add_column('Username', [i['username'] for i in entries])
dinner_board.add_column('Wins', [i['wins'] for i in entries])
dinner_board.add_column('Kills', [i['kills'] for i in entries])
dinner_board.add_column('Top Kills', [i['topKills'] for i in entries])
dinner_board.add_column('Top Dps', [i['topDps'] for i in entries])

dinner_board.sortby = 'Wins'
dinner_board.reversesort = True
dinner_board.align = 'c'

#print dinnerboard to discord using webhook
webhook = DiscordWebhook(url=config.WEBHOOK_URL) 
embed = DiscordEmbed(title='Dinner Board', description = '```\n' + dinner_board.get_string() + '```')
webhook.add_embed(embed)
response = webhook.execute()
