import robin_stocks.robinhood as rs
from pyotp import TOTP as otp
from os.path import expanduser
import os

robin_user = os.environ.get("RH_USR")
robin_pass = os.environ.get("RH_PWD")


def rh_login():
    clear_pickles()
    print("Logging in to RobinHood...")

    # For this you'll need to set up MFA in robinhood
    totp = otp(os.environ.get('RH_TOKEN')).now()

    if totp is None:
        print('RH_TOKEN is missing from your env. Go set up MFA in robinhoods webpage,'
              'copy the token (by clicking \"can\'t scan\") and try again!')
        exit(0)

    rs.authentication.login(
        username=os.environ.get('RH_USR'),
        password=os.environ.get('RH_PWD'),
        mfa_code=totp
    )
    print("Login Successful")


def clear_pickles():
    print("Clearing any lingering pickels from previous logins...")
    home = expanduser("~")
    full_path = home + '/.tokens/robinhood.pickle'
    if os.path.exists(full_path):
        os.remove(full_path)


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
