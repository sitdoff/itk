# Запуск через gunicorn из корневой папки репозитория:
#     gunicorn srs.module_5.wsgi_exchange_rate:app --host 0.0.0.0 --port 8000

import json
import logging
from functools import wraps

import requests
from requests.exceptions import ConnectionError, HTTPError, InvalidURL, Timeout

API_URL = "https://api.exchangerate-api.com/v4/latest/{}"

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("WSGI")


class NotFound(Exception):
    pass


def validate_signs(signs: str) -> None:
    """
    Проверяет что символы валюты соответствуют требуемым параметрам
    """
    if not signs.isalpha():
        raise ValueError("Currency signs should be only letters")
    if len(signs) < 3:
        raise ValueError("Signs should be at least 3 letters")


def validate_raw_uri(raw_uri: str | None) -> None:
    if raw_uri is None:
        logger.error("Request error: RAW_URI is None")
        raise ValueError("Request error: RAW_URI is None")
    if raw_uri in {"/", "/favicon.ico"}:
        logger.debug("Path %s is not for exchange rate", raw_uri)
        raise NotFound("Request is not for exchange rate")


def get_currency_signs(environ: dict) -> str:
    """
    Извлекает символы валюты из uri
    """
    raw_uri = environ.get("RAW_URI", "/")
    logger.debug("environ.RAW_URI: %s", raw_uri)
    validate_raw_uri(raw_uri)
    signs = raw_uri.split("/")[1].lower()
    validate_signs(signs)
    logger.debug("Prefix is %s", signs)
    return signs


def get_exchange_rate(currency_signs: str) -> bytes:
    """
    Получает данные от стороннего api для указанных символов валют
    """
    logger.debug("URL for request: %s", API_URL.format(currency_signs))
    with requests.get(API_URL.format(currency_signs)) as response:
        logger.debug("Currency signs: %s", currency_signs)
        logger.debug("Status code: %s", response.status_code)
        if response.status_code == 404:
            logger.error("Request error: %s", response.status_code)
            raise ValueError("Currency signs are not valid")
        return response.content


def exception_response(
    start_response,
    status: str,
    headers: list[tuple[str, str]],
    message: str,
):
    """
    Формирует ответ при возникновении ошибки
    """
    start_response(status=status, headers=headers)
    error_dict = {"error": message}
    return [json.dumps(error_dict).encode("utf-8")]


def exception_handler(headers):
    """
    Декоратор для обработки исключений возникших при выполнеии главной функции
    """

    def decorator(func):
        @wraps(func)
        def wrapper(environ, start_response):
            try:
                return func(environ, start_response, headers)
            except ValueError as exc:
                return exception_response(
                    start_response,
                    status="400 BAD REQUEST",
                    headers=headers,
                    message=str(exc),
                )
            except (ConnectionError, HTTPError, InvalidURL, Timeout) as exc:
                logger.error("Error: %s", exc)
                return exception_response(
                    start_response,
                    status="400 BAD REQUEST",
                    headers=headers,
                    message="An error occurred while processing the request",
                )
            except NotFound as exc:
                return exception_response(
                    start_response,
                    status="404 NOT FOUND",
                    headers=headers,
                    message=str(exc),
                )

        return wrapper

    return decorator


@exception_handler(headers=[("Content-Type", "application/json")])
def app(environ, start_response, headers=None):
    currency_signs = get_currency_signs(environ)
    exchange_rate_data = get_exchange_rate(currency_signs)
    start_response(status="200 OK", headers=headers)
    return [exchange_rate_data]
