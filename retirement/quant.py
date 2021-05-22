import time
import numpy as np
import datetime as dt


class QuantEngine:
    def __init__(self, allowance=100.00, is_mock=True):
        self.is_mock = is_mock
        self.funds_available = allowance
        self.min_samples = 60  # minimum number of samples required to initiate trade
        self.min_time_since_last_trade = 1  # measured in minutes
        self.time_of_last_trade = time.time()
        self.prices = []
        self.times = []
        self.data = {'x': [], 'y': [], 'x_p': [], 'y_p': []}
        self.shares_owned = 0
        self.invested = False

    def should_buy(self):
        # This needs to be overridden by child
        raise Exception("not implemented")

    def buy(self):
        if self.invested:
            print("ERROR: trying to buy when you already bought")
            return

        amount_to_buy_in_dollars = self.how_much_to_buy()
        self.update_funds_available(amount_to_buy_in_dollars*-1)
        shares = amount_to_buy_in_dollars/(self.prices[-1])
        self.update_shares_owned(shares)
        self.invested = True

        print("Buying ", shares, " shares at ", self.prices[-1], " for $", amount_to_buy_in_dollars)

    def sell(self):
        if not self.invested:
            print("ERROR: trying to sell when you ain't got none")
            return

        amount_to_sell_in_dollars = self.shares_owned * self.prices[-1]
        self.update_funds_available(amount_to_sell_in_dollars)
        shares_sold = self.shares_owned
        self.update_shares_owned(self.shares_owned*-1)
        self.invested = False

        print("Sold ", shares_sold, " shares at ", self.prices[-1], " for $", amount_to_sell_in_dollars)

    def should_sell(self):
        # This needs to be overridden by child
        raise Exception("not implemented")

    def can_trade(self):
        # First make sure we have enough samples to decide
        if len(self.prices) < self.min_samples:
            msg = "Not enough samples to trade - num samples: " + len(self.prices)
            return msg

        # Next make sure that enough time has passed since the last trade
        time_now = time.time()
        elapsed_time_min = (time_now - self.time_of_last_trade)/60.0
        if elapsed_time_min < self.min_time_since_last_trade:
            msg = "Not enough time since last trade - time elapsed: " + elapsed_time_min
            return msg

        return ""

    def how_much_to_buy(self):
        # Get amount to buy. Probably all available.
        return self.funds_available

    def how_much_to_sell(self):
        # Probably all available
        return self.funds_available

    def update_funds_available(self, diff):
        # Diff positive for deposits and negative for withdrawals
        self.funds_available += diff

    def update_shares_owned(self, num_shares):
        self.shares_owned += num_shares

    def update_model(self, price, time_of_price):
        raise Exception("not implemented")


class DerivBasedQuantEngine(QuantEngine):
    def __init__(self):
        super().__init__()
        self.buy_threshold = 0.01  # No idea if this is right or not
        self.sell_threshold = 0  # No idea if this is right or not

    def should_buy(self):
        if len(self.data['y_p']) < 1:
            return False

        if self.invested:
            return False  # already bought

        trade_err_msg = self.can_trade()

        if self.data['y_p'][-1] >= self.buy_threshold:
            if trade_err_msg != "":
                print("Want to buy, but can't because: ", trade_err_msg)
                return False
            else:
                return True

        return False

    def should_sell(self):
        if len(self.data['y_p']) < 1:
            return False

        if not self.invested:
            return False  # already sold

        trade_err_msg = self.can_trade()

        if self.data['y_p'][-1] <= self.sell_threshold:
            if trade_err_msg != "":
                print("Want to sell, but can't because: ", trade_err_msg)
                return False
            else:
                return True

        return False

    def update_model(self, price, time_of_price):
        if len(self.times) == 0:
            # First data entry. Set as time of first trade
            self.time_of_last_trade = time_of_price

        self.prices.append(price)
        self.times.append(time_of_price)

        if len(self.prices) >= self.min_samples:
            self.data = {
                'x': self.times,
                'y': self.prices
            }
            self.data['y_p'] = list(np.diff(self.data['y']) / np.diff(self.data['x']))
            self.data['x_p'] = list((np.array(self.data['x'])[:-1] + np.array(self.data['x'])[1:]) / 2)


class TimeBasedQuantEngine(QuantEngine):
    def markets_just_closed(self):
        return self.is_time_in_window(dt.time(16, 00),
                                      dt.time(16, 30),
                                      self.times[-1])

    def markets_just_opened(self):
        return self.is_time_in_window(dt.time(8, 00),
                                      dt.time(8, 30),
                                      self.times[-1])

    @staticmethod
    def is_time_in_window(start_time, end_time, now_time):
        now_time = time.strftime('%H:%M:%S', time.localtime(now_time))
        datetime_object = dt.time.fromisoformat(now_time)
        if start_time < end_time:
            return start_time <= datetime_object <= end_time
        else:
            # Over midnight:
            return now_time >= start_time or now_time <= end_time

    def should_buy(self):
        if len(self.data['y_p']) < 1:
            return False

        if self.invested:
            return False  # already bought

        trade_err_msg = self.can_trade()

        if self.markets_just_closed():
            if trade_err_msg != "":
                print("Want to buy, but can't because: ", trade_err_msg)
                return False
            else:
                return True

        return False

    def should_sell(self):
        if len(self.data['y_p']) < 1:
            return False

        if not self.invested:
            return False  # already sold

        trade_err_msg = self.can_trade()

        if self.markets_just_opened():
            if trade_err_msg != "":
                print("Want to sell, but can't because: ", trade_err_msg)
                return False
            else:
                return True

        return False

    def update_model(self, price, time_of_price):
        if len(self.times) == 0:
            # First data entry. Set as time of first trade
            self.time_of_last_trade = time_of_price

        self.prices.append(price)
        self.times.append(time_of_price)

        if len(self.prices) >= self.min_samples:
            self.data = {
                'x': self.times,
                'y': self.prices
            }
            self.data['y_p'] = list(np.diff(self.data['y']) / np.diff(self.data['x']))
            self.data['x_p'] = list((np.array(self.data['x'])[:-1] + np.array(self.data['x'])[1:]) / 2)
