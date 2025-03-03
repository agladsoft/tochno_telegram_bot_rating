from src.settings import get_settings
from celery import Celery
from src.scripts.tasks.ratings import main

celery_app = Celery('tasks', broker=f'{get_settings().REDIS_URL}')


@celery_app.task(name='put_your_vote')
def put_your_vote(post_id, star_rating, voices):
    return main(post_id, star_rating, voices)


def send_vote_to_background(post_id: str, star_rating: str, voices: int):
    put_your_vote.delay(post_id, star_rating, voices)
