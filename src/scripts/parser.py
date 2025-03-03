import json
import asyncio
import math
import re
import logging
from typing import Optional, Dict, Any

import aiohttp
import aiofiles
from bs4 import BeautifulSoup

from src.settings import get_settings

logging.basicConfig(level=logging.INFO)

JSON_FILE = "data.json"


async def load_from_json() -> dict:
    try:
        async with aiofiles.open(JSON_FILE, "r") as f:
            content = await f.read()
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


async def save_to_json(data: dict):
    async with aiofiles.open(JSON_FILE, "w") as f:
        await f.write(json.dumps(data, indent=4))


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
        response = await HttpClient.fetch(get_settings().URL_VOTE, method="POST", data=data)
        try:
            votes = json.loads(response)['voteCount']
            rating = json.loads(response)['avgRating']
        except (KeyError, TypeError, json.JSONDecodeError):
            return "N/A", "N/A"
        return votes, rating


class HtmlParser:
    """Класс для парсинга HTML и обновления информации о голосах."""

    @staticmethod
    async def parse_top_developers() -> Optional[str]:
        """
        Парсит страницу с топом застройщиков, извлекает post_id, получает количество голосов,
        сравнивает с сохранёнными данными и обновляет JSON при изменениях.
        """
        html = await HttpClient.fetch(get_settings().URL_TOP)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("div", class_="top-zastroyshikov-table")
        if not table:
            return None

        rows = table.find_all("div", id="rating-table-item")[:10]
        data = await load_from_json()
        new_data = {}
        result = []
        updated = False

        for row in rows:
            name_div = row.find("div", class_="top-zastroyshikov-2")
            a_tag = name_div.find("a") if name_div else None
            if a_tag:
                name = a_tag.get_text(strip=True)
                vote_page_url = a_tag.get("href", "")
                post_id = await HtmlParser.extract_post_id(vote_page_url)
                votes, rating = await VoteCounter.get_count(post_id) if post_id else ("N/A", "N/A")

                new_data[post_id] = {"name": name, "rating": rating, "votes": votes}
                if post_id not in data or (int(votes) - int(data[post_id]["votes"])) >= get_settings().DELTA_THRESHOLD:
                    updated = True
                result.append(f"🏆 *{name}* — {rating} ⭐, Голоса: {votes}")

        if updated:
            await save_to_json(new_data)
            result_table = "\n".join(result)
            result_table += f"\n\n👉 [Подробнее]({get_settings().URL_TOP})"
            return result_table
        return None

    @staticmethod
    async def extract_post_id(url: str) -> Optional[str]:
        """
        Извлекает post_id из тега <script> на странице по заданному URL.
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
