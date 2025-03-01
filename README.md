# 📈 **Stock Market Monitoring & EMA Crossover Strategy**

## 📌 **Project Overview**

This project is a **Flask-based stock monitoring system** that fetches and analyzes **S&P 500 stock data** using `yfinance`, calculates **technical indicators**, and filters stocks based on a well-defined **Exponential Moving Average (EMA) crossover strategy**. It also allows users to monitor selected stocks, backtest crossover performance, and export results for further analysis.

## 🛠 **Tech Stack & Tools**

- **Python** (Pandas, NumPy, yFinance, TA-Lib, Flask)
- **Flask Web Framework** (for UI & API endpoints)
- **Technical Indicators** (EMA, MACD, RSI, Stochastic Oscillator)
- **Historical Data**: `yfinance` API to fetch market prices
- **Backtesting Module** (for past EMA crossovers and performance tracking)

## 📊 **Strategy Implemented**

### 🔹 **EMA Crossover Strategy**

- We use **three EMAs**:
  - **EMA-5** (Short-term trend)
  - **EMA-13** (Medium-term trend)
  - **EMA-26** (Long-term trend)
- A **bullish crossover** occurs when:
  - **EMA-5 crosses above both EMA-13 and EMA-26**
  - **Previous day EMA-5 was below either EMA-13 or EMA-26**
- The stock is further filtered using:
  - **MACD** (Momentum confirmation: MACD > MACD Signal & MACD > 0)
  - **RSI** (40-60 range for consolidation phase)
  - **Stochastic Oscillator** (Recent upward crossover for momentum)

### 📌 **Result: Identifies stocks showing strong bullish momentum**

Stocks passing the **EMA crossover + MACD + RSI + Stochastic** filter are likely poised for an **uptrend**, making them suitable for short-term momentum trades.

## 🚀 **How the Code Works**

### 📌 **Data Fetching**

- **Extracts S&P 500 tickers** from Wikipedia.
- **Uses **``** API** to fetch historical price data from `2022-08-23` to `2024-10-05`.
- Saves each stock's historical prices as a CSV file (`static/{symbol}_prices.csv`).

### 📌 **Technical Indicator Calculation**

- Implements **TA-Lib** to compute:
  - **Exponential Moving Averages (EMA-5, EMA-13, EMA-26)**
  - **MACD (12, 26, 9)**
  - **Relative Strength Index (RSI-14)**
  - **Stochastic Oscillator (14, 3, 3)**
- Saves **indicator values** for each stock as `static/indicators_{symbol}.csv`.

### 📌 **Stock Filtering**

- Iterates over **all stocks** in the dataset.
- Checks **EMA crossover conditions**.
- Confirms with **MACD, RSI, and Stochastic Oscillator**.
- Saves shortlisted stocks as ``.

### 📌 **Flask Application (Web UI & API)**

- **Homepage (**``**)**: Displays stocks passing the filter in a **web table**.
- **Indicators Page (**``**)**: Shows indicator values for each stock.
- **Download Endpoint (**``**)**: Allows CSV file downloads.
- **Monitoring Stocks (**``**)**: Enables users to select and track specific stocks.
- **Breakout Tracking (**``**)**: Stores user-input breakout levels.

## 📈 **Backtesting: Evaluating Past Crossovers**

### 🔹 **Historical Performance Evaluation**

- Identifies **past Stochastic crossovers** (oversold reversals).
- Tracks **subsequent EMA crossovers** (bullish confirmation).
- Monitors **price movement after crossovers** (success rate).
- **Success metric**: % of EMA crossovers that led to a **3%+ price increase within 25 days**.

### 🔹 **Future Enhancements: QuantConnect-Based Backtesting**

- We plan to **move backtesting to QuantConnect** for more rigorous evaluation.
- Future iterations will include:
  - **Multiple time-frame analysis (daily, weekly)**
  - **Incorporating volume analysis for trend confirmation**
  - **Live paper trading & execution tracking**

## 📊 **Results & Insights**

- **EMA crossover strategy** effectively highlights stocks in strong uptrends.
- **Backtesting validates** that high-probability setups yield better results.
- **Live monitoring** helps in tracking real-time breakouts & adding watchlist stocks.

## 🔮 **Future Roadmap**

- ✅ **Integrate Bollinger Bands for volatility analysis**
- ✅ **Improve position sizing & risk management modules**
- ✅ **Deploy on cloud for automated daily updates**
- 🚀 **Add trade execution API for semi-automated trading**

## 📥 **How to Run the Project**

### 🔹 **Installation**

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/stock-monitoring-system.git
   cd stock_analysis
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask app:
   ```bash
   python app.py
   ```

## 📜 **License**

This project is licensed under the **MIT License**.

## 📩 **Contact**

For any inquiries, feel free to reach out via GitHub or LinkedIn.

---

### ⭐ **If you find this project useful, don't forget to give it a star on GitHub!** ⭐

