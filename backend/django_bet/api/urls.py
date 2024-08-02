from django.urls import path
from api.views import LeagueList, MatchList, TeamList, OddsList, MatchLiveList, Login, Logout, TicketRoute
from . import views

urlpatterns=[ 
    #path('task', views.index, name='index'),
    #path('schedule', views.schedule_task, name='schedule'),
    path('leagues', LeagueList.as_view()),
    path('matches', MatchList.as_view()),
    path('matches-live', MatchLiveList.as_view()),
    path('teams', TeamList.as_view()),
    path('odds', OddsList.as_view()),
    path('tickets', TicketRoute.as_view()),
    path('login', Login.as_view()),
    path('logout', Logout.as_view()),
    #path('leagues/<int:pk>/', LeagueListAndCreate.as_view()),
]