from api.models import League, Match, Team, Market, Bet, Ticket
from api.serializers import LeaguesBySportIdCategorys, MatchSerializer, TeamSerializer, OddSerializer, LeagueSerializer

from rest_framework import status as status_code
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response

from .pagination.pagination import CustomPageNumberPagination

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import random
import json
from datetime import datetime

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from .tasks import *

from api.services import betsapi
#betsapi.execute_odds_football()
# def index(request):
#     my_task.delay()
#     return HttpResponse('Task rodando!')

# def schedule_task(request):
#     interval, _ = IntervalSchedule.objects.get_or_create(
#         every=10,
#         period=IntervalSchedule.SECONDS,
#     )

#     PeriodicTask.objects.create(
#         interval=interval,
#         name="my-schedule",
#         task="api.tasks.my_task",
#         #args=json.dump(['Arg1', 'Arg2'])
#         #one_off=True
#     )
    
#     return HttpResponse("Task schedule!")

class Login(APIView):
    @swagger_auto_schema(
        operation_description="Este endpoint permite a autenticação de usuários. Enviar os campos 'username' and 'password' via formulário para essa rota",
        responses={202: 'Logado com sucesso', 400: 'Preencha o nome de usuário e a senha', 401: 'Credenciais inválidas'},
        tags=['Autenticação'],
    )
    #@csrf_exempt
    def post(self, request):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        username = body['username']
        password = body['password']
        
        if not username or not password:
            return Response(data={'detail': 'Preencha o nome de usuário e a senha'}, status=status_code.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
                login(request, user)
                return Response(data={'detail': 'Logado com sucesso'}, status=status_code.HTTP_202_ACCEPTED)
        else:
            return Response(data={'detail': 'Credenciais inválidas'}, status=status_code.HTTP_401_UNAUTHORIZED)

class Logout(APIView):
    @swagger_auto_schema(
        operation_description="Este endpoint permite deslogar o usuário",
        responses={202: 'Deslogado com sucesso'},
        tags=['Autenticação'],
    )
    #@csrf_exempt
    def post(self, request):
        try:
            logout(request)
            return Response(data={'detail': 'Deslogado com sucesso'}, status=status_code.HTTP_202_ACCEPTED)
        except:
            return Response(data={'detail': 'Não existe usuário logado'}, status=status_code.HTTP_400_BAD_REQUEST)

class LeagueList(APIView):
    @swagger_auto_schema(
        operation_description="Este endpoint lista todas as ligas disponíveis.",
        responses={200: 'Dados retornados com sucesso'},
        tags=['Ligas'],  # Tags para organizar no Swagger UI
        manual_parameters=[
            openapi.Parameter(
                'sport_id',
                openapi.IN_QUERY,
                description="parâmetro para filtrar os dados pelo esporte",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="parâmetro para filtrar os dados pela categoria",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'active',
                openapi.IN_QUERY,
                description="parâmetro para filtrar os dados pelo status ativo",
                type=openapi.TYPE_BOOLEAN
            ),
        ],
    )
    def get(self, request):
        category = request.query_params.get('category', None)
        sport_id = request.query_params.get('sport_id', None)
        active = request.query_params.get('active', None)
        
        leagues = League.objects.all()
        
        if category:
            leagues = leagues.filter(country=category)
        
        if sport_id:
            leagues = leagues.filter(sport_id=sport_id)

        if active:
            status = active.lower()
            if status == 'true':
                active = True
            elif status == 'false':
                active = False
            leagues = leagues.filter(active=active)
        
        #Mostrar leagues por sport_id > CC (Category)
        leagues_by_sport_id_category = {}
        for league in leagues:
            if league.sport_id not in leagues_by_sport_id_category:
                leagues_by_sport_id_category[league.sport_id] = {}
            if league.country not in leagues_by_sport_id_category[league.sport_id]:
                leagues_by_sport_id_category[league.sport_id][league.country] = []
            serializer = LeaguesBySportIdCategorys(league)
            leagues_by_sport_id_category[league.sport_id][league.country].append(serializer.data)

        return Response(leagues_by_sport_id_category)

class MatchList(APIView):
    pagination_class = CustomPageNumberPagination  # Use a classe de paginação personalizada

    @swagger_auto_schema(
        operation_description="Este endpoint lista todas as partidas disponíveis",
        responses={200: 'Dados retornados com sucesso', 204: 'Não encontrado', 404: 'Inexistente'},
        tags=['Partidas'],  # Tags para organizar no Swagger UI
        manual_parameters=[
            openapi.Parameter(
                'league_id',
                openapi.IN_QUERY,
                description="Parâmetro para filtrar as partidas de uma determinada liga",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Parâmetro para filtrar as partidas por um determinado status \nhttps://www.api-football.com/documentation-v3#tag/Fixtures/operation/get-fixtures",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Parâmetro para filtrar as partidas por dia",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Parâmetro para filtrar a página",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'match_id',
                openapi.IN_QUERY,
                description="Parâmetro para filtrar pelo id da partida",
                type=openapi.TYPE_INTEGER
            ),
        ],
    )
    def get(self, request):
        league_id = request.query_params.get('league_id', None)
        status = request.query_params.get('status', None)
        date = request.query_params.get('date', None)
        match_id = request.query_params.get('match_id', None)
        
        matches = Match.objects.with_bets()
        
        if match_id:
            matches = matches.filter(id=match_id)
            if not matches.exists():
                return Response(data={'detail': 'Partida inexistente'}, status=status_code.HTTP_404_NOT_FOUND)

        if league_id:
            try:
                league = League.objects.get(pk=league_id)
                matches = matches.filter(league=league)
            except League.DoesNotExist:
                return Response(data={'detail': 'Liga inexistente'}, status=status_code.HTTP_404_NOT_FOUND)
            
            if not matches.exists():
                return Response(data={'detail': 'Não há partidas para essa liga'}, status=status_code.HTTP_204_NO_CONTENT)

        if status:
            matches = matches.filter(status=status)
            if not matches.exists():
                return Response(data={'detail': 'Não há partidas com esse status'}, status=status_code.HTTP_204_NO_CONTENT)
        
        if date:
            try:
                # Convertendo a string para um objeto datetime
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                ano = date_obj.year
                mes = date_obj.month
                dia = date_obj.day

                # Filtrando os objetos Match pelo ano, mês e dia extraídos
                matches = matches.filter(date_time__year=ano, date_time__month=mes, date_time__day=dia)
                if not matches.exists():
                    return Response(data={'detail': 'Não há partidas para essa data'}, status=status_code.HTTP_204_NO_CONTENT)
        
            except ValueError:
                return Response(data={'detail': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=status_code.HTTP_400_BAD_REQUEST)
            
        paginator = self.pagination_class()  # Use a classe de paginação personalizada
        paginated_matches = paginator.paginate_queryset(matches, request)
        
        serializer = MatchSerializer(paginated_matches, many=True)
        return paginator.get_paginated_response(serializer.data)

class MatchLiveList(APIView):
    pagination_class = CustomPageNumberPagination  # Use a classe de paginação personalizada

    @swagger_auto_schema(
        operation_description="Este endpoint lista todas as partidas ao vivo disponíveis",
        responses={200: 'Dados retornados com sucesso', 204: 'Não há partidas cadastradas', 404: 'Liga inexistente'},
        tags=['Partidas'],  # Tags para organizar no Swagger UI
        manual_parameters=[
            openapi.Parameter(
                'league_id',
                openapi.IN_QUERY,
                description="Parâmetro para filtrar as partidas de uma determinada liga",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Parâmetro para filtrar a página",
                type=openapi.TYPE_INTEGER
            ),
        ],
    )
    def get(self, request):
        league_id = request.query_params.get('league_id', None)
        
        matches = Match.objects.with_bets()
        matches = matches.filter(status__in=['1H', '2H', 'HT', 'ET', 'BT', 'P', 'SUSP', 'INT']).with_bets()
        if league_id:
            try:
                league = League.objects.get(pk=league_id)
                matches = matches.filter(league=league)
            except League.DoesNotExist:
                return Response(data={'detail': 'Liga inexistente'}, status=status_code.HTTP_404_NOT_FOUND)
            
            if not matches.exists():
                return Response(data={'detail': 'Não há partidas para essa liga'}, status=status_code.HTTP_204_NO_CONTENT)
        
        # Agrupando as partidas por liga
        matches_by_league = {}
        for match in matches:
            league_id = match.league.id
            if league_id not in matches_by_league:
                matches_by_league[league_id] = {
                    'league': LeagueSerializer(match.league).data,
                    'matches': []
                }
            matches_by_league[league_id]['matches'].append(MatchSerializer(match).data)
        
        # Convertendo o dicionário em uma lista de resultados
        organized_matches = list(matches_by_league.values())
        
        paginator = self.pagination_class()  # Use a classe de paginação personalizada
        paginated_matches = paginator.paginate_queryset(organized_matches, request)
        
        return paginator.get_paginated_response(paginated_matches)

class TeamList(APIView):
    @swagger_auto_schema(
        operation_description="Este endpoint lista todos os times disponíveis",
        responses={200: 'Dados retornados com sucesso', 204: 'Não há times cadastrados'},
        tags=['Times'],  # Tags para organizar no Swagger UI
        manual_parameters=[
        ]
    )
    def get(self, request):
        
        teams = Team.objects.all()

        if len(teams) == 0:
            return Response(data={'detail': 'Não há times cadastrados'}, status=status_code.HTTP_204_NO_CONTENT)

        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

class OddsList(APIView):
    @swagger_auto_schema(
        operation_description="Este endpoint lista todas as odds disponíveis",
        responses={200: 'Dados retornados com sucesso', 204: 'Não existem odds cadastradas para essa partida', 400: 'É necessário especificar uma partida para que sejam retornados os dados', 404: 'Partida inexistente'},
        tags=['Odds'],
        manual_parameters=[
            openapi.Parameter(
                'match_id',
                openapi.IN_QUERY,
                description="parâmetro para filtrar as odds de uma determinada partida",
                type=openapi.TYPE_INTEGER
            ),
        ],
    )
    def get(self, request):
        
        match_id = request.query_params.get('match_id', None)
        
        if match_id:
            try:
                match_obj = Match.objects.get(id=match_id)
                markets = Market.objects.filter(match=match_obj)
                if len(markets) == 0:
                    return Response(data={'detail': 'Não existem odds cadastradas para essa partida'}, status=status_code.HTTP_204_NO_CONTENT)
            except:
                return Response(data={'detail': 'Partida inexistente'}, status=status_code.HTTP_404_NOT_FOUND)
        else:
            return Response(data={'detail': 'É necessário especificar uma partida para que sejam retornados os dados'}, status=status_code.HTTP_400_BAD_REQUEST)

        serializer = OddSerializer(markets, many=True)
        return Response(serializer.data)

class TicketRoute(APIView):
    @swagger_auto_schema(
        operation_description="Este endpoint lista todas os tickets disponíveis",
        responses={200: 'Ok'},
        tags=['Tickets'],
    )
    def get():
        pass
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ticket': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_quotation': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Total da cotação esperado'),
                        'bet_value': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description='Valor da aposta'),
                        'bet_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description='Lista de IDs das apostas'),
                    },
                    required=['total_quotation', 'bet_value', 'bet_ids']
                )
            },
            required=['ticket']
        ),
        responses={
            201: openapi.Response(
                description='Bilhete criado com sucesso',
                examples={
                    'application/json': {
                        'detail': 'Bilhete criado com sucesso',
                        'pin': '12345'
                    }
                }
            ),
            400: openapi.Response(
                description='Solicitação mal formada ou dados inválidos',
                examples={
                    'application/json': {
                        'detail': 'Erro ao decodificar o JSON.',
                    }
                }
            ),
            404: openapi.Response(
                description='Uma ou mais apostas não foram encontradas',
                examples={
                    'application/json': {
                        'detail': 'Bet de id 342153 não existe.'
                    }
                }
            ),
            406: openapi.Response(
                description='total_quotation diferente do produto das cotações presentes no banco',
                examples={
                    'application/json': {
                        'detail': 'total_quotation diferente do produto das cotações presentes no banco',
                        'bet_odds': [
                            {'id': '342153', 'odd': 1.5},
                            {'id': '454353', 'odd': 2.0}
                        ],
                        'correct_total_quotation': 3.0
                    }
                }
            ),
        },
        tags=['Tickets']
    )
    def post(self, request):
        try:
            # Decodifica e carrega o JSON
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            
            # Valida a estrutura do JSON
            if not isinstance(body, dict):
                return Response(data={'detail': 'Formato JSON inválido.'}, status=status_code.HTTP_400_BAD_REQUEST)
            
            ticket = body.get('ticket')
            if not isinstance(ticket, dict):
                return Response(data={'detail': 'Campo "ticket" está faltando ou é inválido.'}, status=status_code.HTTP_400_BAD_REQUEST)
            
            total_quotation = ticket.get('total_quotation')
            bet_value = ticket.get('bet_value')
            bet_ids = ticket.get('bet_ids')
            
            # Verifica se os campos obrigatórios estão presentes
            if total_quotation is None or bet_value is None or bet_ids is None:
                return Response(data={'detail': 'Campos obrigatórios estão faltando.'}, status=status_code.HTTP_400_BAD_REQUEST)
            
            try:
                total_quotation = float(total_quotation)
            except ValueError:
                return Response(data={'detail': 'total_quotation deve ser um número.'}, status=status_code.HTTP_400_BAD_REQUEST)
            
            if not isinstance(bet_ids, list):
                return Response(data={'detail': 'bet_ids deve ser uma lista.'}, status=status_code.HTTP_400_BAD_REQUEST)
            
            total_odds = 1
            bet_odds = []
            bet_objects = []
            for bet_id in bet_ids:
                try:
                    bet = Bet.objects.get(id=bet_id)
                    total_odds *= bet.odd
                    bet_odds.append({'id': bet_id, 'odd': bet.odd})
                    bet_objects.append(bet)
                except Bet.DoesNotExist:
                    return Response(data={'detail': f'Bet de id {bet_id} não existe.'}, status=status_code.HTTP_404_NOT_FOUND)

            if float(total_odds) == total_quotation:
                unique_pin = ''
                while True:
                    pin = f"{random.randint(0, 99999):05d}"  # Gera um PIN de 5 dígitos
                    if not Ticket.objects.filter(pin=pin).exists():  # Verifica se o PIN já existe no banco
                        unique_pin = pin
                        break
                
                try:
                    ticket = Ticket(value=bet_value, pin=unique_pin)
                    ticket.save()
                    if bet_objects:  # Verifica se bet_objects não está vazio
                        ticket.bets.add(*bet_objects)

                    return Response(data={'detail': 'bilhete criado com sucesso', 'pin': ticket.pin}, status=status_code.HTTP_201_CREATED)
                except:
                    return Response(data={'detail': 'Erro ao salvar o bilhete no banco'}, status=status_code.HTTP_422_UNPROCESSABLE_ENTITY)
            else:
                return Response(data={'detail': 'total_quotation diferente do produto das cotações presentes no banco', 'bet_odds': bet_odds, 'correct_total_quotation': total_odds}, status=status_code.HTTP_406_NOT_ACCEPTABLE)

        except json.JSONDecodeError:
            return Response(data={'detail': 'Erro ao decodificar o JSON.'}, status=status_code.HTTP_400_BAD_REQUEST)