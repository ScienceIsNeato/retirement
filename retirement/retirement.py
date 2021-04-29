import rh_wrapper as rh
import time
import numpy as np
import matplotlib.pyplot as plt

# Login
rh.rh_login()

# Create a queue to store stock prices
prices = []
times = []

MAX_SAMPLES = 15

while True:
    # Get the stock price
    current_price = float(rh.get_crypto_price('LTC'))

    # print the stock value
    print("Current price: ", current_price)

    prices.append(current_price)
    times.append(time.time())
    if len(prices) > MAX_SAMPLES:
        prices.pop()
        times.pop()
        print("popping it")

    if len(prices) >= MAX_SAMPLES:
        data = {
            'x': times,
            'y': prices
        }
        data['y_p'] = 1000*(np.diff(data['y']) / np.diff(data['x']))
        data['x_p'] = (np.array(data['x'])[:-1] + np.array(data['x'])[1:]) / 2

        plt.figure(1)
        plt.plot(data['x'], data['y'], 'r')
        plt.plot(data['x_p'], data['y_p'], 'b')
        plt.show()

    time.sleep(1)
