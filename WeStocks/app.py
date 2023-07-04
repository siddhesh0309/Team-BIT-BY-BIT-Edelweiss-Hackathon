from flask import Flask, render_template, request, jsonify
import csv
from scipy.optimize import fsolve
from math import log, sqrt, exp
from scipy.stats import norm

app = Flask(__name__)

# Path to the CSV file
csv_file = 'C:/Users/Niraj Gandhi/real_time_data.csv'


def read_options_data(selected_underlying, selected_expiry):
    options_data = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            try:
                # Index 1 for 'trading_symbol', Index 2 for 'expiry_date'
                if (selected_underlying is None or row[1].startswith(selected_underlying)) and \
                   (selected_expiry is None or row[2] == selected_expiry):
                    options_data.append(row)
            except IndexError:
                # Skip rows with insufficient data (less than 3 elements in this case)
                pass
    return options_data[-20:]  # Return only the latest 20 rows


def calculate_change_in_oi(options_data):
    for row in options_data:
        open_interest = int(row[14])
        previous_open_interest = int(row[16])
        change_in_oi = open_interest - previous_open_interest
        row.append(str(change_in_oi))
    return options_data


def calculate_chng(options_data):
    for row in options_data:
        ltp = float(row[7])
        previous_closed = float(row[15])
        chng = ltp - previous_closed
        row.append(str(chng))
    return options_data


def get_underlyings():
    underlyings = set()
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            try:
                # Index 1 for 'trading_symbol'
                underlyings.add(row[1].split()[0])
            except IndexError:
                pass
    return sorted(underlyings)


# Function to calculate implied volatility
def implied_volatility(row):
    S = float(row[7])  # Last Traded Price (LTP)
    K = float(row[3])  # Strike Price
    T = 10 / 365      # Time to Maturity in years (assuming 10 days)
    r = 0.05         # Risk-Free Rate (assumed as 5%)
    option_type = row[4]

    # Black-Scholes formula for Call option
    def BlackScholesCall(sigma):
        d1 = (log(S / K) + (r + (sigma ** 2) / 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
        if option_type == 'CE':
            return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
        elif option_type == 'PE':
            return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("Invalid option type")

    # Solve for implied volatility using fsolve
    implied_volatility = fsolve(BlackScholesCall, 0.5)[0]
    return str(implied_volatility)


@app.route('/', methods=['GET', 'POST'])
def options_chain():
    if request.method == 'POST':
        selected_underlying = request.form['underlying']
        selected_expiry = request.form['expiry']
    else:
        selected_underlying = None
        selected_expiry = None

    options_data = read_options_data(selected_underlying, selected_expiry)
    options_data = calculate_change_in_oi(options_data)
    options_data = calculate_chng(options_data)
    underlyings = get_underlyings()

    # Calculate implied volatility for each row of options data
    for row in options_data:
        implied_vol = implied_volatility(row)
        row.append(implied_vol)

    return render_template('options_chain.html', options_data=options_data, underlyings=underlyings,
                           selected_underlying=selected_underlying, selected_expiry=selected_expiry)


@app.route('/api/latest_options_data')
def latest_options_data():
    selected_underlying = request.args.get('underlying')
    selected_expiry = request.args.get('expiry')
    options_data = read_options_data(selected_underlying, selected_expiry)
    options_data = calculate_change_in_oi(options_data)
    options_data = calculate_chng(options_data)

    # Calculate implied volatility for each row of options data
    for row in options_data:
        implied_vol = implied_volatility(row)
        row.append(implied_vol)

    return jsonify(options_data)


if __name__ == '__main__':
    app.run(debug=True)