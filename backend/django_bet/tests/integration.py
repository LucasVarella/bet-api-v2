import requests
import time
import datetime
import json

from django.utils.text import slugify
from decouple import config

api_token = config('API_TOKEN')

def fetch_matches_and_leagues_football():
    
    current_year = datetime.datetime.now().year

    url = "https://v3.football.api-sports.io/fixtures"
    token = api_token

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": token 
    }
    
    current_date = datetime.datetime.now().date()
    dates = [current_date + datetime.timedelta(days=i) for i in range(3)]
    
    matches_by_date = {}
    for date in dates:
        formated_date = date.strftime("%Y-%m-%d")

        print(formated_date)
        
        params = {
            "season": current_year,
            "date": formated_date,
            "timezone": "America/Sao_Paulo"
        }
        
        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        list_matches = []
        for match in result['response']:
            fixture = match['fixture']
            league = match['league']
            teams = match['teams']
            
            dict_league = {
                "id": league['id'],
                "name": league['name'],
                "logo": league['logo'],
                "country": league['country'],
                "flag": league['flag']
            }
            
            dict_home = {
                "id": teams['home']['id'],
                "name": teams['home']['name'],
                "logo": teams['home']['logo']
            }
            
            dict_away = {
                "id": teams['away']['id'],
                "name": teams['away']['name'],
                "logo": teams['away']['logo']
            }
        
            dict_match = {
                "id": fixture['id'],
                "date": fixture['date'],
                "venue": fixture['venue']['name'],
                "city": fixture['venue']['city'],
                "status": fixture['status']['short'],
                "league": dict_league,
                "home": dict_home,
                "away": dict_away
            }
            
            list_matches.append(dict_match)
        
        matches_by_date[formated_date] = list_matches
    
    write_to_file(matches_by_date, filename="matches.json")

def write_to_file(data, filename):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def fetch_odds_football(bookmaker_id, days_to_fetch):
    current_year = datetime.datetime.now().year
    current_date = datetime.datetime.now().date()
    dates = [current_date + datetime.timedelta(days=i) for i in range(days_to_fetch)]
    
    url = "https://v3.football.api-sports.io/odds"
    token = api_token

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": token 
    }

    params_base = {
        "season": current_year,
        "timezone": "America/Sao_Paulo",
        "bookmaker": bookmaker_id
    }

    odds_by_date = {}
    for date in dates:
        formated_date = date.strftime("%Y-%m-%d")
        print(formated_date)
        page = 1
        while True:
            params = params_base.copy()
            params["date"] = formated_date
            params["page"] = page
            
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if len(result['response']) == 0:
                break  # não há mais dados, podemos parar
            
            match_bets_list = []
            for match in result['response']:
                print(match['fixture']['id'])
                match_bets = {'fixture_id': match['fixture']['id'], 'update': match['update'], 'bets': None}
                
                bets = match['bookmakers'][0]['bets']
                list_bets = []
                for bet in bets:
                    bet_id = bet['id']
                    bet_name = bet['name']
                    bet_values = bet['values']
                    
                    list_values = []
                    for value in bet_values:
                        dict_market = {
                            'value': value['value'],
                            'odd': value['odd']
                        }
                        list_values.append(dict_market)
                    
                    dict_bet = {
                        'id': bet_id,
                        'name': bet_name,
                        'values': list_values
                    }
                    list_bets.append(dict_bet)
                
                match_bets['bets'] = list_bets
            
            match_bets_list.append(match_bets)
            page += 1  # ir para a próxima página
        
        len(match_bets_list)
        odds_by_date[formated_date] = match_bets_list

        write_to_file(odds_by_date, 'odds_by_date.json')

#fetch_matches_and_leagues_football()
fetch_odds_football(8, 3)
