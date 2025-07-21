import json
import logging
from functools import wraps

import aiohttp
from aiohttp.client_exceptions import (
    ClientConnectorDNSError,
    InvalidURL,
    ServerTimeoutError,
)

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
        raise ValueError("Request error: RAW_URI is None")
    if raw_uri in {"/", "/favicon.ico"}:
        logger.debug("Prefix is %s, request is not for exchange rate", raw_uri)
        raise NotFound("Request is not for exchange rate")


def get_currency_signs(scope: dict) -> str:
    """
    Извлекает символы валюты из uri
    """
    raw_uri = scope.get("path", "/")
    logger.debug("scope.path: %s", raw_uri)
    validate_raw_uri(raw_uri)
    signs = raw_uri.split("/")[1].lower()
    try:
        validate_signs(signs)
    except ValueError as exc:
        logger.error('Error: %s. Signs "%s" are not valid', exc, signs)
        raise exc
    logger.debug("Prefix is %s", signs)
    return signs


async def get_exchange_rate(
    currency_signs: str, session: aiohttp.ClientSession
) -> bytes:
    """
    Получает данные от стороннего api для указанных символов валют
    """
    logger.debug("URL for request: %s", API_URL.format(currency_signs))
    async with session.get(API_URL.format(currency_signs)) as response:
        logger.debug("Currency signs: %s", currency_signs)
        logger.debug("Status code: %s", response.status)
        if response.status == 404:
            logger.error(
                "Request error: %s. Currency signs: %s.",
                response.status,
                currency_signs,
            )
            raise ValueError("Currency signs are not valid")
        content = await response.read()
        return content


async def exception_response(
    send,
    status: int,
    headers: list[tuple[str, str]],
    message: str,
):
    """
    Формирует ответ при возникновении ошибки
    """
    error_dict = {"error": message}
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": headers,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": json.dumps(error_dict).encode(),
        }
    )


def exception_handler(headers):
    """
    Декоратор для обработки исключений возникших при выполнеии главной функции
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(scope, receive, send):
            try:
                return await func(scope, receive, send, headers)
            except ValueError as exc:
                return await exception_response(
                    send,
                    status=400,
                    headers=headers,
                    message=str(exc),
                )
            except (ClientConnectorDNSError, ServerTimeoutError, InvalidURL) as exc:
                logger.error("Error: %s", exc)
                return await exception_response(
                    send,
                    status=400,
                    headers=headers,
                    message="An error occurred while processing the request",
                )
            except NotFound as exc:
                return await exception_response(
                    send,
                    status=404,
                    headers=headers,
                    message=str(exc),
                )

        return wrapper

    return decorator


@exception_handler([("Content-Type", "application/json")])
async def app(scope, receive, send, headers):
    currency_signs = get_currency_signs(scope)
    async with aiohttp.ClientSession() as session:
        exchange_rate_data = await get_exchange_rate(currency_signs, session)
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": headers,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": exchange_rate_data,
        },
    )
