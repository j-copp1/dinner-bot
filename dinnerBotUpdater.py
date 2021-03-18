from chicken_dinner.pubgapi import PUBG
import config
import boto3
import time
from boto3.dynamodb.conditions import Key

#gets recent wins for every username in dinnerboard
def getMatches():

    ##init db connection
    dynamodb = boto3.resource('dynamodb')
    dinnerBoardTable = dynamodb.Table('PUBG_DinnerBoard')
    dinnersTable = dynamodb.Table('PUBG_Dinners')

    times = []

    #get names from database
    names = [i['username'] for i in dinnerBoardTable.scan()['Items']] # <--------- NAMES

    #get most recent times from database
    for name in names : 
        currName = name
        #get last updated time for name
        response = dinnersTable.query(
            KeyConditionExpression=Key('username').eq(currName)
        )
        mostRecentTime = response['Items'][len(response['Items']) - 1]['timestamp']
        times.append(mostRecentTime) # <------------ TIMES

    #get wins since last recorded win time

    pubg = PUBG(config.PUBGAPIKEY, "pc-na")

    #search every player in dinnerboard
    for currPlayerName in names: #<---------------------------------remove to run fully

        #wins to add to pubg_dinners table
        wins = []

        #get matches in last 14 days
        currPlayerId = pubg.players_from_names(currPlayerName)[0].id
        lastMatchesId = pubg.players_from_names(currPlayerName)[0].match_ids
        

        #get matches since last win
        uncountedMatchesId = []
        for m in lastMatchesId :
            convertedTime = time.mktime(time.strptime(pubg.match(m).created_at, "%Y-%m-%dT%H:%M:%SZ"))
            if times[0] < convertedTime :
                uncountedMatchesId.append(m)

        #get wins 
        for m in uncountedMatchesId :
            winners = pubg.match(m).winner
            #game is win, if not discard match
            if currPlayerName in winners.player_names :
                for winner in winners.participants :
                    if currPlayerName == winner.name :
                        wins.append({
                            'username' : winner.name,
                            'timestamp' : int(time.mktime(time.strptime(pubg.match(m).created_at, "%Y-%m-%dT%H:%M:%SZ"))),
                            'boardStatus' : False,
                            'gameId' : m,
                            'dps' : int(winner.stats['damage_dealt']),
                            'kills' : int(winner.stats['kills'])
                        })

        #WINS WINS WINS WINS UPLOAD TO DYNAMODB PUBG DINNERS
        for win in wins : 
            print(win)
            dinnersTable.put_item(Item={
                'username' : win['username'],
                'timestamp' : win['timestamp'],
                'dps' : win['dps'],
                'kills' : win['kills'],
                'gameId' : win['gameId'],
                'boardStatus' : win['boardStatus']
            })

#updates dinnerboard and sends a sqs message to trigger dinnerBotUpdater
def updateDinnerboard():

    #init connection to tables
    dynamodb = boto3.resource('dynamodb')
    dinnerBoardTable = dynamodb.Table('PUBG_DinnerBoard')
    dinnersTable = dynamodb.Table('PUBG_Dinners')

    #get names from database
    names = [i['username'] for i in dinnerBoardTable.scan()['Items']] # <--------- NAMES

    #get wins from pubg_dinners that have not been counted, boardStatus == False - also change to True once added
    dinnersToAdd = []

    #get uncounted dinners
    for name in names[2:3] :
        response = dinnersTable.query(
            KeyConditionExpression=Key('username').eq(name)
        )
        for r in response['Items'] :
            if r['boardStatus'] == False :
                dinnersToAdd.append(r)
 
    #change dinner counted status to true
    for d in dinnersToAdd :
        
        response = dinnersTable.update_item(
            Key={
                'username' : d['username'],
                'timestamp' : d['timestamp']
            },
            UpdateExpression = 'SET boardStatus = :values',
            ExpressionAttributeValues={
                ':values' : True
            }
        )
        

    #add uncounted dinners to dinnerboard
    for d in dinnersToAdd :

        response = dinnerBoardTable.query(
            KeyConditionExpression=Key('username').eq(d['username'])
        )['Items'][0]
        x = response['topDps'] if response['topDps'] > d['dps'] else d['dps']

        updatedResponse = dinnerBoardTable.update_item(
            Key={
                'username' : d['username']
            },
            UpdateExpression = 'SET kills = :k, topKills = :tK, topDps = :tD, wins = :w',
            ExpressionAttributeValues = {
                ':k' : response['kills'] + d['kills'],
                ':tK' : response['topKills'] if response['topKills'] > d['kills'] else d['kills'],
                ':tD' : response['topDps'] if response['topDps'] > d['dps'] else d['dps'],
                ':w' : response['wins'] + 1
            }
        ) 

    #send message to updatelistener using SQS
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(
        QueueName='gaucho.fifo' #<------ QUEUE NAME
    )

    response = queue.send_message(
        MessageBody='st louis',
        MessageGroupId='post_dinner_board'
    )
    print(response)

#getMatches()
#updateDinnerboard()