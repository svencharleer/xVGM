import json

# first attempt at converting LoL to xAPI format
# created by Sven Charleer / Francisco Gutierrez (firstname.lastname@kuleuven.be)
# June 2018

# Compare values of players
def comparePlayerStats(stats1, stats2):
    changedStats = {}
    for key in stats2:
        if not stats1[key] == stats2[key]:
                originalValue = stats1[key]
                newValue = stats2[key]
                changedStats[key] = [originalValue, newValue]
    return changedStats

# difficulties:
# no event information, just stats, makes it hard to deduce who does damage to who
# can only have approximation
#

def createActor(stats,playerKey):
    actor = {}
    if "x" in stats:
        actor["x"] = stats["x"]
    if "y" in stats:
        actor["y"] = stats["y"]
    if "h" in stats:
        actor["health"] = stats["h"]
    if "p" in stats:
        actor["mana"] = stats["p"]
    if "cg" in stats:
        actor["credits"] = stats["cg"]
    if "xp" in stats:
        actor["experience"] = stats["xp"]
    if "level" in stats:
        actor["level"] = stats["level"]
    if "items" in stats:
        actor["inventory"] = stats["items"]
    if "teamId" in stats:
        actor["team"] = stats["teamId"]
    else:
        actor["team"] = basicPlayerData[playerKey]["team"]
    if "summonerName" in stats:
        actor["playerName"] = stats["summonerName"]
    else:
        actor["playerName"] = basicPlayerData[playerKey]["playerName"]

    return actor

def createContext(timestamp, value):
    context = {}
    context["timestamp"] = timestamp
    context["value"] = value
    return context

def createEvents(playerKey, players, differences, timestamp):
    xapiEvents = []
    player = players[playerKey]

    #create the actor first
    #actor = player, position,hp,mp,items,spells,cooldowns
    actor = createActor(player,playerKey)
    xapiEvent = {}

    #if nothing in differences, this is the first loop, init stage
    if len(differences) == 0:
        verb = "initialize"
        target = None
        context = createContext(timestamp, None)
        xapiEvent["actor"] = actor
        xapiEvent["verb"] = verb
        xapiEvent["target"] = target
        xapiEvent["context"] = context
        xapiEvents.append(xapiEvent)
        print xapiEvent
        return xapiEvents

    #if no differences, this player did nothing!
    if not playerKey in differences:
        return xapiEvents

    playerDifferences = differences[playerKey]



    # lets start by defining different verbs
    # health, mana, position, what about hitting others, is that data here?

    # damage dealt to champion
    if "tdc" in playerDifferences:
        verb = "damageDealt"
        target = None
        context = createContext(timestamp, playerDifferences["tdc"][1])
        #find champion who we damaged
        for targetKey in differences:
            if targetKey == playerKey:
                continue
            # if enemy's hp changed in the same timestamp, we can assume he got hit
            # by this player
            enemyDiff = differences[targetKey]
            if "h" in enemyDiff:
                target = basicPlayerData[targetKey]["playerName"]

        xapiEvent["actor"] = actor
        xapiEvent["verb"] = verb
        xapiEvent["target"] = target
        xapiEvent["context"] = context
        xapiEvents.append(xapiEvent)
        print xapiEvent

    if "h" in playerDifferences:
        verbFound = False
        if playerDifferences["h"][0] > playerDifferences["h"][1]:
            verbFound = True
            verb = "damageTaken"
            target = None
            context = createContext(timestamp, playerDifferences["h"][1]-playerDifferences["h"][0])
        # health regen ticks make for too many events
        elif playerDifferences["h"][0] < playerDifferences["h"][1]:
            #verbFound = True
            verb = "healthReceived"
            target = None
            context = createContext(timestamp, playerDifferences["h"][1]-playerDifferences["h"][0])

        if verbFound:
            #find champion who damaged me
            for targetKey in differences:
                if targetKey == playerKey:
                    continue
                # if enemy's damage changed in the same timestamp, we can assume we got hit
                # by this player
                enemyDiff = differences[targetKey]
                if "tdc" in enemyDiff:
                    target = basicPlayerData[targetKey]["playerName"]

            xapiEvent["actor"] = actor
            xapiEvent["verb"] = verb
            xapiEvent["target"] = target
            xapiEvent["context"] = context
            xapiEvents.append(xapiEvent)
            print xapiEvent

    if "death" in playerDifferences:
        if playerDifferences["death"]:
            verb = "died"
        else:
            verb = "respawned"
        target = None
        context = createContext(timestamp, None)
        xapiEvent["actor"] = actor
        xapiEvent["verb"] = verb
        xapiEvent["target"] = target
        xapiEvent["context"] = context
        xapiEvents.append(xapiEvent)
        print xapiEvent






        # context = dragons, wards in game, towers up..., team X stats, team Y stats
        # verb = move, ability, buy, ..
        # object = other player, mob, shop,.. .
    return xapiEvents


with open('fox_tl_enhanced.json', 'r') as f:
    data = json.load(f)


playerData = {}
basicPlayerData = {}
# each event
for event in data:
    # has 1 key but it's a number
    for key in event:
        timestamp = event[key]["t"]
        # get the player statistics
        if "playerStats" in event[key]:

            # go through each player and compare if
            # anything changed. if it did, add event!
            # but first make list of all players for each loop
            # as we need to find the target of some events
            players = {}
            differences = {}
            for playerKey in event[key]["playerStats"]:
                # add player to list
                player = event[key]["playerStats"][playerKey]


                # check if player already in list for diff check
                # then check differences
                # if not, add to that list (first loop)
                if playerKey in playerData:
                    # make copy of playerdata, and update
                    # so we keep all the previous values too
                    newPlayerData = dict(playerData[playerKey])
                    newPlayerData.update(player)
                    diff = comparePlayerStats(playerData[playerKey], newPlayerData)
                    differences[playerKey] = diff
                    players[playerKey] = newPlayerData
                else:
                    playerData[playerKey] = player
                    basicPlayerData[playerKey] = {}
                    basicPlayerData[playerKey]["playerName"] = player["summonerName"]
                    basicPlayerData[playerKey]["team"] = player["teamId"]


            for playerKey in players:
                    player = players[playerKey]

                    #verbs (can be multiple events in 1 timestamp)
                    events = createEvents(playerKey, players, differences, timestamp)
                    #update, replace the comparison player with this loop's data
                    playerData[playerKey].update(player)
