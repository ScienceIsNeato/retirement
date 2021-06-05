import rh_wrapper as rh
import quant
import time
import numpy as np
import matplotlib.pyplot as plt
import sys
from matplotlib.widgets import Button
from datetime import datetime


class Manager:
    def __init__(self):
        # style.use('fivethirtyeight')
        # Create a queue to store stock prices
        self.prices = []
        self.times = []

        self.MAX_SAMPLES = 50
        self.UPDATE_INTERVAL = 1
        self.FIG_INITIALIZED = False
        self.data = {'x': [], 'y': [], 'x_p': [], 'y_p': []}
        self.ani = None
        self.ax1 = None
        self.button = None
        self.engines = []
        self.plotting = True
        self.continue_live = True  # Set to true for live graphs
        self.stop = False
        self.ticker = 'DOGE'

        if self.plotting:
            self.fig = plt.figure(figsize=(13, 9))

        # Add any quant engines you'd like to exercise here
        self.engines.append(quant.TimeBasedQuantEngine())
        self.engines.append(quant.BaselineQuantEngine())
        self.engines.append(quant.IthDerivBasedQuantEngine())
        self.engines.append(quant.IthDerivBasedQuantEngine(2))
        self.engines.append(quant.IthDerivBasedQuantEngine(3))
        self.engines.append(quant.IthDerivBasedQuantEngine(4))

    def initialize_plot(self):
        if self.FIG_INITIALIZED:
            return

        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()

        # Create and label top graph (stock price)
        plt.subplot(211)
        plt.ylabel('Share Price')
        plt.title(self.ticker+' Share Price Over Time: {}'.format(''))

        # Create and label bottom graph (rate of change)
        plt.subplot(212)
        plt.ylabel('Deriv Price')
        plt.title('Deriv Share Price Over Time: {}'.format(''))

        self.FIG_INITIALIZED = True

    def set_data(self, data):
        # Assume data passed in is a dict of tuples of price, time
        for entry in data:
            price = entry.get('price')
            time_at_price = entry.get('time')
            utc_time = datetime.strptime(time_at_price, "%Y-%m-%dT%H:%M:%SZ")
            epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
            self.prices.append(float(price))
            self.times.append(epoch_time)
            for engine in self.engines:
                engine.update_model(float(price), epoch_time)
                if engine.should_buy():
                    engine.buy()
                elif engine.should_sell():
                    engine.sell()

    def get_current_data(self, ticker):
        # Get the stock price
        current_price = float(rh.get_crypto_price(ticker))

        # print the stock value
        print("Current price: ", current_price)
        print("Current time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

        self.prices.append(current_price)
        self.times.append(time.time())
        for engine in self.engines:
            engine.update_model(current_price, time.time())

        if len(self.prices) > self.MAX_SAMPLES:
            self.prices.pop(0)
            self.times.pop(0)

        if len(self.prices) >= self.MAX_SAMPLES:
            self.data = {
                'x': self.times,
                'y': self.prices
            }
            self.data['y_p'] = list(np.diff(self.data['y'], 4))

            # Need to normalize derivative with respect to time units
            self.data['x_p'] = self.times[:-4]

    def stop_pressed(self, _):
        self.stop = True
        print("User stopped execution")

    @staticmethod
    def convert_times_to_human_readable(epoch_times):
        new_data = []
        i = 0
        for this_time in epoch_times:
            new_data.append(time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(this_time)))
        return new_data

    def live_plotter(self, x_data, y_data, this_plot, plot, pause_time=0.1):
        if x_data != [] and len(x_data) >= self.MAX_SAMPLES - 1:
            # Figure out which graph to update
            if plot == 'price':
                axis = plt.subplot(211)
            else:
                axis = plt.subplot(212)

            if not this_plot:
                if plot == 'price':
                    this_plot, = axis.plot(x_data, y_data, '-o', alpha=0.8)
                else:
                    this_plot, = axis.plot(x_data, y_data, '-o', alpha=0.8)

                return this_plot

            self.initialize_plot()

            # after the figure, axis, and line are created, we only need to update the y-data
            this_plot.set_ydata(y_data)

            # adjust limits if new data goes beyond bounds
            current_min = np.min(y_data)
            last_min = this_plot.axes.get_ylim()[0]
            current_max = np.max(y_data)
            last_max = this_plot.axes.get_ylim()[1]
            if current_min <= last_min or current_max >= last_max:
                axis.set_ylim([np.min(y_data) - np.std(y_data), np.max(y_data) + np.std(y_data)])

            # Put a stop button in place
            button_pos = plt.axes([0.81, 0.05, 0.1, 0.075])
            self.button = Button(button_pos, 'Stop')
            self.button.on_clicked(self.stop_pressed)

            # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
            plt.pause(pause_time)

        # return line so we can update it again in the next iteration
        return this_plot

    def close(self):
        for engine in self.engines:
            engine.close()

        if self.plotting:
            print("Clearing current plot...")
            plt.close()
            self.fig = plt.figure(figsize=(13, 9))
        else:
            exit(0)

        # First sort engines based on final performance
        self.engines.sort(key=lambda x: x.event_points[-1].price, reverse=True)

        for engine in self.engines:
            x_vals = []
            y_vals = []
            for event in engine.event_points:
                x_vals.append(event.time_of_event)
                y_vals.append(event.price)
            legend_val = engine.name
            # Append % difference to legend name
            percent_diff = "%.2f" % ((y_vals[-1]-y_vals[0])/y_vals[0]*100)
            legend_val = legend_val + " (" + percent_diff + ")"
            plt.plot(x_vals, y_vals, label=legend_val)

        # Normalize the stock for comparison
        normalized_prices = []
        initial_stock_val = self.prices[0]
        initial_value = self.engines[0].event_points[0].price

        for price in self.prices:
            normalized_prices.append(price*(initial_value/initial_stock_val))
        # Append % difference to legend name
        percent_diff = "%.2f" % ((self.prices[-1] - self.prices[0]) / self.prices[0] * 100)
        legend_val = "Normalized price for comp" + " (" + percent_diff + ")"
        plt.plot(self.times, normalized_prices, label=legend_val)
        plt.legend()
        plt.title('Quant Engines over time for '+self.ticker+': {}'.format(''))
        plt.show(block=True)


def main():
    # Login
    rh.rh_login()

    manager = Manager()
    share_plot = []
    deriv_plot = []

    prev_data = rh.get_crypto_history(manager.ticker, interval='hour', span='month')

    manager.set_data(prev_data)

    if not manager.continue_live:
        manager.close()
        exit(0)

    while not manager.stop:
        manager.get_current_data(manager.ticker)

        for engine in manager.engines:
            if engine.should_buy():
                engine.buy()
            elif engine.should_sell():
                engine.sell()

        if manager.plotting:
            share_plot = manager.live_plotter(manager.data['x'], manager.data['y'], share_plot, 'price')
            deriv_plot = manager.live_plotter(manager.data['x_p'], manager.data['y_p'], deriv_plot, 'deriv')

        time.sleep(manager.UPDATE_INTERVAL)

    manager.close()


if __name__ == "__main__":
    main()
