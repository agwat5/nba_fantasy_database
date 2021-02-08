# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 10:26:13 2021

@author: andre
"""

# First we import the endpoint
# We will be using pandas dataframes to manipulate the data
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd 
import pandas
import math
from numpy import mean
from time import sleep
import re

import json


rosters = pandas.read_excel('league_analysis.xlsx', sheet_name='team_roster')
average_of_games = 10
team_number = 12
num_active_players = 10
team_names = rosters.loc[range(team_number),'Teams']
requiredstats = ['FGM','FGA','FG_PCT','FG3M','FTM','FTA','REB','AST','STL','BLK','TOV','PTS']


def search_player_id(dict_player,fullname):
    for i in dict_player:
        name = fullname.split(' ', 1)
        first_name = name[0]
        last_Name = name[1]
        if i['firstName'] == first_name and  i['lastName'] == last_Name:
            return i['playerId']
    raise Exception(f'Failed to find player {player_name}') 
    
def player_stat_average(player_name, average_of_games):
    """ Function returns the players average statistics as a series which can be appended to a dataframe"""
    try:
        with open('players.json') as players_json:
            person_dict = json.load(players_json)
            player_id = search_player_id(person_dict,player_name)
                        
        # player_id = players.find_players_by_full_name(player_name)[0]['id'] # hasnt been updated with rookies
        sleep(0.25)
    except:
        raise Exception(f'Failed to find player {player_name}')
        return
    try:
        player_gamelog = playergamelog.PlayerGameLog(player_id=str(player_id), season = '2020', season_type_all_star = 'Regular Season')
    except:
        raise Exception(f'Failed to get data on player {player_name}')
    sleep(0.25)
    
    data = player_gamelog.get_data_frames()[0][requiredstats]
    data_points_mean = data.iloc[range(average_of_games),:].describe().iloc[1] #gets the category stats and finds mean from last x games
    
    return data_points_mean.rename(str(player_id)) #allows index to be player id in the dataframe

# print(player_stat_average("Tyrese Haliburton", average_of_games))
# series = player_stat_average('OG Anunoby', average_of_games)
count = 0
for team_name in team_names:
    for player in rosters[team_name][0:num_active_players]:
        series = player_stat_average(player, average_of_games)
        count += 1
        print(count)
        if 'df' not in locals():
            df = pd.DataFrame(series).transpose()
        else:
            df = df.append(series) 
# 1630169
        
    
    
    
    
#z = player_stat_average('Luka Doncic', 3)

# print whole sheet data




# x = players.find_players_by_full_name('Luka Doncic')

# #Call the API endpoint passing in lebron's ID & which season 
# gamelog_bron = playergamelog.PlayerGameLog(player_id='2544', season = '2021')

# #Converts gamelog object into a pandas dataframe
# #can also convert to JSON or dictionary  
# df_bron_games_2018 = gamelog_bron.get_data_frames()

# # If you want all seasons, you must import the SeasonAll parameter 
# from nba_api.stats.library.parameters import SeasonAll

# gamelog_bron_all = playergamelog.PlayerGameLog(player_id='2544', season = SeasonAll.all)

# df_bron_games_all = gamelog_bron_all.get_data_frames()























# import requests

# #url
# url = 'https://stats.nba.com/stats/leaguedashplayerstats?'

# #request headers
# request_headers = {
# 'Accept': 'application/json, text/plain, */*',
# 'Accept-Encoding':'gzip, deflate, br',
# 'Accept-Language': 'en-US,en;q=0.9',
# 'Connection': 'keep-alive',
# 'Host': 'stats.nba.com',
# 'Origin': 'https://www.nba.com',
# 'Referer': 'https://www.nba.com/',
# 'Sec-Fetch-Dest': 'empty',
# 'Sec-Fetch-Mode': 'cors',
# 'Sec-Fetch-Site': 'same-site',
# 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
# 'x-nba-stats-origin': 'stats',
# 'x-nba-stats-token': 'true',
# }

# #params
# parameters = {
# 'College':'' ,
# 'Conference':'',
# 'Country':'' ,
# 'DateFrom': '',
# 'DateTo': '',
# 'Division': '',
# 'DraftPick': '',
# 'DraftYear': '',
# 'GameScope': '',
# 'GameSegment': '', 
# 'Height': '',
# 'LastNGames': 0,
# 'LeagueID': 00,
# 'Location': '',
# 'MeasureType': 'Base',
# 'Month': 0,
# 'OpponentTeamID': 0,
# 'Outcome': '',
# 'PORound': 0,
# 'PaceAdjust': 'N',
# 'PerMode': 'PerGame',
# 'Period': 0,
# 'PlayerExperience': '',
# 'PlayerPosition': '',
# 'PlusMinus': 'N',
# 'Rank': 'N',
# 'Season': '2020-21',
# 'SeasonSegment': '',
# 'SeasonType': 'Regular Season',
# 'ShotClockRange': '',
# 'StarterBench': '',
# 'TeamID': 0,
# 'TwoWay': 0,
# 'VsConference': '',
# 'VsDivision': '',
# 'Weight': ''
#     }