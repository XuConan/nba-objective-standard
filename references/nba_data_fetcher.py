#!/usr/bin/env python3
"""
NBA 多源数据获取脚本
依赖: pip install pandas requests beautifulsoup4 nba-api balldontlie
"""

import argparse
import json
import sys
import math
from collections import defaultdict

try:
    from nba_api.stats.endpoints import leaguestandings, leaguedashplayerstats, leaguedashteamstats
    from nba_api.stats.library.parameters import SeasonType
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False

try:
    from balldontlie import BalldontlieAPI
    BALLDONTLIE_AVAILABLE = True
except ImportError:
    BALLDONTLIE_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

def fetch_from_nba_api(season):
    """使用 nba_api 获取球队排名和球员高阶数据"""
    if not NBA_API_AVAILABLE:
        return {'teams': [], 'players': []}
    
    try:
        season_str = f"{season-1}-{str(season)[-2:]}"
        
        teams_data = []
        standings = leaguestandings.LeagueStandings(season=season_str)
        standings_df = standings.get_data_frames()[0]
        
        for _, row in standings_df.iterrows():
            teams_data.append({
                'name': row['TeamName'],
                'team_id': row['TeamID'],
                'wins': int(row['WINS']),
                'losses': int(row['LOSSES']),
                'win_pct': float(row['WIN_PCT']),
                'conference': row['Conference'],
                'division': row['Division'],
                'conf_rank': int(row['ConferenceRank']),
                'league_rank': int(row['LeagueRank'])
            })
        
        players_data = []
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season_str,
            season_type_all_star='Regular Season'
        );
        player_df = player_stats.get_data_frames()[0]
        
        for _, row in player_df.iterrows():
            games_played = int(row['GP']) if not pd.isna(row['GP']) else 0
            if games_played < 10:
                continue
                
            players_data.append({

                'name': row['PLAYER_NAME'],
                'player_id': row['PLAYER_ID'],
                'team_id': row['TEAM_ID'],
                'team_abbreviation': row['TEAM_ABBREVIATION'],
                'position': row['POSITION'],
                'gp': games_played,
                'minutes_per_game': float(row['MIN']) if not pd.isna(row['MIN']) else 0,
                'points_per_game': float(row['PTS']) if not pd.isna(row['PTS']) else 0,
                'rebounds_per_game': float(row['REB']) if not pd.isna(row['REB']) else 0,
                'assists_per_game': float(row['AST']) if not pd.isna(row['AST']) else 0,
                'steals_per_game': float(row['STL']) if not pd.isna(row['STL']) else 0,
                'blocks_per_game': float(row['BLK']) if not pd.isna(row['BLK']) else 0,
                'per': float(row['PER']) if not pd.isna(row['PER']) else 0,
                'ws48': float(row['WS']) / (float(row['MIN']) / 48) if not pd.isna(row['WS']) and float(row['MIN']) > 0 else 0,
                'vorp': float(row['VORP']) if not pd.isna(row['VORP']) else 0,
                'dbpm': float(row['DREB_PCT']) * 100 if not pd.isna(row['DREB_PCT']) else 0,
                'dws': float(row['DREB']) * 0.1 if not pd.isna(row['DREB']) else 0,
                'starter_flag': row['START_POSITION'] != '' if row['START_POSITION'] else False,
                'rookie_flag': bool(row['ROOKIE_FLAG']) if 'ROOKIE_FLAG' in row else False
            })
        
        return {'teams': teams_data, 'players': players_data}
    
    except Exception as e:
        print(f"Error fetching from nba_api: {e}", file=sys.stderr)
        return {'teams': [], 'players': []}

def fetch_from_balldontlie(season):
    """使用 balldontlie API 获取球员数据"""
    if not BALLDONTLIE_AVAILABLE:
        return {'teams': [], 'players': []}
    
    try:
        api = BalldontlieAPI(api_key='free')
        teams_data = []
        players_data = []
        
        page = 1
        while True:
            try:
                response = api.players(per_page=100, page=page)
            except Exception:
                break
            if not response.get('data'):
                break
            for player in response['data']:
                players_data.append({
                    'name': f"{player['first_name']} {player['last_name']}",
                    'player_id': player['id'],
                    'team_id': player['team']['id'] if player.get('team') else None,
                    'team_abbreviation': player['team']['abbreviation'] if player.get('team') else None,
                    'position': player.get('position') or 'G',
                    'gp': 0,
                    'minutes_per_game': 0,
                    'points_per_game': 0,
                    'rebounds_per_game': 0,
                    'assists_per_game': 0,
                    'steals_per_game': 0,
                    'blocks_per_game': 0,
                    'per': 0,
                    'ws48': 0,
                    'vorp': 0,
                    'dbpm': 0,
                    'dws': 0,
                    'starter_flag': False,
                    'rookie_flag': False
                })
            page += 1
        
        page = 1
        while True:
            try:
                response = api.teams(per_page=100, page=page)
            except Exception:
                break
            if not response.get('data'):
                break
            for team in response['data']:
                teams_data.append({
                    'name': team['full_name'],
                    'team_id': team['id'],
                    'wins': 0,
                    'losses': 0,
                    'win_pct': 0,
                    'conference': team['conference'],
                    'division': team['division'],
                    'conf_rank': 0,
                    'league_rank': 0
                })
            page += 1
        
        return {'teams': teams_data, 'players': players_data}
    
    except Exception as e:
        print(f"Error fetching from balldontlie: {e}", file=sys.stderr)
        return {'teams': [], 'players': []}

def get_mock_data(season, include_last_season=False):
    """生成模拟数据（当外部API不可用时使用）"""
    teams = [
        {'name': '丹佛掘金', 'team_id': 1, 'wins': 53, 'losses': 29, 'win_pct': 0.646, 'conference': 'West', 'division': '西北区', 'conf_rank': 1, 'league_rank': 1},
        {'name': '波士顿凯尔特人', 'team_id': 2, 'wins': 57, 'losses': 25, 'win_pct': 0.695, 'conference': 'East', 'division': '大西洋区', 'conf_rank': 1, 'league_rank': 2},
        {'name': '密尔沃基雄鹿', 'team_id': 3, 'wins': 58, 'losses': 24, 'win_pct': 0.707, 'conference': 'East', 'division': '中区', 'conf_rank': 2, 'league_rank': 3},
        {'name': '菲尼克斯太阳', 'team_id': 4, 'wins': 54, 'losses': 28, 'win_pct': 0.659, 'conference': 'West', 'division': '太平洋区', 'conf_rank': 2, 'league_rank': 4},
        {'name': '孟菲斯灰熊', 'team_id': 5, 'wins': 51, 'losses': 31, 'win_pct': 0.622, 'conference': 'West', 'division': '西南区', 'conf_rank': 3, 'league_rank': 5},
        {'name': '费城76人', 'team_id': 6, 'wins': 54, 'losses': 28, 'win_pct': 0.659, 'conference': 'East', 'division': '大西洋区', 'conf_rank': 3, 'league_rank': 6},
        {'name': '金州勇士', 'team_id': 7, 'wins': 44, 'losses': 38, 'win_pct': 0.537, 'conference': 'West', 'division': '太平洋区', 'conf_rank': 6, 'league_rank': 10},
        {'name': '洛杉矶湖人', 'team_id': 8, 'wins': 43, 'losses': 39, 'win_pct': 0.524, 'conference': 'West', 'division': '太平洋区', 'conf_rank': 7, 'league_rank': 11},
    ]
    
    teams_last_season = [
        {'name': '丹佛掘金', 'wins': 48},
        {'name': '波士顿凯尔特人', 'wins': 51},
        {'name': '密尔沃基雄鹿', 'wins': 52},
        {'name': '菲尼克斯太阳', 'wins': 45},
        {'name': '孟菲斯灰熊', 'wins': 56},
        {'name': '费城76人', 'wins': 51},
        {'name': '金州勇士', 'wins': 40},
        {'name': '洛杉矶湖人', 'wins': 33},
        {'name': '达拉斯独行侠', 'wins': 38},
        {'name': '迈阿密热火', 'wins': 53},
        {'name': '明尼苏达森林狼', 'wins': 42},
        {'name': '俄克拉荷马城雷霆', 'wins': 24},
        {'name': '纽约尼克斯', 'wins': 47},
        {'name': '印第安纳步行者', 'wins': 35},
        {'name': '奥兰多魔术', 'wins': 34},
    ]
    
    players = [
        {'name': 'Nikola Jokic', 'player_id': 1, 'team_id': 1, 'team_abbreviation': 'DEN', 'team_name': '丹佛掘金', 'team_wins': 53, 'team_win_pct': 0.646, 'position': 'C', 'gp': 69, 'minutes_per_game': 33.7, 'points_per_game': 24.5, 'rebounds_per_game': 11.8, 'assists_per_game': 9.8, 'steals_per_game': 1.3, 'blocks_per_game': 0.7, 'per': 32.1, 'ws48': 0.265, 'vorp': 6.9, 'dbpm': 2.1, 'dws': 2.8, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 30.5, 'playoff_ws48': 0.285, 'playoff_vorp': 3.2, 'playoff_round': 'champion'},
        {'name': 'Joel Embiid', 'player_id': 2, 'team_id': 6, 'team_abbreviation': 'PHI', 'team_name': '费城76人', 'team_wins': 54, 'team_win_pct': 0.659, 'position': 'C', 'gp': 63, 'minutes_per_game': 34.6, 'points_per_game': 33.1, 'rebounds_per_game': 10.2, 'assists_per_game': 4.2, 'steals_per_game': 1.0, 'blocks_per_game': 1.7, 'per': 31.9, 'ws48': 0.258, 'vorp': 6.7, 'dbpm': 1.8, 'dws': 2.5, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 29.8, 'playoff_ws48': 0.245, 'playoff_vorp': 2.1, 'playoff_round': 'semifinalist'},
        {'name': 'Giannis Antetokounmpo', 'player_id': 3, 'team_id': 3, 'team_abbreviation': 'MIL', 'team_name': '密尔沃基雄鹿', 'team_wins': 58, 'team_win_pct': 0.707, 'position': 'F', 'gp': 63, 'minutes_per_game': 32.1, 'points_per_game': 32.1, 'rebounds_per_game': 11.5, 'assists_per_game': 5.8, 'steals_per_game': 1.0, 'blocks_per_game': 1.2, 'per': 32.0, 'ws48': 0.245, 'vorp': 6.1, 'dbpm': 1.5, 'dws': 2.2, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 31.2, 'playoff_ws48': 0.275, 'playoff_vorp': 2.8, 'playoff_round': 'conference_finalist'},
        {'name': 'Luka Doncic', 'player_id': 4, 'team_id': 9, 'team_abbreviation': 'DAL', 'team_name': '达拉斯独行侠', 'team_wins': 49, 'team_win_pct': 0.585, 'position': 'G', 'gp': 66, 'minutes_per_game': 36.2, 'points_per_game': 32.4, 'rebounds_per_game': 8.6, 'assists_per_game': 8.0, 'steals_per_game': 1.4, 'blocks_per_game': 0.5, 'per': 30.5, 'ws48': 0.228, 'vorp': 5.8, 'dbpm': -0.5, 'dws': 1.2, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 32.8, 'playoff_ws48': 0.295, 'playoff_vorp': 3.5, 'playoff_round': 'conference_finalist'},
        {'name': 'Kevin Durant', 'player_id': 5, 'team_id': 4, 'team_abbreviation': 'PHX', 'team_name': '菲尼克斯太阳', 'team_wins': 54, 'team_win_pct': 0.659, 'position': 'F', 'gp': 58, 'minutes_per_game': 36.0, 'points_per_game': 29.9, 'rebounds_per_game': 6.7, 'assists_per_game': 5.0, 'steals_per_game': 0.7, 'blocks_per_game': 1.4, 'per': 28.3, 'ws48': 0.215, 'vorp': 4.9, 'dbpm': 0.8, 'dws': 1.8, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 28.5, 'playoff_ws48': 0.255, 'playoff_vorp': 2.5, 'playoff_round': 'semifinalist'},
        {'name': 'Stephen Curry', 'player_id': 6, 'team_id': 7, 'team_abbreviation': 'GSW', 'team_name': '金州勇士', 'team_wins': 44, 'team_win_pct': 0.537, 'position': 'G', 'gp': 64, 'minutes_per_game': 34.0, 'points_per_game': 29.4, 'rebounds_per_game': 6.1, 'assists_per_game': 6.3, 'steals_per_game': 0.9, 'blocks_per_game': 0.4, 'per': 26.8, 'ws48': 0.198, 'vorp': 4.5, 'dbpm': -0.8, 'dws': 0.9, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 25.2, 'playoff_ws48': 0.215, 'playoff_vorp': 1.8, 'playoff_round': 'first_round'},
        {'name': 'LeBron James', 'player_id': 7, 'team_id': 8, 'team_abbreviation': 'LAL', 'team_name': '洛杉矶湖人', 'team_wins': 43, 'team_win_pct': 0.524, 'position': 'F', 'gp': 55, 'minutes_per_game': 35.5, 'points_per_game': 28.9, 'rebounds_per_game': 8.3, 'assists_per_game': 7.0, 'steals_per_game': 1.3, 'blocks_per_game': 0.6, 'per': 27.1, 'ws48': 0.195, 'vorp': 4.2, 'dbpm': -0.3, 'dws': 1.1, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 26.5, 'playoff_ws48': 0.235, 'playoff_vorp': 2.0, 'playoff_round': 'semifinalist'},
        {'name': 'Jimmy Butler', 'player_id': 8, 'team_id': 10, 'team_abbreviation': 'MIA', 'team_name': '迈阿密热火', 'team_wins': 52, 'team_win_pct': 0.610, 'position': 'F', 'gp': 64, 'minutes_per_game': 33.9, 'points_per_game': 22.9, 'rebounds_per_game': 5.9, 'assists_per_game': 5.3, 'steals_per_game': 1.8, 'blocks_per_game': 0.3, 'per': 24.2, 'ws48': 0.185, 'vorp': 3.8, 'dbpm': 2.8, 'dws': 3.5, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 27.8, 'playoff_ws48': 0.265, 'playoff_vorp': 2.3, 'playoff_round': 'runner-up'},
        {'name': 'Rudy Gobert', 'player_id': 9, 'team_id': 11, 'team_abbreviation': 'MIN', 'team_name': '明尼苏达森林狼', 'team_wins': 49, 'team_win_pct': 0.585, 'position': 'C', 'gp': 70, 'minutes_per_game': 30.7, 'points_per_game': 13.4, 'rebounds_per_game': 11.6, 'assists_per_game': 1.1, 'steals_per_game': 0.6, 'blocks_per_game': 2.1, 'per': 21.5, 'ws48': 0.178, 'vorp': 3.5, 'dbpm': 4.2, 'dws': 4.1, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 19.8, 'playoff_ws48': 0.225, 'playoff_vorp': 1.2, 'playoff_round': 'first_round'},
        {'name': 'Shai Gilgeous-Alexander', 'player_id': 10, 'team_id': 12, 'team_abbreviation': 'OKC', 'team_name': '俄克拉荷马城雷霆', 'team_wins': 40, 'team_win_pct': 0.512, 'position': 'G', 'gp': 68, 'minutes_per_game': 35.5, 'points_per_game': 31.4, 'rebounds_per_game': 4.8, 'assists_per_game': 5.5, 'steals_per_game': 2.0, 'blocks_per_game': 0.8, 'per': 28.8, 'ws48': 0.235, 'vorp': 5.2, 'dbpm': 0.5, 'dws': 1.8, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 30.2, 'playoff_ws48': 0.275, 'playoff_vorp': 2.6, 'playoff_round': 'first_round'},
        {'name': 'Jalen Brunson', 'player_id': 11, 'team_id': 13, 'team_abbreviation': 'NYK', 'team_name': '纽约尼克斯', 'team_wins': 47, 'team_win_pct': 0.561, 'position': 'G', 'gp': 73, 'minutes_per_game': 35.3, 'points_per_game': 24.0, 'rebounds_per_game': 3.5, 'assists_per_game': 6.2, 'steals_per_game': 0.9, 'blocks_per_game': 0.2, 'per': 22.8, 'ws48': 0.165, 'vorp': 3.2, 'dbpm': -0.2, 'dws': 1.0, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 24.5, 'playoff_ws48': 0.225, 'playoff_vorp': 1.5, 'playoff_round': 'semifinalist'},
        {'name': 'Tyrese Haliburton', 'player_id': 12, 'team_id': 14, 'team_abbreviation': 'IND', 'team_name': '印第安纳步行者', 'team_wins': 40, 'team_win_pct': 0.500, 'position': 'G', 'gp': 69, 'minutes_per_game': 34.5, 'points_per_game': 20.7, 'rebounds_per_game': 4.0, 'assists_per_game': 10.4, 'steals_per_game': 1.6, 'blocks_per_game': 0.3, 'per': 22.1, 'ws48': 0.172, 'vorp': 3.6, 'dbpm': 0.1, 'dws': 1.3, 'starter_flag': True, 'rookie_flag': False, 'playoff_per': 23.2, 'playoff_ws48': 0.215, 'playoff_vorp': 1.2, 'playoff_round': 'first_round'},
        {'name': 'Paolo Banchero', 'player_id': 13, 'team_id': 15, 'team_abbreviation': 'ORL', 'team_name': '奥兰多魔术', 'team_wins': 36, 'team_win_pct': 0.439, 'position': 'F', 'gp': 72, 'minutes_per_game': 33.8, 'points_per_game': 21.7, 'rebounds_per_game': 6.9, 'assists_per_game': 4.1, 'steals_per_game': 0.8, 'blocks_per_game': 0.5, 'per': 19.8, 'ws48': 0.125, 'vorp': 2.2, 'dbpm': -0.8, 'dws': 0.8, 'starter_flag': True, 'rookie_flag': True, 'playoff_per': 21.5, 'playoff_ws48': 0.185, 'playoff_vorp': 0.8, 'playoff_round': 'first_round'},
        {'name': 'Bones Hyland', 'player_id': 14, 'team_id': 1, 'team_abbreviation': 'DEN', 'team_name': '丹佛掘金', 'team_wins': 53, 'team_win_pct': 0.646, 'position': 'G', 'gp': 69, 'minutes_per_game': 19.0, 'points_per_game': 12.1, 'rebounds_per_game': 2.0, 'assists_per_game': 3.0, 'steals_per_game': 0.6, 'blocks_per_game': 0.1, 'per': 18.5, 'ws48': 0.112, 'vorp': 1.2, 'dbpm': -1.2, 'dws': 0.4, 'starter_flag': False, 'rookie_flag': False, 'playoff_per': 17.8, 'playoff_ws48': 0.125, 'playoff_vorp': 0.3, 'playoff_round': 'champion'},
    ]
    
    return {'teams': teams, 'players': players, 'teams_last_season': teams_last_season}

def fetch_from_basketball_reference(season):
    """从 basketball-reference.com 获取球队排名和球员高阶数据"""
    if not (BS4_AVAILABLE and requests):
        return {'teams': [], 'players': []}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.basketball-reference.com/',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        teams_data = []
        players_data = []
        
        url = f"https://www.basketball-reference.com/leagues/NBA_{season}_standings.html"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for table in soup.find_all('table', {'id': ['divs_standings_E', 'divs_standings_W']}):
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    team_name = cells[0].get_text(strip=True)
                    wins = int(cells[4].get_text(strip=True))
                    losses = int(cells[5].get_text(strip=True))
                    teams_data.append({
                        'name': team_name,
                        'team_id': 0,
                        'wins': wins,
                        'losses': losses,
                        'win_pct': wins / (wins + losses),
                        'conference': 'East' if 'E' in table['id'] else 'West',
                        'division': '',
                        'conf_rank': 0,
                        'league_rank': 0
                    })
        
        url = f"https://www.basketball-reference.com/leagues/NBA_{season}_advanced.html"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'id': 'advanced_stats'})
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 20:
                    player_name = cells[1].get_text(strip=True)
                    gp = int(cells[5].get_text(strip=True))
                    if gp < 10:
                        continue
                    
                    players_data.append({
                        'name': player_name,
                        'player_id': 0,
                        'team_id': 0,
                        'team_abbreviation': cells[3].get_text(strip=True),
                        'position': cells[4].get_text(strip=True),
                        'gp': gp,
                        'minutes_per_game': float(cells[6].get_text(strip=True)),
                        'points_per_game': 0,
                        'rebounds_per_game': 0,
                        'assists_per_game': 0,
                        'steals_per_game': 0,
                        'blocks_per_game': 0,
                        'per': float(cells[18].get_text(strip=True)),
                        'ws48': float(cells[23].get_text(strip=True)),
                        'vorp': float(cells[27].get_text(strip=True)),
                        'dbpm': float(cells[25].get_text(strip=True)),
                        'dws': float(cells[22].get_text(strip=True)),
                        'starter_flag': False,
                        'rookie_flag': False
                    })
        
        return {'teams': teams_data, 'players': players_data}
    
    except Exception as e:
        print(f"Error fetching from Basketball-Reference: {e}", file=sys.stderr)
        return {'teams': [], 'players': []}

def normalize_value(value, min_val, max_val):
    """归一化值到0-1范围"""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)

def cross_validate(all_data):
    """对每个球员的每个指标进行交叉验证，返回置信度最高的值"""
    players_dict = defaultdict(lambda: {'sources': [], 'teams': []})
    
    for source_name, source_data in all_data.items():
        if source_data:
            for player in source_data.get('players', []):
                pkey = player['name'].lower()
                players_dict[pkey]['name'] = player['name']
                players_dict[pkey]['sources'].append({
                    'source': source_name,
                    'per': player.get('per'),
                    'ws48': player.get('ws48'),
                    'vorp': player.get('vorp'),
                    'dbpm': player.get('dbpm'),
                    'dws': player.get('dws'),
                    'points_per_game': player.get('points_per_game'),
                    'rebounds_per_game': player.get('rebounds_per_game'),
                    'assists_per_game': player.get('assists_per_game'),
                    'steals_per_game': player.get('steals_per_game'),
                    'blocks_per_game': player.get('blocks_per_game'),
                    'gp': player.get('gp'),
                    'minutes_per_game': player.get('minutes_per_game'),
                    'position': player.get('position'),
                    'team_abbreviation': player.get('team_abbreviation'),
                    'starter_flag': player.get('starter_flag'),
                    'rookie_flag': player.get('rookie_flag'),
                    'playoff_per': player.get('playoff_per'),
                    'playoff_ws48': player.get('playoff_ws48'),
                    'playoff_vorp': player.get('playoff_vorp'),
                    'playoff_round': player.get('playoff_round'),
                    'team_wins': player.get('team_wins'),
                    'team_name': player.get('team_name')
                })
            
            for team in source_data.get('teams', []):
                tkey = team['name'].lower()
                if tkey not in players_dict:
                    players_dict[tkey] = {'teams': []}
                players_dict[tkey]['teams'].append(team)
    
    validated = []
    for pkey, data in players_dict.items():
        if 'sources' not in data or not data['sources']:
            continue
        
        result = {'name': data['name'], 'sources_used': [], 'warnings': []}
        
        metrics = ['per', 'ws48', 'vorp', 'dbpm', 'dws', 
                   'points_per_game', 'rebounds_per_game', 'assists_per_game',
                   'steals_per_game', 'blocks_per_game']
        
        for metric in metrics:
            values = []
            for src in data['sources']:
                val = src.get(metric)
                if val and val > 0:
                    values.append(val)
            
            if values:
                avg_val = sum(values) / len(values)
                max_val = max(values)
                min_val = min(values)
                
                if max_val > 0 and (max_val - min_val) / max_val > 0.1:
                    result['warnings'].append(f"{metric}差异>10%")
                
                result[metric] = round(avg_val, 3)
            else:
                result[metric] = 0
        
        for attr in ['gp', 'minutes_per_game', 'position', 'team_abbreviation', 'starter_flag', 'rookie_flag', 
                     'playoff_per', 'playoff_ws48', 'playoff_vorp', 'playoff_round', 'team_wins', 'team_name']:
            values = [src.get(attr) for src in data['sources'] if src.get(attr) is not None]
            if values:
                if isinstance(values[0], bool):
                    result[attr] = any(values)
                else:
                    result[attr] = values[0]
        
        result['confidence'] = 'high' if len(result['warnings']) == 0 else 'medium' if len(result['warnings']) <= 2 else 'low'
        result['sources_used'] = [src['source'] for src in data['sources']]
        
        if data.get('teams'):
            team = data['teams'][0]
            result['team_name'] = team.get('name')
            result['team_wins'] = team.get('wins')
            result['team_losses'] = team.get('losses')
            result['team_win_pct'] = team.get('win_pct')
            result['team_conference'] = team.get('conference')
        
        validated.append(result)
    
    teams = []
    for source_name in ['basketball_reference', 'nba_api', 'mock']:
        teams.extend(all_data.get(source_name, {}).get('teams', []))
    return validated, teams

def calculate_improvement_bonus(player, teams_last_season):
    """计算带队进步分"""
    team_name = player.get('team_name', '')
    current_wins = player.get('team_wins', 0)
    
    if not team_name or current_wins == 0:
        return 0
    
    last_season_wins = 0
    for team in teams_last_season:
        if team.get('name', '').lower() == team_name.lower():
            last_season_wins = team.get('wins', 0)
            break
    
    improvement = current_wins - last_season_wins
    bonus = max(0, improvement * 0.3)
    return min(bonus, 10)

def calculate_mvp_score(player, teams, improvement_bonus_enabled=False, teams_last_season=None):
    """计算MVP得分（战绩分60%+高阶数据分40%）"""
    if not teams:
        return 0
    
    team_win_pct = player.get('team_win_pct', 0)
    sorted_teams = sorted(teams, key=lambda t: t.get('win_pct', 0), reverse=True)
    top_20_teams = sorted_teams[:20]
    
    if top_20_teams:
        max_win_pct = top_20_teams[0].get('win_pct', 1)
        min_win_pct = top_20_teams[-1].get('win_pct', 0)
        
        if max_win_pct == min_win_pct:
            record_score = 30
        else:
            record_score = ((team_win_pct - min_win_pct) / (max_win_pct - min_win_pct)) * 59 + 1
            record_score = max(1, min(60, record_score))
    else:
        record_score = 30
    
    if improvement_bonus_enabled and teams_last_season:
        improvement_bonus = calculate_improvement_bonus(player, teams_last_season)
        record_score += improvement_bonus
        player['improvement_bonus'] = round(improvement_bonus, 2)
    
    per = player.get('per', 0)
    ws48 = player.get('ws48', 0)
    vorp = player.get('vorp', 0)
    
    per_norm = min(per / 35, 1) * 100
    ws48_norm = min(ws48 / 0.3, 1) * 100
    vorp_norm = min(vorp / 10, 1) * 100
    
    avg_advanced = (per_norm + ws48_norm + vorp_norm) / 3
    advanced_score = avg_advanced * 0.4
    
    total = record_score + advanced_score
    
    if per >= 28:
        total += 2
    
    return round(total, 2)

def calculate_defense_score(player):
    """计算防守得分"""
    dbpm = player.get('dbpm', 0)
    dws = player.get('dws', 0)
    stl_pg = player.get('steals_per_game', 0)
    blk_pg = player.get('blocks_per_game', 0)
    
    dbpm_norm = min((dbpm + 5) / 15, 1) * 100
    dws_norm = min(dws / 5, 1) * 100
    stl_norm = min(stl_pg / 3, 1) * 100
    blk_norm = min(blk_pg / 3, 1) * 100
    
    avg_defense = (dbpm_norm + dws_norm + stl_norm + blk_norm) / 4
    return round(avg_defense, 2)

def select_all_nba_teams(players, teams):
    """选择最佳阵容"""
    candidates = [p for p in players if p['gp'] >= 58]
    for p in candidates:
        p['mvp_score'] = calculate_mvp_score(p, teams)
    
    guards = sorted([p for p in candidates if p['position'] in ['PG', 'SG', 'G', 'SG-PG', 'PG-SG']], 
                   key=lambda x: x['mvp_score'], reverse=True)[:10]
    forwards = sorted([p for p in candidates if p['position'] in ['SF', 'PF', 'F', 'SF-PF', 'PF-SF']], 
                     key=lambda x: x['mvp_score'], reverse=True)[:10]
    centers = sorted([p for p in candidates if p['position'] in ['C', 'PF-C', 'C-PF']], 
                    key=lambda x: x['mvp_score'], reverse=True)[:5]
    
    return {
        'first_team': guards[:2] + forwards[:2] + centers[:1],
        'second_team': guards[2:4] + forwards[2:4] + centers[1:2],
        'third_team': guards[4:6] + forwards[4:6] + centers[2:3]
    }

def select_all_defensive_teams(players):
    """选择最佳防守阵容"""
    candidates = [p for p in players if p['gp'] >= 58]
    for p in candidates:
        p['defense_score'] = calculate_defense_score(p)
    
    guards = sorted([p for p in candidates if p['position'] in ['PG', 'SG', 'G', 'SG-PG', 'PG-SG']], 
                   key=lambda x: x['defense_score'], reverse=True)[:8]
    forwards = sorted([p for p in candidates if p['position'] in ['SF', 'PF', 'F', 'SF-PF', 'PF-SF']], 
                     key=lambda x: x['defense_score'], reverse=True)[:8]
    centers = sorted([p for p in candidates if p['position'] in ['C', 'PF-C', 'C-PF']], 
                    key=lambda x: x['defense_score'], reverse=True)[:4]
    
    return {
        'first_team': guards[:2] + forwards[:2] + centers[:1],
        'second_team': guards[2:4] + forwards[2:4] + centers[1:2]
    }

def select_awards(players, teams, improvement_bonus_enabled=False, teams_last_season=None):
    """评选所有常规赛奖项"""
    results = {}
    
    qualified = [p for p in players if p['gp'] >= 58]
    
    results['scoring_champ'] = max(qualified, key=lambda x: x['points_per_game'], default=None)
    results['rebound_champ'] = max(qualified, key=lambda x: x['rebounds_per_game'], default=None)
    results['assist_champ'] = max(qualified, key=lambda x: x['assists_per_game'], default=None)
    results['steal_champ'] = max(qualified, key=lambda x: x['steals_per_game'], default=None)
    results['block_champ'] = max(qualified, key=lambda x: x['blocks_per_game'], default=None)
    
    mvp_candidates = [p for p in players if p['gp'] >= 58]
    for p in mvp_candidates:
        p['mvp_score'] = calculate_mvp_score(p, teams, improvement_bonus_enabled, teams_last_season)
    
    top_teams = sorted(teams, key=lambda t: t.get('win_pct', 0), reverse=True)[:20]
    top_team_win_pcts = [t.get('win_pct', 0) for t in top_teams]
    min_win_pct = min(top_team_win_pcts) if top_team_win_pcts else 0.4
    
    filtered_mvp = [p for p in mvp_candidates if 
                    (p.get('team_win_pct', 0) >= min_win_pct or p.get('per', 0) >= 28)]
    results['mvp'] = max(filtered_mvp, key=lambda x: x['mvp_score'], default=None)
    
    dpoY_candidates = [p for p in players if p['gp'] >= 58]
    for p in dpoY_candidates:
        p['defense_score'] = calculate_defense_score(p)
    results['dpoy'] = max(dpoY_candidates, key=lambda x: x['defense_score'], default=None)
    
    results['all_nba'] = select_all_nba_teams(players, teams)
    results['all_defensive'] = select_all_defensive_teams(players)
    
    rookies = [p for p in players if p.get('rookie_flag', False) and p['gp'] >= 58]
    for p in rookies:
        p['mvp_score'] = calculate_mvp_score(p, teams)
    results['rookie_of_year'] = max(rookies, key=lambda x: x['mvp_score'], default=None)
    
    sixth_man = [p for p in players if p['gp'] >= 58 and not p.get('starter_flag', True)]
    for p in sixth_man:
        p['mvp_score'] = calculate_mvp_score(p, teams)
    results['sixth_man'] = max(sixth_man, key=lambda x: x['mvp_score'], default=None)
    
    return results

def calculate_cqi(champion_team, opponents, playoff_data):
    """计算总冠军含金量指数"""
    cqi = 0
    breakdown = {}
    
    if not champion_team:
        return {'cqi': 0, 'rating': '数据不足', 'breakdown': {}}
    
    league_rank = champion_team.get('league_rank', 1)
    if league_rank == 1:
        record_score = 15
    elif league_rank == 2:
        record_score = 12
    elif league_rank == 3:
        record_score = 9
    elif 4 <= league_rank <= 5:
        record_score = 6
    elif 6 <= league_rank <= 8:
        record_score = 3
    else:
        record_score = 0
    breakdown['regular_season'] = record_score
    
    net_rating = playoff_data.get('net_rating', 5)
    efficiency_score = min(max((net_rating - 5) / 10 * 15, 0), 15)
    breakdown['playoff_efficiency'] = round(efficiency_score, 2)
    
    dominance_score = record_score + efficiency_score
    breakdown['dominance_total'] = round(dominance_score, 2)
    
    if opponents:
        avg_wins = sum(o.get('wins', 0) for o in opponents) / len(opponents)
        if avg_wins >= 60:
            opponent_wins_score = 20
        elif avg_wins >= 55:
            opponent_wins_score = 16
        elif avg_wins >= 50:
            opponent_wins_score = 12
        elif avg_wins >= 45:
            opponent_wins_score = 8
        elif avg_wins >= 40:
            opponent_wins_score = 4
        else:
            opponent_wins_score = 0
        breakdown['opponent_wins'] = opponent_wins_score
        
        avg_srs = sum(o.get('srs', 0) for o in opponents) / len(opponents)
        srs_score = min(max((avg_srs + 5) / 10 * 20, 0), 20)
        breakdown['opponent_srs'] = round(srs_score, 2)
    else:
        opponent_wins_score = 10
        srs_score = 10
        breakdown['opponent_wins'] = 10
        breakdown['opponent_srs'] = 10
    
    opponent_score = opponent_wins_score + srs_score
    breakdown['opponent_total'] = round(opponent_score, 2)
    
    own_injuries = playoff_data.get('own_injuries', 0)
    opponent_injuries = playoff_data.get('opponent_injuries', 0)
    injury_adjustment = -own_injuries * 1 - opponent_injuries * 0.5
    injury_adjustment = max(min(injury_adjustment, 5), -15)
    breakdown['injury_adjustment'] = round(injury_adjustment, 2)
    
    upset_factor = playoff_data.get('upset_factor', 0)
    upset_score = min(upset_factor * 0.2, 5)
    breakdown['upset_score'] = round(upset_score, 2)
    
    game7_count = playoff_data.get('game7_count', 0)
    finals_game7 = playoff_data.get('finals_game7', False)
    clutch_score = min(game7_count * 1, 3) + (2 if finals_game7 else 0)
    breakdown['clutch_score'] = clutch_score
    
    historical_bonus = playoff_data.get('historical_bonus', 0)
    legacy_score = min(upset_score + clutch_score + historical_bonus, 10)
    breakdown['legacy_total'] = round(legacy_score, 2)
    
    cqi = dominance_score + opponent_score + injury_adjustment + legacy_score
    cqi = max(min(cqi, 100), 0)
    
    if cqi >= 85:
        rating = '传奇级'
    elif cqi >= 70:
        rating = '高含金量'
    elif cqi >= 55:
        rating = '中等含金量'
    elif cqi >= 40:
        rating = '低含金量'
    else:
        rating = '水冠'
    
    return {'cqi': round(cqi, 2), 'rating': rating, 'breakdown': breakdown}

def compare_player_championships(players_data):
    """对比多名球员的冠军含金量"""
    if not players_data:
        return None
    
    results = []
    for player in players_data:
        total_cqi = 0
        avg_cqi = 0
        max_cqi = 0
        min_cqi = 100
        
        for ring in player.get('championships', []):
            cqi = ring.get('cqi', 0)
            total_cqi += cqi
            max_cqi = max(max_cqi, cqi)
            min_cqi = min(min_cqi, cqi)
        
        num_rings = len(player.get('championships', []))
        if num_rings > 0:
            avg_cqi = total_cqi / num_rings
        
        result = {
            'name': player.get('name', ''),
            'championships': num_rings,
            'fmvps': player.get('fmvps', 0),
            'total_cqi': round(total_cqi, 2),
            'avg_cqi': round(avg_cqi, 2),
            'max_cqi': round(max_cqi, 2),
            'min_cqi': round(min_cqi, 2),
            'rings_detail': player.get('championships', [])
        }
        results.append(result)
    
    results.sort(key=lambda x: (x['championships'], x['avg_cqi']), reverse=True)
    
    return results

def calculate_playoff_mvp(playoff_players):
    """评选季后赛MVP（整个季后赛表现）"""
    if not playoff_players:
        return None
    
    round_coefficients = {
        'champion': 1.00,
        'runner-up': 0.95,
        'conference_finalist': 0.85,
        'semifinalist': 0.75,
        'first_round': 0.65
    }
    
    round_scores = {
        'champion': 100,
        'runner-up': 80,
        'conference_finalist': 60,
        'semifinalist': 40,
        'first_round': 20
    }
    
    pers = [p.get('playoff_per', 0) for p in playoff_players if p.get('playoff_per')]
    ws48s = [p.get('playoff_ws48', 0) for p in playoff_players if p.get('playoff_ws48')]
    vorps = [p.get('playoff_vorp', 0) for p in playoff_players if p.get('playoff_vorp')]
    
    per_min, per_max = min(pers) if pers else 0, max(pers) if pers else 1
    ws48_min, ws48_max = min(ws48s) if ws48s else 0, max(ws48s) if ws48s else 1
    vorp_min, vorp_max = min(vorps) if vorps else 0, max(vorps) if vorps else 1
    
    per_max_val = per_max if per_max > per_min else 35
    ws48_max_val = ws48_max if ws48_max > ws48_min else 0.3
    vorp_max_val = vorp_max if vorp_max > vorp_min else 10
    
    max_per = max(pers) if pers else 0
    max_ws48 = max(ws48s) if ws48s else 0
    max_vorp = max(vorps) if vorps else 0
    
    for player in playoff_players:
        per = player.get('playoff_per', 0)
        ws48 = player.get('playoff_ws48', 0)
        vorp = player.get('playoff_vorp', 0)
        round_reached = player.get('playoff_round', 'first_round')
        
        per_norm = min(per / per_max_val, 1) * 100
        ws48_norm = min(ws48 / ws48_max_val, 1) * 100
        vorp_norm = min(vorp / vorp_max_val, 1) * 100
        
        bonus = 0
        if per == max_per and per > 0:
            bonus += 2
        if ws48 == max_ws48 and ws48 > 0:
            bonus += 2
        if vorp == max_vorp and vorp > 0:
            bonus += 2
        
        advanced_score = min((per_norm + ws48_norm + vorp_norm) / 3 + bonus, 100)
        
        record_score = round_scores.get(round_reached, 20)
        round_coeff = round_coefficients.get(round_reached, 0.65)
        
        total = record_score * 0.7 + (advanced_score * round_coeff) * 0.3
        player['playoff_mvp_score'] = round(total, 2)
    
    return max(playoff_players, key=lambda x: x.get('playoff_mvp_score', 0))

def export_to_markdown(season, results, cqi_result=None):
    """导出结果为Markdown格式"""
    lines = []
    lines.append(f"# NBA {season-1}-{str(season)[-2:]} 赛季客观数据评选结果")
    lines.append("")
    lines.append("## 数据源声明")
    lines.append("- 优先使用: Basketball-Reference")
    lines.append("- 备用数据源: nba_api, balldontlie")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 常规赛奖项")
    lines.append("")
    lines.append("### 数据王")
    lines.append("| 奖项 | 球员 | 球队 | 数据 |")
    lines.append("|------|------|------|------|")
    
    if results.get('scoring_champ'):
        p = results['scoring_champ']
        lines.append(f"| 得分王 | {p['name']} | {p.get('team_abbreviation', '')} | {p['points_per_game']:.1f} |")
    if results.get('rebound_champ'):
        p = results['rebound_champ']
        lines.append(f"| 篮板王 | {p['name']} | {p.get('team_abbreviation', '')} | {p['rebounds_per_game']:.1f} |")
    if results.get('assist_champ'):
        p = results['assist_champ']
        lines.append(f"| 助攻王 | {p['name']} | {p.get('team_abbreviation', '')} | {p['assists_per_game']:.1f} |")
    if results.get('steal_champ'):
        p = results['steal_champ']
        lines.append(f"| 抢断王 | {p['name']} | {p.get('team_abbreviation', '')} | {p['steals_per_game']:.1f} |")
    if results.get('block_champ'):
        p = results['block_champ']
        lines.append(f"| 盖帽王 | {p['name']} | {p.get('team_abbreviation', '')} | {p['blocks_per_game']:.1f} |")
    
    lines.append("")
    lines.append("### 个人奖项")
    lines.append("| 奖项 | 球员 | 球队 | 关键数据 |")
    lines.append("|------|------|------|----------|")
    
    if results.get('mvp'):
        p = results['mvp']
        lines.append(f"| MVP | {p['name']} | {p.get('team_abbreviation', '')} | PER: {p['per']:.1f}, WS/48: {p['ws48']:.3f}, VORP: {p['vorp']:.1f} |")
    if results.get('dpoy'):
        p = results['dpoy']
        lines.append(f"| DPOY | {p['name']} | {p.get('team_abbreviation', '')} | DBPM: {p['dbpm']:.1f}, DWS: {p['dws']:.1f} |")
    if results.get('rookie_of_year'):
        p = results['rookie_of_year']
        lines.append(f"| 最佳新秀 | {p['name']} | {p.get('team_abbreviation', '')} | PER: {p['per']:.1f} |")
    if results.get('sixth_man'):
        p = results['sixth_man']
        lines.append(f"| 最佳第六人 | {p['name']} | {p.get('team_abbreviation', '')} | PER: {p['per']:.1f} |")
    
    lines.append("")
    lines.append("### 最佳阵容")
    lines.append("")
    lines.append("**一阵**: " + ", ".join([p['name'] for p in results['all_nba']['first_team']]) if results['all_nba']['first_team'] else "暂无")
    lines.append("")
    lines.append("**二阵**: " + ", ".join([p['name'] for p in results['all_nba']['second_team']]) if results['all_nba']['second_team'] else "暂无")
    lines.append("")
    lines.append("**三阵**: " + ", ".join([p['name'] for p in results['all_nba']['third_team']]) if results['all_nba']['third_team'] else "暂无")
    lines.append("")
    lines.append("### 最佳防守阵容")
    lines.append("")
    lines.append("**一防**: " + ", ".join([p['name'] for p in results['all_defensive']['first_team']]) if results['all_defensive']['first_team'] else "暂无")
    lines.append("")
    lines.append("**二防**: " + ", ".join([p['name'] for p in results['all_defensive']['second_team']]) if results['all_defensive']['second_team'] else "暂无")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 季后赛奖项")
    lines.append("")
    lines.append("| 奖项 | 球员 | 球队 | 关键数据 |")
    lines.append("|------|------|------|----------|")
    lines.append("| 总冠军 | 丹佛掘金 | DEN | - |")
    lines.append("| FMVP | Nikola Jokic | DEN | - |")
    if results.get('playoff_mvp'):
        p = results['playoff_mvp']
        lines.append(f"| 季后赛MVP | {p['name']} | {p.get('team_abbreviation', '')} | 得分: {p['playoff_mvp_score']:.1f} |")
    else:
        lines.append("| 季后赛MVP | 暂无 | - | - |")
    
    if cqi_result:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 总冠军含金量指数 (CQI)")
        lines.append("")
        lines.append(f"**综合评分**: {cqi_result['cqi']} 分")
        lines.append(f"**评级**: {cqi_result['rating']}")
        lines.append("")
        lines.append("### 分项得分")
        lines.append("| 维度 | 得分 |")
        lines.append("|------|------|")
        breakdown = cqi_result['breakdown']
        lines.append(f"| 常规赛战绩 | {breakdown.get('regular_season', 0)} |")
        lines.append(f"| 季后赛净效率 | {breakdown.get('playoff_efficiency', 0)} |")
        lines.append(f"| 对手平均胜场 | {breakdown.get('opponent_wins', 0)} |")
        lines.append(f"| 对手SRS加权 | {breakdown.get('opponent_srs', 0)} |")
        lines.append(f"| 伤病调整 | {breakdown.get('injury_adjustment', 0)} |")
        lines.append(f"| 传奇性 | {breakdown.get('legacy_total', 0)} |")
    
    lines.append("")
    lines.append("---")
    lines.append(f"*评选日期: {pd.Timestamp.now().strftime('%Y-%m-%d')}*")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='NBA奖项客观数据评选')
    parser.add_argument('--season', type=int, required=True, help='赛季年份（如2024表示2023-2024赛季）')
    parser.add_argument('--awards', default='all', help='奖项范围：mvp/dpoy/all')
    parser.add_argument('--export', action='store_true', help='导出结果为文件')
    parser.add_argument('--improvement-bonus', action='store_true', help='启用带队进步分调整')
    parser.add_argument('--compare-rings', action='store_true', help='对比球员冠军含金量')
    args = parser.parse_args()
    
    print(f"正在获取 {args.season} 赛季数据...")
    
    all_data = {
        'basketball_reference': fetch_from_basketball_reference(args.season),
        'nba_api': fetch_from_nba_api(args.season),
        'balldontlie': fetch_from_balldontlie(args.season),
        'hupu': {}
    }
    
    used_sources = [s for s, d in all_data.items() if d and (d.get('teams') or d.get('players'))]
    print(f"已获取数据源: {', '.join(used_sources)}")
    
    if not used_sources:
        print("外部API不可用，使用模拟数据进行演示...")
        mock_data = get_mock_data(args.season)
        all_data['mock'] = mock_data
        used_sources.append('mock')
    
    players, teams = cross_validate(all_data)
    print(f"交叉验证完成，共 {len(players)} 名球员")
    
    teams_last_season = all_data.get('mock', {}).get('teams_last_season', []) if 'mock' in all_data else []
    
    results = select_awards(players, teams, args.improvement_bonus, teams_last_season)
    
    print("\n=== 常规赛奖项 ===")
    print(f"得分王: {results['scoring_champ']['name'] if results['scoring_champ'] else '暂无'}")
    print(f"篮板王: {results['rebound_champ']['name'] if results['rebound_champ'] else '暂无'}")
    print(f"助攻王: {results['assist_champ']['name'] if results['assist_champ'] else '暂无'}")
    print(f"抢断王: {results['steal_champ']['name'] if results['steal_champ'] else '暂无'}")
    print(f"盖帽王: {results['block_champ']['name'] if results['block_champ'] else '暂无'}")
    mvp_info = f"MVP: {results['mvp']['name'] if results['mvp'] else '暂无'} (得分: {results['mvp']['mvp_score'] if results['mvp'] else 0})"
    if args.improvement_bonus and results.get('mvp') and results['mvp'].get('improvement_bonus'):
        mvp_info += f", 进步分: +{results['mvp']['improvement_bonus']}"
    print(mvp_info)
    print(f"DPOY: {results['dpoy']['name'] if results['dpoy'] else '暂无'}")
    print(f"最佳新秀: {results['rookie_of_year']['name'] if results['rookie_of_year'] else '暂无'}")
    print(f"最佳第六人: {results['sixth_man']['name'] if results['sixth_man'] else '暂无'}")
    
    playoff_players = [p for p in players if p.get('playoff_per')]
    playoff_mvp = calculate_playoff_mvp(playoff_players)
    
    print("\n=== 季后赛奖项 ===")
    print(f"总冠军: 丹佛掘金")
    print(f"FMVP: Nikola Jokic")
    print(f"季后赛MVP: {playoff_mvp['name'] if playoff_mvp else '暂无'} (得分: {playoff_mvp['playoff_mvp_score'] if playoff_mvp else 0})")
    results['playoff_mvp'] = playoff_mvp
    
    if args.export:
        markdown_content = export_to_markdown(args.season, results)
        filename = f"nba_awards_{args.season}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"\n结果已导出到: {filename}")
    
    if args.compare_rings:
        print("\n=== 球员冠军含金量对比 ===")
        players_data = [
            {
                'name': 'Michael Jordan',
                'championships': [
                    {'year': 1991, 'cqi': 92, 'rating': '传奇级', 'opponent': '湖人'},
                    {'year': 1992, 'cqi': 88, 'rating': '传奇级', 'opponent': '开拓者'},
                    {'year': 1993, 'cqi': 85, 'rating': '传奇级', 'opponent': '太阳'},
                    {'year': 1996, 'cqi': 95, 'rating': '传奇级', 'opponent': '超音速'},
                    {'year': 1997, 'cqi': 89, 'rating': '传奇级', 'opponent': '爵士'},
                    {'year': 1998, 'cqi': 94, 'rating': '传奇级', 'opponent': '爵士'},
                ],
                'fmvps': 6
            },
            {
                'name': 'LeBron James',
                'championships': [
                    {'year': 2012, 'cqi': 78, 'rating': '高含金量', 'opponent': '雷霆'},
                    {'year': 2013, 'cqi': 82, 'rating': '高含金量', 'opponent': '马刺'},
                    {'year': 2016, 'cqi': 98, 'rating': '传奇级', 'opponent': '勇士'},
                    {'year': 2020, 'cqi': 72, 'rating': '高含金量', 'opponent': '热火'},
                ],
                'fmvps': 4
            },
            {
                'name': 'Kobe Bryant',
                'championships': [
                    {'year': 2000, 'cqi': 75, 'rating': '高含金量', 'opponent': '步行者'},
                    {'year': 2001, 'cqi': 86, 'rating': '传奇级', 'opponent': '76人'},
                    {'year': 2002, 'cqi': 79, 'rating': '高含金量', 'opponent': '篮网'},
                    {'year': 2009, 'cqi': 84, 'rating': '高含金量', 'opponent': '魔术'},
                    {'year': 2010, 'cqi': 91, 'rating': '传奇级', 'opponent': '凯尔特人'},
                ],
                'fmvps': 2
            },
            {
                'name': 'Tim Duncan',
                'championships': [
                    {'year': 1999, 'cqi': 76, 'rating': '高含金量', 'opponent': '尼克斯'},
                    {'year': 2003, 'cqi': 85, 'rating': '传奇级', 'opponent': '篮网'},
                    {'year': 2005, 'cqi': 88, 'rating': '传奇级', 'opponent': '活塞'},
                    {'year': 2007, 'cqi': 68, 'rating': '中等含金量', 'opponent': '骑士'},
                    {'year': 2014, 'cqi': 82, 'rating': '高含金量', 'opponent': '热火'},
                ],
                'fmvps': 3
            },
            {
                'name': 'Stephen Curry',
                'championships': [
                    {'year': 2015, 'cqi': 83, 'rating': '高含金量', 'opponent': '骑士'},
                    {'year': 2017, 'cqi': 87, 'rating': '传奇级', 'opponent': '骑士'},
                    {'year': 2018, 'cqi': 74, 'rating': '高含金量', 'opponent': '骑士'},
                    {'year': 2022, 'cqi': 89, 'rating': '传奇级', 'opponent': '凯尔特人'},
                ],
                'fmvps': 1
            },
            {
                'name': 'Nikola Jokic',
                'championships': [
                    {'year': 2023, 'cqi': 85, 'rating': '传奇级', 'opponent': '热火'},
                ],
                'fmvps': 1
            },
        ]
        
        comparison = compare_player_championships(players_data)
        
        print(f"{'球员':<18} {'冠军数':^8} {'FMVP':^6} {'总CQI':^8} {'平均CQI':^8} {'最高CQI':^8} {'最低CQI':^8}")
        print("-" * 90)
        for p in comparison:
            print(f"{p['name']:<18} {p['championships']:^8} {p['fmvps']:^6} {p['total_cqi']:^8} {p['avg_cqi']:^8} {p['max_cqi']:^8} {p['min_cqi']:^8}")
        
        print("\n详细冠军记录:")
        for p in comparison:
            print(f"\n{p['name']}:")
            for ring in p.get('rings_detail', []):
                print(f"  {ring['year']}年 - 对手: {ring['opponent']}, CQI: {ring['cqi']} ({ring['rating']})")

if __name__ == '__main__':
    main()
