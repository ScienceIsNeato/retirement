import robin_stocks.robinhood as rs
import os

robin_user = os.environ.get("RH_USR")
robin_pass = os.environ.get("RH_PWD")


def rh_login():
    print("Logging in to RobinHood...")
    rs.login(username=robin_user,
             password=robin_pass,
             expiresIn=86400,
             by_sms=True)
    print("Login Successful")


def rh_execute_trade(ticker):
    # This example for buying a little bit of litecoin ('LTC') actually worked!
    rs.orders.order_buy_crypto_by_price(ticker,
                                        5,
                                        timeInForce='gtc')


def get_crypto_price(ticker):
    return rs.crypto.get_crypto_quote(ticker).get('mark_price')


def get_crypto_history(ticker, interval='15second', span='hour'):

    # interval: The time between data points.
    #       Can be '15second', '5minute', '10minute', 'hour', 'day', or 'week'. Default is 'hour'.
    # span: The entire time frame to collect data points.
    #       Can be 'hour', 'day', 'week', 'month', '3month', 'year', or '5year'. Default is 'week'
    # param info: Will filter the results to have a list of the values that correspond to key that matches info.

    print("Getting historical data for Symbol: ", ticker, " , interval: ", interval, " , span: ", span)
    history = rs.crypto.get_crypto_historicals(ticker, interval=interval, span=span)

    # We don't need to return all that extra info. Just return a list of tuples of times and prices
    res = []
    for entry in history:
        price = entry.get('open_price')
        time_at_price = entry.get('begins_at')
        res.append({'price': price, 'time': time_at_price})
    print("History fetch completed successfully with ", len(res), " results.")
    return res
