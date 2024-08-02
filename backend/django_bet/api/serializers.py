from api.models import League, Match, Team, Market, Bet

from rest_framework import serializers

class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ['id', 'name', 'slug', 'logo', 'country', 'flag']

class LeaguesBySportIdCategorys(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ['id', 'name','slug', 'logo', 'country', 'flag', 'active']

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name','logo']

class BetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        fields = ['id', 'name', 'odd']

class OddSerializer(serializers.ModelSerializer):
    bets = BetSerializer(many=True, read_only=True)
    
    class Meta:
        model = Market
        fields = ['id','name','category', 'bets']

class MatchSerializer(serializers.ModelSerializer):
    league = LeagueSerializer(read_only=True)
    home_team = TeamSerializer(read_only=True)
    away_team = TeamSerializer(read_only=True)
    main_market = serializers.SerializerMethodField()
    bet_count = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ['id','date_time','status', 'city', 'venue', 'home_team', 'away_team', 'home_goals', 'away_goals', 'league', 'main_market', 'bet_count']
    def get_main_market(self, obj):
        markets = obj.markets.filter(name='Match Winner')
        if markets.exists():
            return OddSerializer(markets, many=True).data
        else:
            return []
    def get_bet_count(self, obj):
        total_bets = Bet.objects.filter(market__match=obj).count()
        count = total_bets - 3
        return count
