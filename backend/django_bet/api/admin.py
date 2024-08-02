from django.contrib import admin
from .models import League, Team, Match, Market, Bet, Ticket

class LeagueAdmin(admin.ModelAdmin):
    list_display =  ('id', 'sport_id', 'name', 'country','active') 

class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'logo') 

class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'home_team', 'away_team', 'status', 'league', 'city', 'home_goals', 'away_goals')

class MarketAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'name', 'match', 'category')
    
class BetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'odd', 'market')

class TicketAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Modifica o queryset para o campo `bets` apenas se a instância do objeto for editada
        if obj:
            form.base_fields['bets'].queryset = Bet.objects.filter(tickets=obj)
        
        return form
    
admin.site.register(League, LeagueAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Market, MarketAdmin)
admin.site.register(Bet, BetAdmin)
admin.site.register(Ticket, TicketAdmin)