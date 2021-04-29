import robin_stocks.robinhood as rs
import os

robin_user = os.environ.get("RH_USR")
robin_pass = os.environ.get("RH_PWD")


def rh_login():
    rs.login(username=robin_user,
             password=robin_pass,
             expiresIn=86400,
             by_sms=True)


def rh_execute_trade(ticker):
    # This example for buying a little bit of litecoin ('LTC') actually worked!
    rs.orders.order_buy_crypto_by_price(ticker,
                                        5,
                                        timeInForce='gtc')


def get_crypto_price(ticker):
    return rs.crypto.get_crypto_quote(ticker).get('mark_price')
