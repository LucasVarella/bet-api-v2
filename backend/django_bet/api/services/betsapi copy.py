import requests
import time
import datetime
import uuid

from django.utils.text import slugify
from django.db import transaction

from ..models import League, Match, Team, Market, Bet

from decouple import config

api_token = config('API_TOKEN')

headers = {
    "Content-Type": "application/json",
    "x-rapidapi-key": api_token 
}

def fetch_matches_and_leagues_football(days_to_fetch):
    
    current_year = datetime.datetime.now().year

    url = "https://v3.football.api-sports.io/fixtures"
    
    current_date = datetime.datetime.now().date()
    dates = [current_date + datetime.timedelta(days=i) for i in range(days_to_fetch)]
    
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
            goals = match['goals']
            
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

            dict_score = {
                "home": goals['home'],
                "away": goals['away'],
            }

            dict_match = {
                "id": fixture['id'],
                "date": fixture['date'],
                "venue": fixture['venue']['name'],
                "city": fixture['venue']['city'],
                "status": fixture['status']['short'],
                "league": dict_league,
                "home": dict_home,
                "away": dict_away,
                "score": dict_score
            }
            
            list_matches.append(dict_match)
        
        matches_by_date[formated_date] = list_matches
    
    return matches_by_date

def save_matches_and_leagues_footbal(matches_by_date):

    matches_to_create = []
    matches_to_update = []
    for date, list_matches in matches_by_date.items(): 
        
        for match in list_matches:
            league_id = match["league"]["id"]
            home_id = match["home"]["id"]
            away_id = match["away"]["id"]
            match_id = match["id"]
            
            home_goals = None
            away_goals = None
            try:
                home_goals = int(match["score"]["home"])
                away_goals = int(match["score"]["away"])

            except:
                pass
            
            # Processar League
            league_obj = None
            try:
                try:
                    league = League.objects.get(id=league_id)
                    league_obj = league
                except:
                    slug = slugify(match["league"]["name"])
                    counter = 1
                    while True:
                        try:
                            League.objects.get(slug=slug)
                        except League.DoesNotExist:
                            break
                        slug += f"-{counter}"
                        counter += 1
                    league = League(
                        id=league_id,
                        name=match["league"]["name"],
                        slug=slug,
                        logo=match["league"]["logo"],
                        country=match["league"]["country"],
                        flag=match["league"]["flag"],
                        sport_id=1,
                    )
                    league.save()
                    league_obj = league
            except Exception as error:
                print(f"Falha ao processar League\n{error}")
    
            # Processar Teams
            home_team_obj = None
            away_team_obj = None
            try:
                # Home
                home_team, created = Team.objects.get_or_create(
                    id=home_id,
                    defaults={
                        'name': match["home"]["name"],
                        'logo': match["home"]["logo"],
                    }
                )
                # Se já existe, atualiza caso necessário
                if not created:
                    updated = False
                    for field, value in {
                        'name': match["home"]["name"],
                        'logo': match["home"]["logo"],
                    }.items():
                        if getattr(home_team, field)!= value:
                            setattr(home_team, field, value)
                            updated = True
                    if updated:
                        home_team.save()
                home_team_obj = home_team
                
                # Away
                away_team, created = Team.objects.get_or_create(
                    id=away_id,
                    defaults={
                        'name': match["away"]["name"],
                        'logo': match["away"]["logo"],
                    }
                )
                # Se já existe, atualiza caso necessário
                if not created:
                    updated = False
                    for field, value in {
                        'name': match["away"]["name"],
                        'logo': match["away"]["logo"],
                    }.items():
                        if getattr(away_team, field)!= value:
                            setattr(away_team, field, value)
                            updated = True
                    if updated:
                        away_team.save()
                away_team_obj = away_team
            except Exception as error:
                print(f"Falha ao processar Teams\n{error}")
            
            # Processar Match
            try:
                match_in_create = any(match.id == match_id for match in matches_to_create)
                match_in_update = any(match.id == match_id for match in matches_to_update)
                
                try:
                    match_obj = Match.objects.get(id=match_id)
                    fields_to_update = {
                            'date_time': match["date"],
                            'venue': match["venue"],
                            'city': match["city"],
                            'status': match["status"],
                            'league': league_obj if match_obj.league.id!= league_id else match_obj.league,
                            'home_team': home_team_obj if match_obj.home_team.id!= home_id else match_obj.home_team,
                            'away_team': away_team_obj if match_obj.away_team.id!= away_id else match_obj.away_team,
                            "home_goals": home_goals,
                            "away_goals": away_goals
                        } 
                    updated = False
                    for field, value in fields_to_update.items():
                        if getattr(match_obj, field)!= value:
                            setattr(match_obj, field, value)
                            updated = True
                    if updated:
                        matches_to_update.append(match_obj)
                except:
                    if not match_in_create and not match_in_update:
                        match_obj = Match(
                            id = match_id,
                            date_time = match["date"],
                            league = league_obj,
                            home_team = home_team_obj,
                            away_team = away_team_obj,
                            venue = match["venue"],
                            city = match["city"],
                            status = match["status"],
                            home_goals = home_goals,
                            away_goals = away_goals,
                        )
                        matches_to_create.append(match_obj)

            except Exception as error:
                print(f"Falha ao processar Match\n{error}")

    #Criar objetos em bulk
    try:
        if matches_to_create:
            Match.objects.bulk_create(matches_to_create)
    except Exception as error:
        print(f"Falha ao salvar matches\n{error}")

    try:
        if matches_to_update:
            Match.objects.bulk_update(matches_to_update, fields=['date_time', 'venue', 'city', 'status', 'league', 'home_team', 'away_team','home_goals', 'away_goals'])
    except Exception as error:
        print(f"Falha ao atualizar matches\n{error}")

def fetch_odds_football(bookmaker_id, days_to_fetch):
    current_year = datetime.datetime.now().year
    current_date = datetime.datetime.now().date()
    dates = [current_date + datetime.timedelta(days=i) for i in range(days_to_fetch)]
    
    url = "https://v3.football.api-sports.io/odds"

    params_base = {
        "season": current_year,
        "timezone": "America/Sao_Paulo",
        "bookmaker": bookmaker_id
    }

    for date in dates:
        formated_date = date.strftime("%Y-%m-%d")
        print(formated_date)
        page = 1
        while True:
            print(page)
            params = params_base.copy()
            params["date"] = formated_date
            params["page"] = page
            
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if len(result['response']) == 0:
                print('acabaram as páginas')
                break  # não há mais dados, podemos parar
                
            for match in result['response']:
                match_id = match['fixture']['id']
                print(f'PARTIDA - [{match_id}]')
                update = match['update']

                market_obj = None
                match_obj = None
                try:
                    match_obj = Match.objects.get(id=match['fixture']['id'])
                except:
                    continue
                
                # Market
                for market in match['bookmakers'][0]['bets']:
                    market_id = market['id']
                    market_name = market['name']
                    print(f'market - [{market_id}] - [{market_name}]')
                    uu_id = uuid.uuid4()
                    
                    market_obj, created = Market.objects.get_or_create(
                        number=market['id'],
                        match=match_obj,
                        defaults={
                            'id': uu_id,
                            'name': market["name"]
                        }
                    )
                    if created:
                        bets_to_create = []
                        for bet in market['values']:
                            bet_obj = Bet(
                                market=market_obj,
                                name=bet['value'],
                                odd=bet['odd']
                            )
                            bets_to_create.append(bet_obj)
                        Bet.objects.bulk_create(bets_to_create)
                    else:
                        # Se o Market já existia, atualiza as Bets existentes
                        bets_to_update = []
                        bets_to_create = []
                        for bet in market['values']:
                            # Procura a Bet existente associada ao Market
                            bet_obj = Bet.objects.filter(market=market_obj, name=bet['value']).first()
                            
                            if bet_obj:
                                if bet_obj.odd != bet['odd']:
                                    # Atualiza o campo odd se a Bet já existir
                                    bet_obj.odd = bet['odd']
                                    bets_to_update.append(bet_obj)
                            else:
                                # Se a Bet não existir, cria uma nova
                                new_bet = Bet(
                                    market=market_obj,
                                    name=bet['value'],
                                    odd=bet['odd']
                                )
                                bets_to_create.append(new_bet)
                        
                        # Salva as Bets atualizadas
                        Bet.objects.bulk_update(bets_to_update, ['odd'])
                        # Salva as novas Bets
                        Bet.objects.bulk_create(bets_to_create)
                print('\n')
            page += 1  # ir para a próxima página

def execute():
    print('Atualizando partidas')
    start_time = time.time()
    data = fetch_matches_and_leagues_football(days_to_fetch=3)
    end_time = time.time()
    print(f"Tempo de execução: {end_time - start_time:.2f} segundos\n")
    
    print('Salvando no banco de dados')
    start_time = time.time()
    save_matches_and_leagues_footbal(data)
    end_time = time.time() 
    print(f"Tempo de execução: {end_time - start_time:.2f} segundos\n")

