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
# using df_from_excel (given by stackoverflow.com/questions/41722374/pandas-read-excel-values-not-formulas)
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
    num_games_include = average_num_games if len(data.index) >= average_num_games else len(data.index)
    data_points_mean = data.iloc[range(num_games_include), :].describe().loc[
        "mean"]  # gets the category stats and finds mean from last x games
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

    player_df.to_pickle('./dataframes/player_df')
    team_average_df.to_pickle('./dataframes/team_df')

    return team_average_df, player_df


def create_head2head_db(team_average_df):
    i = 0
    # fix TOV
    buffer = 0.02  # buffer is used so that wins are not declared on tight calls
    results = np.empty(shape=(len(team_average_df.index), len(team_average_df.index)), dtype=object)
    for team1, data_series1 in team_average_df.iterrows():
        ii = 0
        for team2, data_series2 in team_average_df.iterrows():
            test = data_series1[:8] > (data_series2[:8] + buffer * data_series2[:8])
            test_TOV = data_series1[8] < (data_series2[8] - buffer * data_series2[8])
            won = sum(test) + test_TOV
            test = data_series1[:8] < (data_series2[:8] - buffer * data_series2[:8])
            test_TOV = data_series1[8] > (data_series2[8] + buffer * data_series2[8])
            lost = sum(test) + test_TOV
            drew = len(data_series2) - won - lost
            results[i][ii] = f'{won}-{drew}-{lost}'
            ii += 1
            if data_series1.index[8] != 'TOV':
                raise Exception(f'TOV no longer 8th index')

        i += 1
    return pd.DataFrame(results, index=list(team_average_df.index), columns=list(team_average_df.index))


def rank_team_categories(team_average_df):
    rank_df1 = team_average_df1.iloc[:, :8].rank(ascending = False)
    rank_df2 = team_average_df1.iloc[:, 8].rank(ascending = True)
    result = pd.concat([rank_df1, rank_df2], axis=1)
    return result


rosters = pd.read_excel('static_league_analysis.xlsx', 'team_roster')
average_of_games = 15
team_number = 12
num_active_players = 10
team_names = rosters.loc[range(team_number), 'Teams']
required_stats = ['FGM', 'FGA', 'FG_PCT', 'FG3M', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PTS']
update_data_flag = 1

# find team roster averages and player stats
if update_data_flag:
    team_average_df1, player_df1 = create_team_db(rosters)
else:
    team_average_df1 = pd.read_pickle('./dataframes/team_df')
    player_df1 = pd.read_pickle('./dataframes/player_df')
head2head_df = create_head2head_db(team_average_df1)
team_ranking = rank_team_categories(team_average_df1)
# options = {}
# options['strings_to_formulas'] = False
# options['strings_to_urls'] = False
with pd.ExcelWriter('python_league_analysis.xlsx', engine='openpyxl') as writer:
# writer = pd.ExcelWriter('python_league_analysis.xlsx', engine='openpyxl')
    rosters.iloc[:, 1:].to_excel(writer, sheet_name='rosters')
    player_df1.to_excel(writer, sheet_name='player_averages')
    team_average_df1.to_excel(writer, sheet_name='team_averages')
    head2head_df.to_excel(writer, sheet_name='team_Head2Head')
    team_ranking.to_excel(writer, sheet_name='team_ranking')

with pd.ExcelWriter('python_league_analysis.xlsx', engine='openpyxl', mode='a') as writer:
    team_ranking.sum(axis = 1).sort_values(ascending = True).to_excel(writer, sheet_name='team_ranking')
# data_filtered.to_excel(writer, "Main", cols=['Diff1', 'Diff2'])
# writer.save()
# writer.close()
