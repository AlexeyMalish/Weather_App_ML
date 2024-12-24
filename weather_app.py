import streamlit as st
import pandas as pd
import aiohttp
import asyncio
import matplotlib.pyplot as plt
from datetime import datetime


async def get_current_temperature_async(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data['main']['temp']
            else:
                error_message = await response.json()
                return error_message


# Интерфейс WEB-приложения
st.title("Анализ исторических данных и текущей погоды")

# Загрузка файла с историческими данными и их валидация
uploaded_file = st.file_uploader("Загрузите файл с историческими данными (CSV)", type=["csv"])
if uploaded_file:
    historical_data = pd.read_csv(uploaded_file)
    st.write("Загруженные данные:", historical_data.head())

    if "city" in historical_data.columns and "temperature" in historical_data.columns and "timestamp" in historical_data.columns:
        historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'])
        st.success("Данные корректно загружены!")
    else:
        st.error("Файл должен содержать столбцы: city, temperature, timestamp.")

# Выбор города из списка
if uploaded_file:
    cities = historical_data['city'].unique()
    selected_city = st.selectbox("Выберите город", cities)

# Ввод API-ключа
api_key = st.text_input("Введите ваш API-ключ OpenWeatherMap")
if api_key:
    st.info("API-ключ введен, можно запросить текущую температуру.")
else:
    st.warning("Введите API-ключ для получения текущей погоды.")

# Получение и отображение текущей температуры для конкретного корода
if api_key and uploaded_file and selected_city:
    st.write("Получение текущей температуры для города:", selected_city)


    async def fetch_temperature():
        return await get_current_temperature_async(selected_city, api_key)


    current_temperature = asyncio.run(fetch_temperature())

    if isinstance(current_temperature, dict) and current_temperature.get("cod") == 401:
        st.error(f"Ошибка: {current_temperature['message']}")
    elif current_temperature:
        st.success(f"Текущая температура в {selected_city}: {current_temperature}°C")

        # Проверка на нормальность температуры для сезона
        seasonal_data = historical_data[historical_data['city'] == selected_city]
        seasonal_data['month'] = seasonal_data['timestamp'].dt.month
        current_month = datetime.now().month

        month_data = seasonal_data[seasonal_data['month'] == current_month]
        avg_temp = month_data['temperature'].mean()
        std_temp = month_data['temperature'].std()

        if avg_temp - 2 * std_temp <= current_temperature <= avg_temp + 2 * std_temp:
            st.info("Текущая температура нормальна для сезона.")
        else:
            st.warning("Текущая температура аномальна для сезона!")

# Описательную статистику по историческим данным для города в визуализации
if uploaded_file and selected_city:
    city_data = historical_data[historical_data['city'] == selected_city]
    st.subheader("Описательная статистика для города")
    st.write(city_data['temperature'].describe())

    # Временной ряд температур
    st.subheader("Временной ряд температур")
    plt.figure(figsize=(10, 6))
    plt.plot(city_data['timestamp'], city_data['temperature'], label="Температура")

    # Выделение аномалий
    mean_temp = city_data['temperature'].mean()
    std_temp = city_data['temperature'].std()
    anomalies = city_data[(city_data['temperature'] < mean_temp - 2 * std_temp) |
                          (city_data['temperature'] > mean_temp + 2 * std_temp)]

    plt.scatter(anomalies['timestamp'], anomalies['temperature'], color='red', label='Аномалии')
    plt.axhline(mean_temp, color='green', linestyle='--', label='Средняя температура')
    plt.legend()
    plt.xlabel("Дата")
    plt.ylabel("Температура")
    plt.title("Временной ряд температур с выделением аномалий")
    st.pyplot(plt)

    # Сезонные профили
    st.subheader("Сезонные профили")
    seasonal_profile = city_data.groupby(city_data['timestamp'].dt.month)['temperature'].agg(['mean', 'std'])
    seasonal_profile.reset_index(inplace=True)
    seasonal_profile.rename(columns={'timestamp': 'month'}, inplace=True)

    plt.figure(figsize=(10, 6))
    plt.errorbar(seasonal_profile['month'], seasonal_profile['mean'], yerr=seasonal_profile['std'], fmt='-o')
    plt.xlabel("Месяц")
    plt.ylabel("Температура")
    plt.title("Сезонные профили температуры")
    st.pyplot(plt)
