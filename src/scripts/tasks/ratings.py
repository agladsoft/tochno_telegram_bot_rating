import os
import random
import string
import time
import json
import subprocess
import requests
from src.scripts.logger import app_logger as logger
from src.settings import get_settings
from src.scripts.__init__ import *


def get_my_ip():
    try:
        response = requests.get("https://api.myip.com")
        logger.info(response.json())
        return response.json()['ip']  # Выведет {'ip': 'X.X.X.X', 'country': 'YourCountry'}
    except requests.RequestException as e:
        print(f"Ошибка при запросе через прокси: {e}")


def set_proxy() -> None:
    """
    Устанавливает прокси для HTTPS-запросов.

    Использует настройки из setting.PROXY для формирования переменной окружения.
    """
    os.environ['https_proxy'] = f'http://{get_settings().PROXY}'


def check_proxy() -> bool:
    """
    Проверяет работоспособность прокси через попытку доступа к Google.

    :raises RuntimeError: Если прокси не работает или запрос завершается ошибкой.
    :return: True, если запрос успешен.
    """
    try:
        response = requests.get("https://google.com", timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Прокси http://{get_settings().PROXY} не работает: {e}")
        raise RuntimeError(f"Прокси http://{get_settings().PROXY} не работает: {e}")

    return True


def send_curl_request(curl_command: str) -> dict:
    """
    Выполняет curl-запрос и возвращает ответ в виде словаря.

    :param curl_command: Строка с командой curl.
    :return: Словарь с ключами 'status_code', 'response' и 'errors'.
    """
    try:
        result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
        return {
            "status_code": result.returncode,
            "response": json.loads(result.stdout) if result.stdout else None,
            "errors": result.stderr or None
        }
    except Exception as e:
        logger.error(f"error {str(e)}")
        return {"error": str(e)}


def register_user(sub: str, first_name: str, second_name: str, city: str, phone: str, second_number: str,
                  email: str) -> dict:
    """
    Регистрирует пользователя перед голосованием.

    Формирует curl-запрос для регистрации пользователя.

    :param sub: Категория или подгруппа.
    :param first_name: Имя пользователя.
    :param second_name: Фамилия пользователя.
    :param city: Город пользователя.
    :param phone: Телефон в формате с разделителями.
    :param second_number: Телефон в цифровом формате.
    :param email: Email пользователя.
    :return: Результат выполнения curl-запроса в виде словаря.
    """
    curl_command = f"""curl --location 'https://xn--b1agapfwapgcl.xn--p1ai/wp-json/contact-form-7/v1/contact-forms/16044/feedback' \
        --form '_wpcf7=16044' \
        --form '_wpcf7_version=6.0.4' \
        --form '_wpcf7_locale=ru_RU' \
        --form '_wpcf7_unit_tag=wpcf7-f16044-o2' \
        --form '_wpcf7_container_post=0' \
        --form '_wpcf7_posted_data_hash=' \
        --form 'category={sub}' \
        --form 'firstname={first_name}' \
        --form 'lastname={second_name}' \
        --form 'city={city}' \
        --form 'phone-cf7it-national={phone}' \
        --form 'phone={second_number}' \
        --form 'phone-cf7it-country-name=Russia (Россия)' \
        --form 'phone-cf7it-country-code=7' \
        --form 'phone-cf7it-country-iso2=ru' \
        --form 'mail={email}' \
        --form 'wpcf7tg_sending=1'
        """
    return send_curl_request(curl_command)


def send_rating(post_id: str, star_rating: str) -> dict:
    """
    Отправляет рейтинг поста через curl-запрос.

    :param postID: Идентификатор поста.
    :param star_rating: Количество звезд для рейтинга.
    :return: Результат выполнения запроса в виде словаря.
    """
    curl_command = f"""curl --location 'https://xn--b1agapfwapgcl.xn--p1ai/wp-admin/admin-ajax.php' \
    --form 'action="process_rating"' \
    --form 'star_rating="{star_rating}"' \
    --form 'postID="{post_id}"' \
    --form 'duration="87"' \
    --form 'nonce="f9f9b17a49"'
    """
    return send_curl_request(curl_command)


# def generate_phone_number() -> tuple[str, str]:
#     """
#     Генерирует случайный российский номер телефона и возвращает его в двух форматах.
#
#     :return: Кортеж, где первый элемент – форматированный номер,
#              а второй – номер без форматирования.
#     """
#     number = f"+7{random.randint(9000000000, 9999999999)}"
#     formatted_number = f"+7 ({number[2:5]}) {number[5:8]}-{number[8:10]}-{number[10:]}"
#     return formatted_number, number


def generate_phone_number() -> tuple[str, str]:
    """
    Генерирует случайный российский номер телефона с использованием известных кодов операторов
    и возвращает его в двух форматах.

    :return: Кортеж, где первый элемент – форматированный номер вида +7 (XXX) XXX-XX-XX,
             а второй – номер без форматирования.
    """
    # Список известных операторских кодов
    known_codes = [
        "910", "915", "916", "919",
        "920", "921", "922", "923", "924", "928", "929",
        "903", "905", "906", "909", "960", "961", "962", "963", "964", "965", "966", "967", "968", "969",
        "902", "908", "950", "951", "952", "953", "954", "955", "956", "957", "958", "959",
        "977"
    ]
    code = random.choice(known_codes)

    # Генерируем оставшиеся 7 цифр с лидирующими нулями, если необходимо
    remaining_number = f"{random.randint(0, 9999999):07d}"

    # Формируем полный номер без форматирования
    full_number = f"+7{code}{remaining_number}"

    # Форматируем номер: +7 (XXX) YYY-YY-YY, где YYY-YY-YY – оставшиеся 7 цифр
    formatted_number = f"+7 ({code}) {remaining_number[:3]}-{remaining_number[3:5]}-{remaining_number[5:]}"

    return formatted_number, full_number


def generate_unique_email() -> str:
    """
    Генерирует уникальный email с одним из популярных российских доменов.

    :return: Сгенерированный email.
    """
    # Список популярных российских почтовых доменов
    domains = ["mail.ru", "rambler.ru", "list.ru", "internet.ru"]

    # Генерация случайного имени пользователя
    username_length = random.randint(5, 10)
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))

    # Выбор случайного домена
    domain = random.choice(domains)

    return f"{username}@{domain}"


def get_user_data() -> tuple[str, str, str, str, str, str, str]:
    """
    Генерирует случайные данные пользователя для регистрации.

    :return: Кортеж, содержащий:
             sub, first_name, second_name, city, phone, second_number, email.
    """
    sub = random.choice(SUBS)
    first_name = random.choice(NAMES)
    second_name = random.choice(LAST_NAME)
    city = random.choice(CITIES)
    phone, second_number = generate_phone_number()
    email = generate_unique_email()
    return sub, first_name, second_name, city, phone, second_number, email


def registrations(sub, first_name, second_name, city, phone, second_number, email) -> True:
    logger.info(f"Регистрируем пользователя {sub},{first_name},{second_name}, {city} {phone},{second_number}")
    registration_response = register_user(sub, first_name, second_name, city, phone, second_number, email)
    if not registration_response.get("response") or registration_response["response"].get("status") != "mail_sent":
        logger.error(
            f"Ошибка регистрации: {registration_response}")
        return False
    logger.info("Регистрация успешна. Начинаем голосование...")
    return True


def votes(post_id: str, star_rating: str):
    logger.info("Голосуем")
    rating_response = send_rating(post_id, star_rating)
    if rating_response.get("response"):
        avg_rating = rating_response["response"].get("avgRating", "Unknown")
        if not avg_rating:
            logger.error(f"Ошибка при отправке голоса: {rating_response}")
            raise RuntimeError(f"Ошибка при отправке голоса: {rating_response}")
        logger.info(
            f"Голос учтен. Текущий рейтинг: {avg_rating} Голоса : "
            f"{rating_response['response'].get('voteCount', 'Unknown')}")
        return True, False
    else:
        logger.error(f"Ошибка при отправке голоса: {rating_response}")
        raise RuntimeError(f"Ошибка при отправке голоса: {rating_response}")


def main(post_id: str, star_rating: str, voices: int) -> str:
    """
    Запускает процесс голосования заданное количество раз, учитывая IP-адрес.

    :param post_id: Идентификатор поста.
    :param star_rating: Количество звезд для рейтинга.
    :param voices: Количество успешных голосов, которые необходимо отправить.
    :return: Строка, уведомляющая о завершении голосования.
    """
    success_count = 0
    registered_users = {}
    current_ip = None
    user = None

    while success_count < voices:
        try:
            set_proxy()
            check_proxy()
            new_ip = get_my_ip()

            if new_ip != current_ip:
                current_ip = new_ip
                if current_ip in registered_users:
                    user = registered_users[current_ip]
                else:
                    user = get_user_data()
                    if registrations(*user):
                        registered_users[current_ip] = user
                    else:
                        time.sleep(15)
                        continue

            logger.info(f"Голосуем пользователем {user} с IP {current_ip}")

            # Ограничение попыток голосования
            vote_attempts = 0
            max_vote_attempts = 20  # лимит попыток голосования
            vote_successful = False
            while vote_attempts < max_vote_attempts:
                if votes(post_id, star_rating):
                    vote_successful = True
                    break
                time.sleep(15)
                # Если IP изменился в процессе голосования, прерываем попытку
                if get_my_ip() != current_ip:
                    break
                vote_attempts += 1

            if vote_successful:
                success_count += 1
                time.sleep(180)
            else:
                logger.warning("Голосование не выполнено за отведённое число попыток.")
                # Переходим к следующей итерации внешнего цикла
                continue

            logger.info(f"Ожидаем смены IP (текущий: {current_ip})...")
            # Ограничение ожидания смены IP
            ip_wait_attempts = 0
            max_ip_wait_attempts = 10  # например, 10 циклов по 30 секунд
            while get_my_ip() == current_ip and ip_wait_attempts < max_ip_wait_attempts:
                time.sleep(30)
                ip_wait_attempts += 1

            if ip_wait_attempts >= max_ip_wait_attempts:
                logger.warning("IP не изменился за отведённое время, переключаемся на новый proxy.")
                # Если смена IP не произошла, можно перейти к следующей итерации, чтобы попробовать сменить proxy
                continue

        except RuntimeError:
            logger.error("Произошла ошибка во время голосования.")
            time.sleep(15)
            continue

    return "Голосование завершено"


if __name__ == '__main__':
    main('26124', '5', 35)
