import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Опционный анализатор", layout="centered")
st.title("📊 Опционный анализатор (Analyze + IV/HV)")

st.markdown("Введите параметры опциона **вручную** или **загрузите CSV-файл** с колонками:\n"
            "`Ticker, Expiry, Type, Premium, Strike, IV, HV` (Type = Call/Put)")

uploaded_file = st.file_uploader("Загрузить CSV-файл", type="csv")

if not uploaded_file:
    st.subheader("Ввод вручную...")

    ticker = st.text_input("Тикер", value="AAPL")
    expiry = st.date_input("Срок действия опциона", min_value=datetime.date.today())
    option_type = st.selectbox("Тип опциона", ["Call", "Put"])
    premium_type = st.selectbox("Тип премии", ["Bid", "Ask", "Mark"], index=2)
    premium = st.number_input(f"Значение премии ({premium_type})", min_value=0.0, step=0.1)
    strike = st.number_input("Strike", min_value=0.01, step=0.5)
    iv = st.number_input("Implied Volatility (IV, %)", min_value=0.0, step=0.1)
    hv = st.number_input("Historical Volatility (HV, %)", min_value=0.0, step=0.1)

    df = pd.DataFrame([{
        "Ticker": ticker.upper(),
        "Expiry": expiry,
        "Type": option_type,
        "Premium": premium,
        "Strike": strike,
        "IV": iv,
        "HV": hv
    }])
else:
    try:
        df = pd.read_csv(uploaded_file)
        expected_cols = {"Ticker", "Expiry", "Type", "Premium", "Strike", "IV", "HV"}
        if not expected_cols.issubset(set(df.columns)):
            st.error(f"CSV должен содержать колонки: {', '.join(expected_cols)}")
            st.stop()
        df["Expiry"] = pd.to_datetime(df["Expiry"]).dt.date
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        st.stop()

# Расчёты
df["Grade"] = (df["Premium"] * 100) / df["Strike"]
mean_iv = df["IV"].mean()
df["Средняя IV"] = mean_iv

def analyze(row):
    if row["Type"] == "Put":
        if row["IV"] < row["HV"] and row["IV"] < row["Средняя IV"]:
            return "📉 Идеальный момент: Buy Put"
        elif row["Grade"] > 10 and row["IV"] > row["HV"]:
            return "✅ Sell Put (Analyze > 10 и высокая IV)"
        elif row["IV"] < row["HV"]:
            return "🟢 Buy Put (IV < HV)"
        elif row["Grade"] < 10:
            return "❌ Не продавать Put (Analyze < 10)"
        else:
            return "ℹ️ Нет чёткой рекомендации (Put)"
    else:  # Call
        if row["IV"] < row["HV"] and row["IV"] < row["Средняя IV"]:
            return "📈 Идеальный момент: Buy Call"
        elif row["Grade"] > 10 and row["IV"] > row["HV"]:
            return "✅ Sell Call (Analyze > 10 и высокая IV)"
        elif row["IV"] < row["HV"]:
            return "🟢 Buy Call (IV < HV)"
        elif row["Grade"] < 10:
            return "❌ Не продавать Call (Analyze < 10)"
        else:
            return "ℹ️ Нет чёткой рекомендации (Call)"

df["Рекомендация"] = df.apply(analyze, axis=1)

# Подсветка
def highlight(row):
    if "Идеальный момент" in row["Рекомендация"]:
        return ["background-color: #d4edda"] * len(row)  # зелёный
    elif "Sell" in row["Рекомендация"]:
        return ["background-color: #fff3cd"] * len(row)  # жёлтый
    elif "Не продавать" in row["Рекомендация"]:
        return ["background-color: #f8d7da"] * len(row)  # красный
    return [""] * len(row)

st.subheader("📈 Результаты анализа:")
st.dataframe(df.style.format({
    "Premium": "{:.2f}",
    "Strike": "{:.2f}",
    "IV": "{:.2f}",
    "HV": "{:.2f}",
    "Grade": "{:.2f}",
    "Средняя IV": "{:.2f}"
}).apply(highlight, axis=1), use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Скачать результат в CSV", data=csv, file_name="option_analysis.csv", mime="text/csv")

with st.expander("ℹ️ Как работает анализ?"):
    st.markdown("""
    - **Grade = Premium / Strike × 100**
    - **IV < HV** = волатильность недооценена, выгодно покупать
    - **IV > HV и Grade > 10** = высокая премия и волатильность — можно продать
    - Анализ работает отдельно для Call и Put
    """)
