import streamlit as st
import requests
from datetime import datetime


@st.cache_data
def get_nbu_rate(date_str, currency_code="USD"):
    url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={currency_code}&date={date_str}&json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]['rate']
    except Exception as e:
        st.error(f"Помилка API: {e}")
    return None


def calculate_all(income_usd, nbu_rate):
    income_uah = income_usd * nbu_rate
    ep_uah = income_uah * 0.05
    vz_uah = income_uah * 0.01
    esv_uah = 1902.34

    total_taxes_uah = ep_uah + vz_uah + esv_uah
    net_uah = income_uah - total_taxes_uah

    return {
        "UAH": {
            "total": income_uah, "ep": ep_uah, "vz": vz_uah,
            "esv": esv_uah, "taxes": total_taxes_uah, "net": net_uah
        },
        "USD": {
            "total": income_usd, "ep": ep_uah / nbu_rate, "vz": vz_uah / nbu_rate,
            "esv": esv_uah / nbu_rate, "taxes": total_taxes_uah / nbu_rate, "net": net_uah / nbu_rate
        }
    }


st.set_page_config(page_title="FOP Tax Calc", layout="wide")

st.title("💰 Податковий калькулятор + Звірка")

col_in1, col_in2 = st.columns(2)
with col_in1:
    amount = st.number_input("Фактично надійшло (USD):", min_value=0.0, value=800.30, step=10.0)
with col_in2:
    date_val = st.date_input("Дата курсу НБУ:", datetime.now())

st.header("2. Звірка з відпрацьованим часом")
col_next1, col_next2 = st.columns(2)
with col_next1:
    hours_worked = st.number_input("Кількість відпрацьованих годин:", min_value=0.0, value=200.0, step=1.0)
with col_next2:
    BONUS_USD = 35.0
    st.info(f"Сталий бонус: **${BONUS_USD}**")

st.divider()

if st.button("Розрахувати все", type="primary"):
    rate = get_nbu_rate(date_val.strftime("%Y%m%d"))

    if rate:
        data = calculate_all(amount, rate)

        st.info(f"Курс НБУ: **{rate:.4f} грн**")

        st.subheader("Розподіл доходу")
        h1, h2, h3 = st.columns([2, 1, 1])
        h1.write("**Показник**")
        h2.write("**Гривня (UAH)**")
        h3.write("**Долар (USD)**")


        def show_row(label, uah_val, usd_val, highlight=False, is_tax=False):
            c1, c2, c3 = st.columns([2, 1, 1])
            prefix = "-" if is_tax else ""
            if highlight:
                c1.write(f"### {label}")
                c2.write(f"### {prefix}{uah_val:,.2f} ₴")
                c3.write(f"### {prefix}${usd_val:,.2f}")
            else:
                c1.write(label)
                c2.write(f"{prefix}{uah_val:,.2f} ₴")
                c3.write(f"{prefix}${usd_val:,.2f}")


        show_row("Загальний дохід", data["UAH"]["total"], data["USD"]["total"])
        show_row("Єдиний податок (5%)", data["UAH"]["ep"], data["USD"]["ep"], is_tax=True)
        show_row("Військовий збір (1%)", data["UAH"]["vz"], data["USD"]["vz"], is_tax=True)
        show_row("ЄСВ (фіксовано)", data["UAH"]["esv"], data["USD"]["esv"], is_tax=True)

        st.markdown("---")
        show_row("Всього податків", data["UAH"]["taxes"], data["USD"]["taxes"], is_tax=True)
        st.markdown("---")

        show_row("ЧИСТИЙ ПРИБУТОК", data["UAH"]["net"], data["USD"]["net"], highlight=True)

        st.divider()
        st.subheader("Результат звірки")

        earned_usd = (hours_worked * 3.5) + BONUS_USD
        earned_uah = earned_usd * rate

        net_usd = data["USD"]["net"]
        net_uah = data["UAH"]["net"]

        diff_usd = net_usd - earned_usd
        diff_uah = net_uah - earned_uah

        st.write("**В доларах (USD):**")
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric(label="Зароблено (Години + Бонус)", value=f"${earned_usd:,.2f}")
        col_res2.metric(label="Чистий прибуток", value=f"${net_usd:,.2f}")
        col_res3.metric(label="Різниця", value=f"${diff_usd:,.2f}", delta=f"{diff_usd:,.2f} USD")

        st.write("**В гривнях (UAH):**")
        col_res4, col_res5, col_res6 = st.columns(3)
        col_res4.metric(label="Зароблено (Години + Бонус)", value=f"{earned_uah:,.2f} ₴")
        col_res5.metric(label="Чистий прибуток", value=f"{net_uah:,.2f} ₴")
        col_res6.metric(label="Різниця", value=f"{diff_uah:,.2f} ₴", delta=f"{diff_uah:,.2f} UAH")

        st.divider()
        st.subheader("Покриття податків для заробленої суми")

        required_gross_uah = (earned_uah + 1902.34) / 0.94
        required_gross_usd = required_gross_uah / rate

        tax_coverage_usd = required_gross_usd - earned_usd
        tax_coverage_uah = required_gross_uah - earned_uah

        st.write("**Скільки необхідно отримати (Gross), щоб після всіх податків на руках залишилась зароблена сума:**")

        col_req1, col_req2, col_req3 = st.columns(3)
        col_req1.metric(label="Бажана сума (Зароблено)", value=f"${earned_usd:,.2f}")
        col_req2.metric(label="Добавити на податки", value=f"${tax_coverage_usd:,.2f}")
        col_req3.metric(label="Необхідне надходження", value=f"${required_gross_usd:,.2f}")

        col_req4, col_req5, col_req6 = st.columns(3)
        col_req4.metric(label="Бажана сума (Зароблено)", value=f"{earned_uah:,.2f} ₴")
        col_req5.metric(label="Добавити на податки", value=f"{tax_coverage_uah:,.2f} ₴")
        col_req6.metric(label="Необхідне надходження", value=f"{required_gross_uah:,.2f} ₴")
