import rh_wrapper as rh
import time
import numpy as np
import matplotlib.pyplot as plt
import sys
from matplotlib import style
from matplotlib.widgets import Button


class Manager:
    def __init__(self):
        style.use('fivethirtyeight')
        # Create a queue to store stock prices
        self.prices = []
        self.times = []

        self.MAX_SAMPLES = 5
        self.UPDATE_INTERVAL = .5
        self.FIRST_TIME = True
        self.data = {'x': [], 'y': [], 'x_p': [], 'y_p': []}
        self.ani = None
        self.ax1 = None
        self.fig = plt.figure(figsize=(13, 6))
        self.button = None

    def get_data(self):
        # Get the stock price
        current_price = float(rh.get_crypto_price('LTC'))

        # print the stock value
        print("Current price: ", current_price)

        self.prices.append(current_price)
        self.times.append(time.time())
        if len(self.prices) > self.MAX_SAMPLES:
            self.prices.pop(0)
            self.times.pop(0)
            print("popping it")

        if len(self.prices) >= self.MAX_SAMPLES:
            self.data = {
                'x': self.times,
                'y': self.prices
            }
            self.data['y_p'] = list((1000 * (np.diff(self.data['y']) / np.diff(self.data['x']))))
            self.data['x_p'] = list((np.array(self.data['x'])[:-1] + np.array(self.data['x'])[1:]) / 2)

    @staticmethod
    def stop_pressed(mouse_event):
        print("Exiting")
        sys.exit(0)

    def live_plotter(self, x_vec, y1_data, line1, subplot, identifier='', pause_time=0.1):
        if x_vec != [] and len(x_vec) >= self.MAX_SAMPLES - 1:
            if not line1:
                # this is the call to matplotlib that allows dynamic plotting
                plt.ion()

                ax = self.fig.add_subplot(subplot)
                # create a variable for the line so we can later update it
                line1, = ax.plot(x_vec, y1_data, '-o', alpha=0.8)
                # update plot label/title
                plt.ylabel('Share Price')
                plt.title('Etherium Share Price Over Time: {}'.format(identifier))

                # Put a stop button in place
                button_pos = plt.axes([0.81, 0.05, 0.1, 0.075])
                self.button = Button(button_pos, 'Stop')
                self.button.on_clicked(self.stop_pressed)

                plt.show()

            # after the figure, axis, and line are created, we only need to update the y-data
            line1.set_ydata(y1_data)
            # adjust limits if new data goes beyond bounds
            if np.min(y1_data) <= line1.axes.get_ylim()[0] or np.max(y1_data) >= line1.axes.get_ylim()[1]:
                plt.ylim([np.min(y1_data) - np.std(y1_data), np.max(y1_data) + np.std(y1_data)])
            # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
            plt.pause(pause_time)

        # return line so we can update it again in the next iteration
        return line1


def main():
    # Login
    rh.rh_login()

    manager = Manager()
    share_plot = []
    deriv_plot = []

    while True:
        manager.get_data()

        share_plot = manager.live_plotter(manager.data['x'], manager.data['y'], share_plot, 311)
        deriv_plot = manager.live_plotter(manager.data['x_p'], manager.data['y_p'], deriv_plot, 313)

        time.sleep(manager.UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
