"""
Communication with BitMEX REST API.
"""

import time
import hashlib
import hmac
import requests

from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, urljoin, urlencode
from json import dumps, loads
from datetime import datetime

from backend.exceptions import BitmexApiException


#
# Constants
#

API_ROOT = "/api/v1/"  # Root location of api calls
LIFE = 5  # Default request life in seconds
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


#
# Internal functions
#

def _generate_signature(secret, verb, url, json, expires):
    """
    Generate request signature compatible with BitMEX.

    secret:     api key secret
    verb:       method verb (POST, GET, ...)
    url:        full request url or only path
    expires:    request expiration in unix time
    json:       json string body of request

    Returns signature as string
    """
    # Parse the url so we can remove the base and extract just the path.
    parsedURL = urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query

    if isinstance(json, (bytes, bytearray)):
        json = json.decode('utf8')

    message = verb + path + str(expires) + json

    signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'),
                         digestmod=hashlib.sha256).hexdigest()
    return signature


def _generate_headers(life, key, secret, verb, url, json):
    """
    Generate request headers compatible with BitMEX.

    life:       how many seconds before request expires
    key:        api key id
    secret:     api key secret
    verb:       method verb (POST, GET, ...)
    url:        full request url or only path
    json:       json string body of request

    Returns headers as a dict
    """
    # Unix time + 5 seconds
    expires = int(time.time()) + 5
    headers = {
        "api-key": key,
        "api-expires": str(expires),
        "api-signature": _generate_signature(secret, verb, url, json, expires),
        "content-type": "application/json"
    }
    return headers


# Utility

def _datetime_to_str(dt):
    """
    Convert python datetime to datetime string.
    """
    return dt.strftime(TIME_FORMAT)


def _str_to_datetime(st):
    """
    Parse datetime string to python datetim.
    """
    return datetime.strptime(st, TIME_FORMAT)


def _json_sanitize(dict):
    """
    Prepare dict to be used in GET url query sent to BitMEX.

    Inplace.
    """
    for key in dict:
        value = dict[key]
        if isinstance(value, datetime):
            dict[key] = _datetime_to_str(value)
        elif not isinstance(value, str):
            dict[key] = dumps(value)


# Http

def _get(host: str, key: str, secret: str, path: str, life: int = LIFE, **params):
    """
    Send GET request to BitMEX server.

    host:   url of bitmex server (https:// has to be included)
    key:    api key id
    secret: api key secret
    path:   path to endpoint (i.e. /order/all)
    life:   how many seconds before request expires
    params: http query parameters

    Returns response json as dict.
    """
    verb = "GET"
    path = API_ROOT + path

    if life < 0:
        raise BitmexApiException("Request life of " + str(life) + " is negative")

    url = urljoin(host, path)
    if params:
        _json_sanitize(params)
        url = url + "?" + urlencode(params)
    headers = _generate_headers(life, key, secret, verb, url, "")
    response = requests.get(url, headers=headers)

    responseData = loads(response.text)
    if response.status_code == 200:  # Success
        return responseData
    else:                            # Error
        raise BitmexApiException("%d %s: %s" % (response.status_code,
                                                responseData["error"]["name"],
                                                responseData["error"]["message"]))


def _put_post_delete(host: str, key: str, secret: str, path: str, verb: str,
                     life: int = LIFE, **params):
    """
    Send PUT, POST or DELETE request to BitMEX server.

    host:   url of bitmex server (https:// has to be included)
    key:    api key id
    secret: api key secret
    path:   path to endpoint (i.e. /order/all)
    verb:   http operation verb
                GET
                PUT
                POST
                DELETE
    life:   how many seconds before request expires
    params: http query parameters

    Returns response json as dict.
    """
    path = API_ROOT + path

    if life < 0:
        raise BitmexApiException("Request life of " + str(life) + " is negative")

    url = urljoin(host, path)
    json = dumps(params)
    print(json)  # DEBUG
    headers = _generate_headers(life, key, secret, verb, url, json)
    if verb == "PUT":
        response = requests.put(url, headers=headers, data=json)
    elif verb == "POST":
        response = requests.post(url, headers=headers, data=json)
    elif verb == "DELETE":
        response = requests.delete(url, headers=headers, data=json)
    else:
        raise BitmexApiException("Internal Error: Unrecognized http operation: "
                                 + str(verb) + " (should be all uppercase).")

    responseData = loads(response.text)
    if response.status_code == 200:  # Success
        return responseData
    else:                            # Error
        raise BitmexApiException("%d %s: %s" % (response.status_code,
                                                responseData["error"]["name"],
                                                responseData["error"]["message"]))


#
# Api calls
#

# Instrument

def instrument_get(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    GET api call at /instrument

    Get instruments info.

    str host:               url of bitmex server (https:// has to be included)
    str key:                api key id
    str secret:             api key secret
    [int life]:             how many seconds before request expires

    params:
    [str symbol]:           filter by position symbol
    [dict filter]:          dict, only retrieve for orders with matching columns
    [list columns]:         truncate instruments info to only contain these columns
    [int count]:            limit how many instruments to retrieve
    [int start]:            skip this many instruments
    [bool reverse]:         if true, sort by newest first (default false)
    [datetime startTime]:   don't show instruments before this time
    [datetime endTime]:     don't show instruments after this time

    Returns instruments information dict list.
    """
    return _get(host, key, secret, "/instrument", life, **params)


# Order

def order_get(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    GET api call at /order.

    Get orders info.

    str host:               url of bitmex server (https:// has to be included)
    str key:                api key id
    str secret:             api key secret
    [int life]:             how many seconds before request expires

    params:
    [str symbol]:           filter by position symbol
    [dict filter]:          dict, only retrieve for orders with matching columns
    [list columns]:         truncate order info to only contain these columns
    [int count]:            limit how many orders to retrieve
    [int start]:            skip this many orders
    [bool reverse]:         if true, sort by newest first (default false)
    [datetime startTime]:   don't show orders before this time
    [datetime endTime]:     don't show orders after this time

    Returns positions information dict list.
    """
    return _get(host, key, secret, "/order", life, **params)


def order_put(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    PUT api call at /order

    Amend open order.

    str host:               url of bitmex server (https:// has to be included)
    str key:                api key id
    str secret:             api key secret
    [int life]:             how many seconds before request expires

    str orderID:            amend order with this id
    str origClOrdID:        clOrdID can be used instead of orderID
    [str clOrdID]:          new clOrdID
    [int orderQty]:         new number of contracts in order
    [int leavesQty]:        orderQty = leavesQty + already filled contracts
                            (used to set orderQty regardless of filled contracts)
    [float price]:          new limit price (only Limit orders valid)
    [float stopPx]:         new trigger price (only Stop and IfTouched orders valid)
    [float pegOffsetValue]: new trailing offset from the current price
                            (only Stop and IfTouched orders valid)
    [str text]:             new custom order annotation

    Returns amended order information dict.
    """
    return _put_post_delete(host, key, secret, "/order", "PUT", life, **params)


def order_post(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    POST api call at /order

    Create new order. Warning: price and stopPx only accept values rounded to
    instruments tick.

    str host:               url of bitmex server (https:// has to be included)
    str key:                api key id
    str secret:             api key secret
    [int life]:             how many seconds before request expires

    str symbol:             position symbol
    [str side]:             order side (defaults Buy unless orderQty negative)
                                Buy
                                Sell
    [int orderQty]:         how many contracts
    float price:            limit price (only Limit orders valid)
    [int displayQty]:       quantity to display in book
    float stopPx:           trigger price (only Stop and IfTouched orders valid)
    [str clOrdID]:          custom additional order id
    [float pegOffsetValue]: trailing offset from the current price
                            (only Stop and IfTouched orders valid)
    [str pegPriceType]:     peg price type (only Stop and IfTouched orders valid)
                                LastPeg
                                MidPricePeg
                                MarketPeg
                                PrimaryPeg
                                TrailingStopPeg
    [str ordType]:          order type
                                Market
                                Limit
                                Stop
                                StopLimit
                                MarketIfTouched
                                LimitIfTouched
    [str timeInForce]:      when does order expire
                                GoodTillCancel
                                ImmediateOrCancel
                                FillOrKill
    [str execInst]:         additional options (str separated by columns)
                                ParticipateDoNotInitiate
                                AllOrNone (displayQty must be 0)
                                MarkPrice (only Stop and IfTouched orders valid)
                                IndexPrice (only Stop and IfTouched orders valid)
                                LastPrice (only Stop and IfTouched orders valid)
                                Close
                                ReduceOnly
                                Fixed
    [str text]:             custom order annotation

    Returns created order information dict.
    """
    return _put_post_delete(host, key, secret, "/order", "POST", life, **params)


def order_delete(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    DELETE api call at /order

    Cancel order(s).

    str host:               url of bitmex server (https:// has to be included)
    str key:                api key id
    str secret:             api key secret
    [int life]:             how many seconds before request expires

    str orderID:            orders to be deleted (separated with columns)
    str origClOrdID:        clOrdIDs can be used instead of orderIDs
    [str text]:             cancellation custom annotation

    Returns canceled orders information list.
    """
    return _put_post_delete(host, key, secret, "/order", "DELETE", life, **params)


def order_all_delete(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    DELETE api call at /order/all

    Cancel all orders.

    str host:               url of bitmex server (https:// has to be included)
    str key:                api key id
    str secret:             api key secret
    [int life]:             how many seconds before request expires

    [str symbol]:           filter by position symbol
    [dict filter]:          dict, only retrieve for orders with matching columns
    [str text]:             cancellation custom annotation

    Returns canceled orders information list.
    """
    return _put_post_delete(host, key, secret, "/order/all", "DELETE", life, **params)


def order_cancel_all_after_post(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    POST api call at /order/cancelAllAfter

    Cancel ALL orders after specified timeout. If called repreatedly, timer
    will be reset to new timeout.

    str host:               url of bitmex server (https:// has to be included)
    str key:                api key id
    str secret:             api key secret
    [int life]:             how many seconds before request expires

    int timeout             timeout in milliseconds

    Returns empty dict.
    """
    return _put_post_delete(host, key, secret, "/cancelAllAfter", "POST", life, **params)


# Position

def position_get(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    GET api call at /position.

    Get positions info.

    str host:       url of bitmex server (https:// has to be included)
    str key:        api key id
    str secret:     api key secret
    [int life]:     how many seconds before request expires

    params:
    [dict filter]:  dict, only retrieve for positions with matching columns
    [list columns]: truncate position info to only contain these columns
    [int count]:    limit how many positions to retrieve

    Returns positions information dict list.
    """
    return _get(host, key, secret, "/position", life, **params)


def position_leverage_post(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    POST api call at /position/leverage.

    Set position leverage.

    str host:       url of bitmex server (https:// has to be included)
    str key:        api key id
    str secret:     api key secret
    [int life]:     how many seconds before request expires

    params:
    str symbol:     position symbol
    float leverage: leverage of 0-100 (0 for cross)

    Returns position information dict.
    """
    return _put_post_delete(host, key, secret, "/position/leverage", "POST", life, **params)


def position_risk_limit_post(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    POST api call at /position/riskLimit.

    Set position risk limit. Warning: This will set risk limit to next value
    available due to server-side implementation.

    str host:       url of bitmex server (https:// has to be included)
    str key:        api key id
    str secret:     api key secret
    [int life]:     how many seconds before request expires

    params:
    str symbol:     position symbol
    int riskLimit:  new risk limit (in satoshis)

    Returns position information dict.
    """
    return _put_post_delete(host, key, secret, "/position/riskLimit", "POST", life, **params)


def position_transfer_margin_post(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    POST api call at /position/transferMargin.

    Transfer equity in or out of a position. Warning: Doesn't work.

    str host:       url of bitmex server (https:// has to be included)
    str key:        api key id
    str secret:     api key secret
    [int life]:     how many seconds before request expires

    params:
    str symbol:     position symbol
    float amount:   amount to transfer (in satoshis) (may be negative)

    Returns position information dict.
    """
    return _put_post_delete(host, key, secret, "/order/transferMargin", "POST", life, **params)


# User

def user_margin_get(host: str, key: str, secret: str, life: int = LIFE, **params):
    """
    GET api call at /user/margin.

    Get accounts margin status. Send currency = "all" to receive list of all
    supported currencies.

    str host:       url of bitmex server (https:// has to be included)
    str key:        api key id
    str secret:     api key secret
    [int life]:     how many seconds before request expires

    params:
    str currency:   in which currency to list values

    Returns accounts margin status dict.
    """
    return _get(host, key, secret, "/user/margin", life, **params)
