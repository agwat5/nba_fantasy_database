# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 10:26:13 2021

@author: andre
"""

# We will be using pandas dataframes to manipulate the data
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from time import sleep
import re

import json

# https://stackoverflow.com/questions/58178719/append-pandas-dataframe-to-excelsheet-not-overwrite-it?noredirect=1&lq=1
#using df_from_excel (given by stackoverflow.com/questions/41722374/pandas-read-excel-values-not-formulas)
# df_from_excel used as pandas is reading formulas as NaN
import xlwings as xl
def df_from_excel(path, sheet_name):
    book = load_workbook(path)
    writer = pd.ExcelWriter(path, engine='openpyxl')
    writer.book = book
    ## ExcelWriter for some reason uses writer.sheets to access the sheet.
    ## If you leave it empty it will not know that sheet Main is already there
    ## and will create a new sheet.
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    writer.save()
    writer.close()
    return pd.read_excel(path, sheet_name)



def search_player_id(dict_player, fullname):
    """Find the id for each player (id is permanent and used by nba stats)"""
    for i in dict_player:
        name = fullname.split(' ', 1)
        first_name = name[0]
        last_Name = name[1]
        if i['firstName'] == first_name and i['lastName'] == last_Name:
            return i['playerId']
    raise Exception(f'Failed to find player {fullname}')


def player_stat_average(player_name, average_num_games):
    """ Function returns the players average statistics as a series which can be appended to a dataframe"""
    try:
        with open('players.json') as players_json:
            person_dict = json.load(players_json)
            player_id = search_player_id(person_dict, player_name)

        # player_id = players.find_players_by_full_name(player_name)[0]['id'] # hasnt been updated with rookies
    except:
        raise Exception(f'Failed to find player {player_name}')
        return
    try:
        player_gamelog = playergamelog.PlayerGameLog(player_id=str(player_id), season='2020',
                                                     season_type_all_star='Regular Season')
    except:
        raise Exception(f'Failed to get data on player {player_name}')
    sleep(0.25)

    data = player_gamelog.get_data_frames()[0][required_stats]
    num_games_include = average_num_games if len(data.index) >= average_num_games else  len(data.index)
    data_points_mean = data.iloc[range(num_games_include), :].describe().loc["mean"]  # gets the category stats and finds mean from last x games
    data_points_mean = pd.concat([pd.Series({'Player_Name': player_name}), data_points_mean])

    return data_points_mean.rename(str(player_id))  # allows index to be player id in the dataframe


def create_team_db(rosters):
    player_df = pd.DataFrame()
    team_average_df = pd.DataFrame()

    team_names = rosters.loc[range(team_number), 'Teams']

    count = 0
    for team_name in team_names:
        for player in rosters[team_name][0:num_active_players]:
            series = player_stat_average(player, average_of_games)
            count += 1
            print(count)
            player_df = player_df.append(series)

        team_averaging = player_df.iloc[-9:, :].sum()
        team_averaging['FG_PCT'] = team_averaging['FGM'] / team_averaging['FGA']
        team_averaging['FT_PCT'] = team_averaging['FTM'] / team_averaging['FTA']
        team_averaging = team_averaging.drop('FGM')
        team_averaging = team_averaging.drop('FGA')
        team_averaging = team_averaging.drop('FTM')
        team_averaging = team_averaging.drop('FTA')
        team_averaging = team_averaging.drop('Player_Name')
        team_averaging = team_averaging.rename(str(team_name))

        team_average_df = team_average_df.append(team_averaging)

    return team_average_df, player_df

def create_head2head_db(team_average_df):
    i = 0
    buffer = 0.05  # buffer is used so that wins are not declared on tight calls
    results = np.empty(shape=(len(team_average_df.index), len(team_average_df.index)), dtype=object)
    for team1, data_series1 in team_average_df.iterrows():
        ii = 0
        for team2, data_series2 in team_average_df.iterrows():
            test = data_series1 > (data_series2 + buffer * data_series2)
            won = sum(test)
            test = data_series1 < (data_series2 - buffer * data_series2)
            lost = sum(test)
            drew = len(test) - won - lost
            results[i][ii] = f'{won}-{drew}-{lost}'
            ii += 1
        i += 1
    return pd.DataFrame(results, index=list(team_average_df.index), columns=list(team_average_df.index))



rosters = df_from_excel(path = 'league_analysis.xlsx', sheet_name='team_roster')
average_of_games = 11
team_number = 12
num_active_players = 10
team_names = rosters.loc[range(team_number), 'Teams']
required_stats = ['FGM', 'FGA', 'FG_PCT', 'FG3M', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PTS']


# find team roster averages and player stats
team_average_df1, player_df1 = create_team_db(rosters)

head2head_df = create_head2head_db(team_average_df1)

options = {}
options['strings_to_formulas'] = False
options['strings_to_urls'] = False

book = load_workbook('league_analysis.xlsx')
writer = pd.ExcelWriter('league_analysis.xlsx', engine='openpyxl')
writer.book = book
## ExcelWriter for some reason uses writer.sheets to access the sheet.
## If you leave it empty it will not know that sheet Main is already there
## and will create a new sheet.
writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
player_df1.to_excel(writer, sheet_name='player_averages')
team_average_df1.to_excel(writer, sheet_name='team_averages')
head2head_df.to_excel(writer, sheet_name='team_Head2Head')
# data_filtered.to_excel(writer, "Main", cols=['Diff1', 'Diff2'])
writer.save()
writer.close()


# book = load_workbook('league_analysis.xlsx')
# with pd.ExcelWriter('league_analysis.xlsx') as writer: # , engine = 'openpyxl'
#     writer.book = book
#     player_df1.to_excel(writer, sheet_name='player_averages')
#     team_average_df1.to_excel(writer, sheet_name='team_averages')
#     head2head_df.to_excel(writer, sheet_name='team_Head2Head')



# z = player_stat_average('Luka Doncic', 3)

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
