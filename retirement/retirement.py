import rh_wrapper as rh
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
        self.UPDATE_INTERVAL = .5
        self.FIG_INITIALIZED = False
        self.data = {'x': [], 'y': [], 'x_p': [], 'y_p': []}
        self.ani = None
        self.ax1 = None
        self.fig = plt.figure(figsize=(13, 9))
        self.button = None

    def initialize_plot(self):
        if self.FIG_INITIALIZED:
            return

        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()

        # Create and label top graph (stock price)
        plt.subplot(211)
        plt.ylabel('Share Price')
        plt.title('Etherium Share Price Over Time: {}'.format(''))

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

    def get_data(self, ticker):
        # Get the stock price
        current_price = float(rh.get_crypto_price(ticker))

        # print the stock value
        print("Current price: ", current_price)
        print("Current time: ", time.time())

        self.prices.append(current_price)
        self.times.append(time.time())
        if len(self.prices) > self.MAX_SAMPLES:
            self.prices.pop(0)
            self.times.pop(0)

        if len(self.prices) >= self.MAX_SAMPLES:
            self.data = {
                'x': self.times,
                'y': self.prices
            }
            self.data['y_p'] = list(np.diff(self.data['y']) / np.diff(self.data['x']))
            self.data['x_p'] = list((np.array(self.data['x'])[:-1] + np.array(self.data['x'])[1:]) / 2)

    @staticmethod
    def stop_pressed(mouse_event):
        print("Exiting")
        sys.exit(0)

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


def main():
    # Login
    rh.rh_login()

    manager = Manager()
    share_plot = []
    deriv_plot = []

    ticker = 'ETH'  # Etherium
    prev_data = rh.get_crypto_history(ticker, interval='5minute', span='day')

    manager.set_data(prev_data)

    while True:
        manager.get_data(ticker)

        share_plot = manager.live_plotter(manager.data['x'], manager.data['y'], share_plot, 'price')
        deriv_plot = manager.live_plotter(manager.data['x_p'], manager.data['y_p'], deriv_plot, 'deriv')

        time.sleep(manager.UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
