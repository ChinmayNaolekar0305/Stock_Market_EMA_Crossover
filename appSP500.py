import pandas as pd
import numpy as np
import yfinance as yf
import talib as ta
import os
from flask import Flask, render_template, send_file, request, redirect, url_for, jsonify
from datetime import datetime, timedelta

# Set up Flask app
app = Flask(__name__)

monitoring_file = 'monitoring_stocks.csv'



tickers = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()



end_date = '2024-10-05'
start_date = '2022-08-23'

price_data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker')

# Save each stock's data to its own CSV file
for symbol in tickers:
    if symbol in price_data.columns.levels[0]:  # Ensure data exists for the stock
        stock_data = price_data[symbol]  # Extract data for this stock
        stock_data.to_csv(f'static/{symbol}_prices.csv')  # Save to CSV


def calculate_indicators(data):
    
    indicators = pd.DataFrame(index=data.index)
    
    close = data['Close']
    high = data['High']
    low = data['Low']
    
    # Calculate EMA
    indicators['EMA_5'] = ta.EMA(close, timeperiod=5)
    indicators['EMA_13'] = ta.EMA(close, timeperiod=13)
    indicators['EMA_26'] = ta.EMA(close, timeperiod=26)
    
    # Calculate MACD with specified parameters
    macd, macdsignal, macdhist = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    indicators['MACD'] = macd
    indicators['MACD_Signal'] = macdsignal
    indicators['MACD_Hist'] = macdhist
    
    # Calculate RSI with specified parameters
    indicators['RSI'] = ta.RSI(close, timeperiod=14)
    
    # Calculate Stochastic Oscillator with specified parameters
    slowk, slowd = ta.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
    indicators['Stoch_K'] = slowk
    indicators['Stoch_D'] = slowd
    
    
    return indicators

def filter_stocks(price_data):
    filtered_stocks = []
    stock_details = []

    for symbol in price_data.columns.levels[0]:
        stock_data = price_data.loc[:, symbol]  # Extract data for this stock as a DataFrame

        # print(f"Processing {symbol}")
        # print("Stock data columns:", stock_data.columns)  # Check columns are as expected
        # print(stock_data.head())  # Check first few rows

        if stock_data.empty:
            continue  

        indicators = calculate_indicators(stock_data)


        ema_crossover_recent = False


        
        for i in range(1, 5):
            recent_data = indicators.iloc[-i]
            previous_data = indicators.iloc[-i-1]

            ema_crossover_today = (recent_data['EMA_5'] > recent_data['EMA_13']) and (recent_data['EMA_5'] > recent_data['EMA_26'])
            ema_crossover_yesterday = (previous_data['EMA_5'] <= previous_data['EMA_13']) or (previous_data['EMA_5'] <= previous_data['EMA_26'])

            if ema_crossover_today and ema_crossover_yesterday:
                ema_crossover_recent = True
                break

        if ema_crossover_recent:
            recent_data = indicators.iloc[-1]

            # Check other conditions
            macd_condition = (recent_data['MACD'] > recent_data['MACD_Signal']) and (recent_data['MACD'] > 0)
            rsi_condition = 40 <= recent_data['RSI'] <= 60
            stoch_crossover = (recent_data['Stoch_K'] > recent_data['Stoch_D'])
            # adx_condition = recent_data['ADX'] >= 15

            stoch_crossover_last_5_days = False
            for i in range(1, 6):
                if indicators['Stoch_K'].iloc[-i] > indicators['Stoch_D'].iloc[-i]:
                    stoch_crossover_last_5_days = True
                    break

            if macd_condition and rsi_condition and stoch_crossover:
                filtered_stocks.append(symbol)
                stock_details.append({
                    'Stock': symbol,
                    'EMA_Crossover': ema_crossover_recent,
                    'MACD_Condition': macd_condition,
                    'RSI_Condition': rsi_condition,
                    'Stoch_Crossover': stoch_crossover,
                    # 'ADX_Condition': adx_condition,
                    'Stoch_Crossover_Last_5_Days': 'Yes' if stoch_crossover_last_5_days else 'No'
                })

    stock_details_df = pd.DataFrame(stock_details)
    return filtered_stocks, stock_details_df


# Save each stock's data to its own CSV file
for symbol in price_data.columns.levels[0]:
    stock_data = price_data.loc[:, symbol]  # Ensure we extract data as a DataFrame
    indicators = calculate_indicators(stock_data)
    
    if indicators is not None:
        indicators.tail(10).to_csv(f'static/indicators_{symbol}.csv')


summary_data = {
    'Stock': [],
    'Closing Price': [],
    'Indicators File': []
}

for symbol in price_data.columns.levels[0]:
    stock_data = price_data.loc[:, symbol]
    summary_data['Stock'].append(symbol)
    summary_data['Closing Price'].append(stock_data['Close'].iloc[-1])
    summary_data['Indicators File'].append(f'indicators_{symbol}.csv')

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('static/summary_indicators.csv', index=False)


def identify_stochastic_crossovers(data):
    crossovers = []
    for i in range(1, len(data)):
        if data['Stoch_K'].iloc[i] > data['Stoch_D'].iloc[i] and data['Stoch_K'].iloc[i-1] <= data['Stoch_D'].iloc[i-1] and data['Stoch_K'].iloc[i] < 20:
            crossovers.append(data.index[i])
    return crossovers

def track_ema_crossovers(data, crossovers, days=20):
    ema_crossovers = []
    for crossover in crossovers:
        start_index = data.index.get_loc(crossover)
        for i in range(1, days + 1):
            if start_index + i >= len(data):
                break
            recent_data = data.iloc[start_index + i]
            previous_data = data.iloc[start_index + i - 1]
            if ((recent_data['EMA_5'] > recent_data['EMA_13']) and (recent_data['EMA_5'] > recent_data['EMA_26']) and 
                previous_data['EMA_5'] < previous_data['EMA_13']) or (previous_data['EMA_5'] < previous_data['EMA_26']):
                ema_crossovers.append(data.index[start_index + i])
                break
    return ema_crossovers

def track_price_changes(data, points, threshold=0.03):
    successful_points = []
    for point in points:
        start_index = data.index.get_loc(point)
        for i in range(1, 25):
            if start_index + i >= len(data):
                break
            price_change = (data['Close'].iloc[start_index + i] - data['Close'].iloc[start_index]) / data['Close'].iloc[start_index]
            if price_change >= threshold:
                successful_points.append(point)
                break
    return successful_points

def backtest_stochastic_crossovers(filtered_stocks):
    backtest_results = []
    six_months_ago = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=545)
    six_months_ago = pd.Timestamp(six_months_ago)

    for symbol in filtered_stocks:
        data = price_data[symbol]
        indicators = calculate_indicators(data)
        
        # Ensure the index is a DatetimeIndex
        if not isinstance(indicators.index, pd.DatetimeIndex):
            indicators.index = pd.to_datetime(indicators.index)

        # Check if the date exists in the index
        if six_months_ago not in indicators.index:
            continue

        crossovers = identify_stochastic_crossovers(indicators.loc[six_months_ago:])
        ema_crossovers = track_ema_crossovers(indicators.loc[six_months_ago:], crossovers)
        successful_points = track_price_changes(data.loc[six_months_ago:], ema_crossovers)
        
        total_crossovers = len(ema_crossovers)
        successful_crossovers = len(successful_points)
        success_rate = (successful_crossovers / total_crossovers) * 100 if total_crossovers > 0 else 0
        stochastic_crossovers = identify_stochastic_crossovers(indicators)
        
        backtest_results.append({
            'Stock': symbol,
            'Total_Crossovers': total_crossovers,
            'Successful_Crossovers': successful_crossovers,
            'Success_Rate': success_rate,
            'Stochastic_Crossover Dates': stochastic_crossovers,
            'Succesfull Stochastic_Crossover Dates': successful_points
        })
    
    backtest_df = pd.DataFrame(backtest_results)
    return backtest_df


def get_all_crossover_dates(price_data):
    all_crossover_dates = {}
    for symbol, data in price_data.items():
        if data.empty:
            continue

        indicators = calculate_indicators(data)
        stochastic_crossovers = identify_stochastic_crossovers(indicators)
        ema_crossover_dates = track_ema_crossovers(indicators, stochastic_crossovers)
        all_crossover_dates[symbol] = ema_crossover_dates
    return all_crossover_dates

def ensure_monitoring_file():
    if not os.path.exists(monitoring_file):
        with open(monitoring_file, 'w') as f:
            f.write('Stock\n')



@app.route('/')
def index():
    summary_df = pd.read_csv('static/summary_indicators.csv')
    filtered_stocks, stock_details_df = filter_stocks(price_data)
    print(filtered_stocks)

    if 'Stock' not in summary_df.columns:
        return "Error: 'Stock' column missing in summary_df"
    if 'Stock' not in stock_details_df.columns:
        return "Error: 'Stock' column missing in stock_details_df"

    filtered_summary_df = summary_df[summary_df['Stock'].isin(filtered_stocks)]
    print(filtered_summary_df)
    final_df = filtered_summary_df.merge(stock_details_df, on='Stock', how='left')
    print(final_df)

    backtest_df = backtest_stochastic_crossovers(filtered_stocks)
    final_df = final_df.merge(backtest_df, on='Stock', how='left')

    final_df['Monitor'] = final_df.apply(
    lambda row: f'<input type="checkbox" name="selected_stocks" value="{row["Stock"]}" data-stock="{row["Stock"]}">',
    axis=1)

    final_df = final_df[['Monitor', 'Stock', 'Closing Price', 'Indicators File', 'EMA_Crossover', 'MACD_Condition', 'RSI_Condition', 'Stoch_Crossover', 'Stoch_Crossover_Last_5_Days', 'Total_Crossovers', 'Successful_Crossovers', 'Success_Rate', 'Stochastic_Crossover Dates', 'Succesfull Stochastic_Crossover Dates']]

    try:
        monitored_stocks = pd.read_csv(monitoring_file)['Stock'].tolist()
    except FileNotFoundError:
        monitored_stocks = []

    return render_template('index.html', tables=[final_df.to_html(classes='data', header="true", index=False, escape=False)])

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join('static', filename)
    return send_file(path, as_attachment=True)

@app.route('/indicators/<stock>')
def view_indicators(stock):
    filepath = f'static/indicators_{stock}.csv'
    if os.path.exists(filepath):
        indicators_df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
        return render_template('indicators.html', stock=stock, tables=[indicators_df.to_html(classes='data', header="true")])
    else:
        return "File not found", 404
    
@app.route('/monitor', methods=['POST'])
def select_stocks():
    selected_stocks = request.form.getlist('selected_stocks')
    if selected_stocks:
        today = pd.to_datetime(end_date).date() - pd.Timedelta(days=1)

        # Load existing monitoring list
        if os.path.exists(monitoring_file):
            monitoring_df = pd.read_csv(monitoring_file)
        else:
            monitoring_df = pd.DataFrame(columns=['Stock', 'Date Added', 'Closing Price'])

        new_entries = []

        for stock in selected_stocks:
            closing_price = price_data[stock]['Close'].iloc[-1]

            # Check if the stock has already been added for the current date
            if not ((monitoring_df['Stock'] == stock) & (monitoring_df['Date Added'] == str(today))).any():
                new_entries.append({
                    'Stock': stock,
                    'Date Added': today,
                    'Closing Price': closing_price
                })

        # Add new entries to the monitoring DataFrame
        if new_entries:
            new_entries_df = pd.DataFrame(new_entries)
            monitoring_df = pd.concat([monitoring_df, new_entries_df], ignore_index=True)

        # Save the updated monitoring list
        monitoring_df.to_csv(monitoring_file, index=False)

    return redirect(url_for('index'))

@app.route('/save_breakout', methods=['POST'])
def save_breakout():
    data = request.get_json()
    print(data)
    stock = data['stock']
    breakout_amount = data['breakout_amount']
    date_added = end_date

    # Load existing data or create a new DataFrame if the file doesn't exist
    file_path = 'static/breakout_data1.csv'
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=['Stock', 'Breakout Amount', 'Date Added'])
    else:
        df = pd.read_csv(file_path)

    # Create a new DataFrame for the new data
    new_data = pd.DataFrame([{
        'Stock': stock,
        'Breakout Amount': breakout_amount,
        'Date Added': date_added
    }])

    # Append the new data to the existing DataFrame
    df = pd.concat([df, new_data], ignore_index=True)

    # Save the updated DataFrame to the CSV file
    df.to_csv(file_path, index=False)

    return jsonify({'status': 'success'})



if __name__ == '__main__':
    app.run(debug=True)
