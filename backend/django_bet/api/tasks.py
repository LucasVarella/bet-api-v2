from celery import shared_task
from redis import Redis
from django.conf import settings
import time

from api.services import betsapi

# Configuração do Redis
redis_instance = Redis.from_url(settings.CELERY_BROKER_URL)

@shared_task
def update_matches_football():
    lock_key = 'update_matches_football_lock'
    lock_timeout = 1000  # Tempo em segundos para considerar que a tarefa foi concluída
    
    # Tenta adquirir o bloqueio
    lock_acquired = redis_instance.set(lock_key, 'locked', nx=True, ex=lock_timeout)

    if not lock_acquired:
        # Se o bloqueio não foi adquirido, a tarefa está em execução
        print('Outra instância da tarefa está em execução')
        return 'Outra instância da tarefa está em execução'
    try:
        # Chama a função da API para atualizar os matches
        betsapi.execute_fetch_football()
        print('Tarefa concluída com sucesso')
        return 'Tarefa concluída com sucesso'
    except:
        print('Falha ao executar a atualização das partidas')
        return ('Falha ao executar a atualização das partidas')
    finally:
        # Libera o bloqueio após a conclusão da tarefa
        redis_instance.delete(lock_key)

@shared_task
def update_odds_football():
    betsapi.execute_odds_football()
