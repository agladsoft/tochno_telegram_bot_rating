import json
import asyncio
import math
import re
import logging
from typing import Optional, Dict, Tuple, Any

import aiohttp
from bs4 import BeautifulSoup
from tabulate import tabulate

from src.settings import setting

logging.basicConfig(level=logging.INFO)


class HttpClient:
    """Класс для выполнения HTTP-запросов."""

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/110.0.0.0 Safari/537.36")
    }

    @staticmethod
    async def fetch(url: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[str]:
        """Выполняет HTTP-запрос и возвращает ответ."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120),
                                             headers=HttpClient.headers) as session:
                async with (session.get(url, ssl=False) if method == "GET" else session.post(url, data=data,
                                                                                             ssl=False)) as response:
                    response.raise_for_status()
                    return await response.text()
        except aiohttp.ClientError as e:
            logging.error(f"HTTP error: {e}")
            return None


class VoteCounter:
    """Класс для получения количества голосов по post_id."""

    @staticmethod
    async def get_count(post_id: str) -> tuple[Any, Any]:
        """Получает количество голосов для указанного post_id."""
        data = {"action": "load_results", "postID": post_id}
        response = await HttpClient.fetch(setting.URL_VOTE, method="POST", data=data)
        try:
            votes = json.loads(response)['voteCount']
            rating = json.loads(response)['avgRating']
        except (KeyError, TypeError, json.JSONDecodeError):
            return "N/A", "N/A"
        return votes, rating

    @staticmethod
    def calculate_votes_for_target_difference(rating_first, votes_first, rating_second, votes_second,
                                              target_diff=setting.COMPARE_RATING) -> int:
        """
    Рассчитывает, сколько дополнительных голосов необходимо добавить, чтобы добиться разницы в рейтингах
    между первой и второй компанией равной target_diff. При этом:
      - К первой компании прибавляются голоса с оценкой 5.
      - К второй компании прибавляются голоса с оценкой 1.

    Новый рейтинг компаний вычисляется как:
      R1 = (S1 + 5*x) / (votes_first + x)
      R2 = (S2 + 1*x) / (votes_second + x)
    где:
      S1 = rating_first * votes_first
      S2 = rating_second * votes_second
    Требуется, чтобы R1 - R2 = target_diff.

    Путём приведения уравнения к виду A*x² + B*x + C = 0 получаем:
      A = (4 - target_diff)
      B = (S1 - S2 + 5*votes_second - votes_first) - target_diff * (votes_first + votes_second)
      C = S1 * votes_second - S2 * votes_first - target_diff * votes_first * votes_second

    Функция решает это уравнение, выбирает положительный корень и округляет результат до ближайшего
    целого числа вверх (так как число голосов должно быть целым).

    Аргументы:
      rating_first (float): текущий рейтинг первой компании.
      votes_first (int): текущее количество голосов первой компании.
      rating_second (float): текущий рейтинг второй компании.
      votes_second (int): текущее количество голосов второй компании.
      target_diff (float): требуемая разница между рейтингами (по умолчанию 0.1).

    Возвращает:
      int: необходимое количество дополнительных голосов, которое нужно добавить к обеим компаниям
           (положительные для первой с оценкой 5 и отрицательные для второй с оценкой 1),
           чтобы разница в рейтингах стала равной target_diff.
    """
        # Вычисляем суммарные баллы для каждой компании

        S1 = rating_first * votes_first
        S2 = rating_second * votes_second

        # Коэффициенты квадратного уравнения A*x² + B*x + C = 0
        A = 4 - target_diff
        B = (S1 - S2 + 5 * votes_second - votes_first) - target_diff * (votes_first + votes_second)
        C = S1 * votes_second - S2 * votes_first - target_diff * votes_first * votes_second

        discriminant = B ** 2 - 4 * A * C
        if discriminant < 0:
            raise ValueError("Дискриминант меньше нуля. Нет действительного решения для заданных параметров.")

        # Выбираем положительный корень уравнения
        x = (-B + math.sqrt(discriminant)) / (2 * A)
        return math.ceil(x)


class HtmlParser:
    """Класс для парсинга HTML и объединения информации с голосами."""

    @staticmethod
    def compare_first_and_second_place_ratings(first_place_rating: float, second_place_rating: float) -> bool:
        return round(first_place_rating - second_place_rating, 4) >= setting.COMPARE_RATING

    @staticmethod
    async def parse_top_developers() -> str | None:
        """
        Парсит страницу с топом застройщиков и для каждого элемента,
        если доступна ссылка, извлекает post_id и получает количество голосов.
        Возвращает строку с таблицей результатов.
        """
        html = await HttpClient.fetch(setting.URL_TOP)
        if not html:
            return "Ошибка загрузки страницы"

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("div", class_="top-zastroyshikov-table")
        if not table:
            return "Нет данных"

        rows = table.find_all("div", id="rating-table-item")[:5]
        data = []
        first_place = 0
        first_voites = 0
        for index, row in enumerate(rows, 1):
            # Извлекаем место
            place_div = row.find("div", class_="top-zastroyshikov-1")
            place_text = place_div.get_text(strip=True) if place_div else "?"

            # Извлекаем название и, если есть ссылка – голосование
            name_div = row.find("div", class_="top-zastroyshikov-2")
            a_tag = name_div.find("a") if name_div else None
            if a_tag:
                name = a_tag.get_text(strip=True)
                vote_page_url = a_tag.get("href", "")
                post_id = await HtmlParser.extract_post_id(vote_page_url)
                votes, rating = await VoteCounter.get_count(post_id) if post_id else "N/A"
                if index == 2 and HtmlParser.compare_first_and_second_place_ratings(first_place, float(rating)):
                    return f"Разница между 1 и 2 местом не более {setting.COMPARE_RATING} ⭐"


            else:
                name = name_div.get_text(strip=True) if name_div else "Неизвестно"
                rating = "N/A"
                votes = "N/A"

            first_place = rating
            first_voites = votes
            data.append(f"🏆 {place_text}. *{name}* — {rating} ⭐, Голоса: {votes}")

        result_table = "\n".join(data)
        result_table += f"\n\n👉 [Подробнее]({setting.URL_TOP})"
        return result_table

    @staticmethod
    async def extract_post_id(url: str) -> Optional[str]:
        """
        Извлекает post_id из тега <script> на странице по заданному URL.
        Ищет шаблон "post_id":<цифры>.
        """
        html = await HttpClient.fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        script_tag = soup.find("script", string=re.compile(r'"post_id":(\d+)'))
        if script_tag and (match := re.search(r'"post_id":(\d+)', script_tag.string)):
            return match[1]
        return None


# asyncio.run(HtmlParser.parse_top_developers())
