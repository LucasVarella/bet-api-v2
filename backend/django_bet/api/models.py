from django.db import models
from django.db.models import Count
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class League(models.Model):
    id = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999)],
        primary_key=True
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo = models.CharField(max_length=200)
    country = models.CharField(max_length=40)
    flag = models.CharField(max_length=200, null=True)
    sport_id =  models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(999)]
    )
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Team(models.Model):
    id = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999)],
        primary_key=True
    )
    name = models.CharField(max_length=100)
    logo = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class MatchQuerySet(models.QuerySet):
    def with_bets(self):
        return self.annotate(bet_count=Count('markets__bets')).filter(bet_count__gt=0)

class Match(models.Model):
    id = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        primary_key=True
    )
    date_time = models.DateTimeField()
    venue = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=2)
    league = models.ForeignKey(League, related_name='matches', on_delete=models.CASCADE)
    home_team = models.ForeignKey(Team, related_name='home_matches', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_matches', on_delete=models.CASCADE)
    odds_update = models.DateTimeField(null=True)
    home_goals = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)], null=True)
    away_goals = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)], null=True)
    
    objects = MatchQuerySet.as_manager()
    
    def __str__(self):
        return f'{self.id} - [{self.home_team.name} x {self.away_team.name}] - [{self.status}] - [{self.league}] - [{self.date_time}] '

class Market(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    number = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        null=True
    )
    match = models.ForeignKey(Match, related_name='markets', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, null=True)
    
    def __str__(self):
        return f'[{self.number}] - [{self.name}] - [{self.match.id}]'

class Bet(models.Model):
    # id = models.IntegerField(
    #     validators=[MinValueValidator(0), MaxValueValidator(99999)],
    #     primary_key=True
    # )
    market = models.ForeignKey(Market, related_name='bets', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    odd = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f'[{self.market}] - [{self.name}] - [{self.odd}]'

class User(AbstractUser):
    email = models.CharField(max_length=100, null=True)

class Customer(models.Model):
    name = models.CharField(max_length=100, null=True)
    collaborator = models.ForeignKey(User, related_name='tickets', on_delete=models.CASCADE)

class Ticket(models.Model):
    pin = models.CharField(max_length=5, default='false')
    validated = models.BooleanField(default=False)
    customer = models.ForeignKey(Customer, related_name='tickets', on_delete=models.DO_NOTHING, null=True)
    collaborator = models.ForeignKey(User, related_name='collaborator_tickets', on_delete=models.DO_NOTHING, null=True)
    manager = models.ForeignKey(User, related_name='manager_tickets', on_delete=models.DO_NOTHING, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    bets = models.ManyToManyField(Bet, related_name='tickets')
    
    def __str__(self):
        return f'[{self.id}] - [{self.validated}] - [{self.pin}]'