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
from itertools import combinations 
import json
from itertools import compress
from operator import truediv
#from scipy.stats import rankdata

# https://stackoverflow.com/questions/58178719/append-pandas-dataframe-to-excelsheet-not-overwrite-it?noredirect=1&lq=1
# using df_from_excel (given by stackoverflow.com/questions/41722374/pandas-read-excel-values-not-formulas)
# df_from_excel used as pandas is reading formulas as NaN
import xlwings as xl

def create_league_db():
    """Function will go through the 2020-2021 nba player list and grab all game data from this season"""
    player_df = pd.DataFrame()
    # team_names = rosters.loc[range(team_number), 'Teams']

    with open('players.json') as players_json:
        person_dict = json.load(players_json)
        # player_id = search_player_id(person_dict, player_name)

    count = 0

    for player in person_dict:
        player_name = f"{player['firstName']} {player['lastName']}"
        player_id = player['playerId']
        temp_df = player_season_stats(player_name, player_id)
        count += 1
        print(f'{count}/{len(person_dict)}')
        player_df[player_name] = [temp_df.to_dict()]
        #df1.loc[0,0] = [df2.to_dict()] to store df as dict
        #pd.DataFrame(df1.loc[0,0][0]) to restore df


    player_df.to_pickle('./dataframes/season_stats_player_df')


    return


def player_season_stats(player_name, player_id):
    """ Function returns the players season statistics as a df which can be appended to a dataframe"""

    try:
        player_gamelog = playergamelog.PlayerGameLog(player_id=str(player_id), season='2020',
                                                     season_type_all_star='Regular Season')
    except:
        raise Exception(f'Failed to get data on player {player_name}')
    sleep(0.25)
    temp = required_stats.copy()
    temp.extend(['GAME_DATE', 'Player_ID'])
    data = player_gamelog.get_data_frames()[0][temp]

    return data  # return data as df which will be added to another larger df as a dictionary


# def df_from_excel(path, sheet_name):
#     book = load_workbook(path)
#     writer = pd.ExcelWriter(path, engine='openpyxl')
#     writer.book = book
#     ## ExcelWriter for some reason uses writer.sheets to access the sheet.
#     ## If you leave it empty it will not know that sheet Main is already there
#     ## and will create a new sheet.
#     writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
#     writer.save()
#     writer.close()
#     return pd.read_excel(path, sheet_name)


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
    if num_games_include>0:
        data_points_mean = data.iloc[range(num_games_include), :].describe().loc[
            "mean"]  # gets the category stats and finds mean from last x games
    else:
        data_points_mean = pd.Series(np.zeros(len(required_stats)),required_stats)
    data_points_mean = pd.concat([pd.Series({'Player_Name': player_name}), data_points_mean])

    return data_points_mean.rename(str(player_id))  # allows index to be player id in the dataframe


def create_team_db(rosters):
    player_df = pd.DataFrame()
    team_average_df = pd.DataFrame()

    team_names = rosters.loc[range(team_number), 'Teams']

    count = 0
    for team_name in team_names:
        for player in rosters[team_name][:]:
            count += 1
            print(f'{player}-{count}/{len(team_names) * len(rosters)}')
            series = player_stat_average(player, average_of_games)
            player_df = player_df.append(series)


        team_averaging = player_df.iloc[-len(rosters):-3, :].sum()
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


def rank_team_categories(team_average_df1):
    rank_df1 = team_average_df1.iloc[:, :8].rank(ascending = False)
    rank_df2 = team_average_df1.iloc[:, 8].rank(ascending = True)
    result = pd.concat([rank_df1, rank_df2], axis=1)
    return result

def team_compare(data_series1, data_series2):
    data_series2 = data_series2.sort_index()
    data_series1 = data_series1.sort_index()

    test = data_series1[:8] > (data_series2[:8])
    test_TOV = data_series1[8] < (data_series2[8])
    won = sum(test) + test_TOV
    if won > 0:
        winning_margin = data_series1 - data_series2
        winning_indices = list(test)
        winning_indices.append(test_TOV)
        winning_margin = sum(list(map(truediv, np.abs(list(compress(winning_margin, winning_indices))), np.abs(list(compress(data_series2, winning_indices))))))
    else:
        winning_margin =0

    # test = data_series1[:8] < (data_series2[:8] - buffer * data_series2[:8])
    # test_TOV = data_series1[8] > (data_series2[8] + buffer * data_series2[8])
    # lost = sum(test) + test_TOV
    # drew = len(data_series2) - won - lost
    # results[i][ii] = f'{won}-{drew}-{lost}'
    # ii += 1
    # if data_series1.index[8] != 'TOV':
    #     raise Exception(f'TOV no longer 8th index')
    return won, winning_margin

def team_optimiser(roster, optimised_team, opponent_team):
    # team_names = roster.loc[range(team_number), 'Teams']
    player_df = pd.read_pickle('./dataframes/player_df')
    team_db = pd.read_pickle('./dataframes/team_df')
    opponent_stats = team_db.loc[opponent_team,:]

    roster_combinations = combinations(range(13), 10)
    won = []
    winning_margin = []
    possible_team_roster = []
    for count, possible_team_ind in enumerate(roster_combinations):
        possible_team_roster.append(list(roster.loc[list(possible_team_ind), optimised_team]))

        # data = pd.DataFrame(League_db[player][0])

        my_team_df = pd.DataFrame()
        for player in possible_team_roster[count]:
            with open('players.json') as players_json:
                person_dict = json.load(players_json)
                player_id = search_player_id(person_dict, player)

            series = player_df.loc[str(player_id), :]
            my_team_df = my_team_df.append(series)

        team_averaging = my_team_df.iloc[:, :].sum()
        team_averaging['FG_PCT'] = team_averaging['FGM'] / team_averaging['FGA']
        team_averaging['FT_PCT'] = team_averaging['FTM'] / team_averaging['FTA']
        team_averaging = team_averaging.drop('FGM')
        team_averaging = team_averaging.drop('FGA')
        team_averaging = team_averaging.drop('FTM')
        team_averaging = team_averaging.drop('FTA')
        team_averaging = team_averaging.drop('Player_Name')
        team_averaging = team_averaging.rename(str(optimised_team))

        x, y = team_compare(team_averaging, opponent_stats)
        won.append(x)
        winning_margin.append(y)
    indices = [count for count, number in enumerate(won) if number == max(won)]
    # [won[i] for i in indices]
    best_team = [(winning_margin[i], i) for i in indices]

    # take first element for sort
    def takefirst(elem):
        return elem[0]
    # sort list with key
    best_team.sort(key=takefirst, reverse = True)

    top_5_teams_ind = [lis[1] for lis in best_team[0:5]]
    possible_team_roster = np.array(possible_team_roster)
    print(possible_team_roster[top_5_teams_ind,:])
    print(best_team[0:5])

    return won, winning_margin

rosters = pd.read_excel('static_league_analysis.xlsx', 'team_roster')
average_of_games = 15
team_number = 12
num_active_players = 10
team_names = rosters.loc[range(team_number), 'Teams']
required_stats = ['FGM', 'FGA', 'FG_PCT', 'FG3M', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PTS']
update_data_flag = 1

league_db = pd.read_pickle('./dataframes/season_stats_player_df')



# create_league_db()
# find team roster averages and player stats
if update_data_flag:
    team_average_df1, player_df1 = create_team_db(rosters)
else:
    team_average_df1 = pd.read_pickle('./dataframes/team_df')
    player_df1 = pd.read_pickle('./dataframes/player_df')
head2head_df = create_head2head_db(team_average_df1)
team_ranking = rank_team_categories(team_average_df1)

won, winning_margin = team_optimiser(rosters, team_names[4], team_names[9])

# Use league stats to find ideal team roster for upcoming round


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
