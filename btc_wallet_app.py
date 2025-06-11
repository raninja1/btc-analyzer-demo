import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import requests
from fpdf import FPDF
import os
from datetime import datetime

# Analyze BTC address
def analyze_btc_address(address):
    url = f"https://blockstream.info/api/address/{address}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            received = data['chain_stats']['funded_txo_sum'] / 1e8
            sent = data['chain_stats']['spent_txo_sum'] / 1e8
            balance = received - sent
            tx_count = data['chain_stats']['tx_count']
            return {
                "Wallet Address": address,
                "Total Received (BTC)": round(received, 8),
                "Total Sent (BTC)": round(sent, 8),
                "Final Balance (BTC)": round(balance, 8),
                "Total Transactions": tx_count
            }
        else:
            return None
    except Exception:
        return None

# Save analysis log
def save_wallet_log(data):
    log_file = "wallet_logs.csv"
    log_data = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **data
    }
    df = pd.DataFrame([log_data])
    if os.path.exists(log_file):
        df.to_csv(log_file, mode='a', header=False, index=False)
    else:
        df.to_csv(log_file, index=False)

# Display wallet data
def display_wallet_report(data):
    df = pd.DataFrame.from_dict(data, orient='index', columns=['Value'])
    st.dataframe(df, use_container_width=True)

# Pie chart
def plot_wallet_pie(data):
    labels = ['Final Balance', 'Total Sent']
    values = [data['Final Balance (BTC)'], data['Total Sent (BTC)']]
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    st.pyplot(fig)

# Risk score
def calculate_risk_score(data):
    tx_count = data['Total Transactions']
    balance = data['Final Balance (BTC)']
    score = 0
    if tx_count > 100:
        score += 30
    if balance < 0.01:
        score += 30
    if data['Total Received (BTC)'] > 50 and data['Total Sent (BTC)'] > 50:
        score += 40
    return min(score, 100)

def plot_risk_meter(score):
    fig, ax = plt.subplots(figsize=(3.5, 1))
    ax.barh(0, 100, height=10, color='lightgray')
    ax.barh(0, score, height=10,
            color='green' if score < 40 else 'orange' if score < 70 else 'red')
    ax.plot([score, score], [-1, 1], color='black', linewidth=2)
    ax.text(score, 2, f"{score}%", ha='center', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_ylim(-2, 3)
    ax.axis('off')
    st.pyplot(fig)

# Suspicious activity detection
def detect_suspicious_activity(data):
    messages = []
    if data['Total Transactions'] > 10000:
        messages.append("📈 הרבה טרנזקציות – ייתכן שזו פעילות שירותים או בוטים.")
    if data['Final Balance (BTC)'] < 0.001 and data['Total Received (BTC)'] > 10:
        messages.append("💸 יתרה נמוכה למרות קבלת סכומים גדולים – בדוק חשד להעברות החוצה.")
    if data['Total Sent (BTC)'] == 0 and data['Total Received (BTC)'] > 1:
        messages.append("🕵️ קבלת כספים בלי העברות – ייתכן כתובת אחסון או מנוחה.")
    if not messages:
        messages.append("✅ אין סימני פעילות חריגה.")
    return messages

# Export PDF
def export_wallet_pdf_clean(data, filename="btc_wallet_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.set_title("Bitcoin Wallet Report")
    pdf.cell(200, 10, txt="Bitcoin Wallet Report", ln=True, align='C')
    pdf.ln(10)
    for key, value in data.items():
        line = f"{key}: {value}"
        try:
            pdf.cell(200, 10, txt=line, ln=True, align='L')
        except:
            pdf.cell(200, 10, txt="[Line could not be printed]", ln=True, align='L')
    pdf.output(filename)
    return filename

# --- UI Design ---
st.set_page_config(page_title="BTC Wallet Analyzer", layout="centered", page_icon="💼")
st.markdown("""
    <style>
    .block-container {
        background-color: #0e1117;
        color: white;
        padding: 2rem;
        border-radius: 10px;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        transition: 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #145a86;
    }
    .stDataFrame, .stAlert, .element-container {
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🕵️ Bitcoin Wallet Analyzer")
st.caption("Track and analyze BTC wallet behavior visually.")

# Admin access modal style
with st.sidebar:
    with st.expander("👤 Login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if username == "ADMIN" and password == "ADMIN":
            st.session_state.show_admin = True

if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

# Show Admin Dashboard
if st.session_state.show_admin:
    st.markdown("---")
    st.subheader("🛠️ Admin Dashboard")
    try:
        logs = pd.read_csv("wallet_logs.csv")
        st.dataframe(logs, use_container_width=True)
        st.bar_chart(logs['Final Balance (BTC)'])
    except Exception:
        st.warning("No logs available yet.")
    st.stop()

# User Input
address = st.text_input("🔗 Enter BTC address:", value="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

if st.button("🔍 Analyze Wallet"):
    with st.spinner("Fetching wallet data..."):
        wallet = analyze_btc_address(address)
        if wallet:
            save_wallet_log(wallet)
            st.markdown("---")
            st.subheader("📋 Wallet Report")
            display_wallet_report(wallet)

            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Wallet Distribution")
                plot_wallet_pie(wallet)

            with col2:
                st.subheader("⚠️ Risk Score")
                score = calculate_risk_score(wallet)
                plot_risk_meter(score)

            with st.expander("🚨 Suspicious Activity Alerts", expanded=True):
                alerts = detect_suspicious_activity(wallet)
                for alert in alerts:
                    st.info(alert)

            with st.expander("🔓 View Full Report"):
                st.markdown("""
                    <div style='padding: 1em; background-color: #1c1c1c; border-radius: 8px;'>
                    <ul>
                        <li>🔸 Hourly activity patterns</li>
                        <li>🔸 Value distribution breakdown</li>
                        <li>🔸 Behavioral fingerprints</li>
                        <li>🧭 Moral Index – deviation from responsible norms</li>
                    </ul>
                    <a href="https://yourdomain.com/premium-report" target="_blank" style='color: #00c0ff;'>🔐 Get full premium report here</a>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📄 Export PDF")
            filename = export_wallet_pdf_clean(wallet)
            with open(filename, "rb") as file:
                st.download_button("📥 Download PDF", file, file_name=filename)
        else:
            st.error("❌ Error fetching wallet data. Please check the address.")
