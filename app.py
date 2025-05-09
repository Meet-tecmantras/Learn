import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# Streamlit page 
st.set_page_config(page_title="Stock Price Predictor", layout="wide")
st.title("📈 LSTM Stock Price Predictor")

# inputs
stock_symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., SUZLON.NS)", "SUZLON.NS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-04-03"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2025-04-04"))

if st.sidebar.button("Train and Predict"):

    # Fetch Stock Data
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)

    if stock_data.empty:
        st.error("No stock data found. Please check the symbol or dates.")
    else:
        st.subheader("📊 Historical Stock Data")
        st.line_chart(stock_data['Close'])

        #  Preprocessing
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(stock_data['Close'].values.reshape(-1, 1))

        X_train, y_train = [], []
        time_step = 60
        for i in range(time_step, len(scaled_data)):
            X_train.append(scaled_data[i - time_step:i, 0])
            y_train.append(scaled_data[i, 0])

        X_train, y_train = np.array(X_train), np.array(y_train)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        #  Build and Train LSTM Model
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        with st.spinner("Training model..."):
            model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)

        #  Predict
        test_data = scaled_data[-(time_step + 30):]
        X_test = []
        for i in range(time_step, len(test_data)):
            X_test.append(test_data[i - time_step:i, 0])
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

        predicted_prices = model.predict(X_test)
        predicted_prices = scaler.inverse_transform(predicted_prices)

        #  Plot
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(stock_data.index[-30:], stock_data['Close'].values[-30:], label="Actual", color="blue")
        ax.plot(stock_data.index[-30:], predicted_prices, label="Predicted", color="red")
        ax.set_title(f"{stock_symbol} Stock Price Prediction")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid()
        st.pyplot(fig)
    