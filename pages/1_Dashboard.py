import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.graph_objects as go

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
FIRMA_NAZWA = st.secrets["FIRMA_NAZWA"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Spark - Dashboard", layout="wide")

# ====== OCHRONA HASŁEM (ADMIN) ======
if "zalogowany_admin" not in st.session_state:
    st.session_state.zalogowany_admin = False

if not st.session_state.zalogowany_admin:
    st.title("🔒 Dostęp ograniczony")
    haslo = st.text_input("Hasło administratora:", type="password")
    if st.button("Zaloguj"):
        if haslo == st.secrets["ADMIN_HASLO"]:
            st.session_state.zalogowany_admin = True
            st.rerun()
        else:
            st.error("Nieprawidłowe hasło")
    st.stop()

# ====== DESIGN TOKENS (TransVia — granat + pomarańcz) ======
BG = "#0B0F17"
SURFACE = "#131A26"
SURFACE_2 = "#1B2432"
ACCENT = "#E8792C"
ACCENT_2 = "#12294D"
TEXT = "#F5F6F8"
TEXT_MUTED = "#8A93A3"
BORDER = "#232C3B"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: {BG}; }}

    #MainMenu, header, footer {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem; max-width: 1200px; }}

    .spark-header {{
        display: flex; align-items: center; gap: 14px;
        margin-bottom: 8px;
    }}
    .spark-header .badge {{
        width: 44px; height: 44px; border-radius: 12px;
        background: {ACCENT};
        box-shadow: 0 0 24px rgba(232, 121, 44, 0.45);
        display: flex; align-items: center; justify-content: center;
        font-size: 22px; font-weight: 700; color: {ACCENT_2};
    }}
    .spark-header .title {{ font-size: 1.6rem; font-weight: 700; color: {TEXT}; letter-spacing: -0.5px; }}
    .spark-header .subtitle {{ font-size: 0.85rem; color: {TEXT_MUTED}; margin-top: -2px; }}

    .section-label {{
        font-size: 0.78rem; font-weight: 600; letter-spacing: 1.2px;
        color: {TEXT_MUTED}; text-transform: uppercase;
        margin: 2.2rem 0 0.8rem 0; padding-bottom: 0.5rem;
        border-bottom: 1px solid {BORDER};
    }}

    .kpi-row {{ display: flex; gap: 16px; margin-top: 0.5rem; }}
    .kpi-card {{
        flex: 1; background: {SURFACE}; border: 1px solid {BORDER};
        border-radius: 14px; padding: 20px 22px;
    }}
    .kpi-card .kpi-icon {{
        font-size: 20px; margin-bottom: 10px; opacity: 0.9;
    }}
    .kpi-card .kpi-value {{
        font-size: 2.1rem; font-weight: 700; color: {TEXT}; letter-spacing: -1px;
        line-height: 1;
    }}
    .kpi-card .kpi-label {{
        font-size: 0.82rem; color: {TEXT_MUTED}; margin-top: 6px;
    }}

    .chart-card {{
        background: {SURFACE}; border: 1px solid {BORDER};
        border-radius: 14px; padding: 20px; margin-top: 0.5rem;
    }}

    [data-testid="stDataFrame"] {{
        background: {SURFACE} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 14px !important;
        padding: 4px !important;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="spark-header">
    <div class="badge">S</div>
    <div>
        <div class="title">Dashboard</div>
        <div class="subtitle">{FIRMA_NAZWA} — przegląd aktywności Sparka</div>
    </div>
</div>
""", unsafe_allow_html=True)

response = supabase.table("klienci").select("*").execute()
data = response.data

if not data:
    st.markdown(f"""
    <div class="chart-card" style="text-align:center; padding: 3rem 1rem; color:{TEXT_MUTED};">
        Baza jest jeszcze pusta — nikt nie rozmawiał ze Sparkiem.
    </div>
    """, unsafe_allow_html=True)
else:
    df = pd.DataFrame(data)
    df["ostatnia_wizyta"] = pd.to_datetime(df["ostatnia_wizyta"], errors="coerce")
    total_clients = len(df)
    total_visits = int(df["liczba_wizyt"].sum())
    returning = int((df["liczba_wizyt"] > 1).sum())

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div class="kpi-value">{total_clients}</div>
            <div class="kpi-label">Liczba klientów</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💬</div>
            <div class="kpi-value">{total_visits}</div>
            <div class="kpi-label">Suma wizyt</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🔁</div>
            <div class="kpi-value">{returning}</div>
            <div class="kpi-label">Powracający klienci</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Wizyty w czasie</div>', unsafe_allow_html=True)
    df_z_data = df.dropna(subset=["ostatnia_wizyta"])
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if not df_z_data.empty:
        df_by_day = df_z_data.groupby(df_z_data["ostatnia_wizyta"].dt.date).size().reset_index(name="wizyty")
        df_by_day.columns = ["data", "wizyty"]

        fig = go.Figure(go.Bar(
            x=df_by_day["data"].astype(str),
            y=df_by_day["wizyty"],
            marker_color=ACCENT,
            marker_line_width=0,
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_MUTED, family="Inter"),
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            xaxis=dict(showgrid=False, color=TEXT_MUTED),
            yaxis=dict(showgrid=True, gridcolor=BORDER, color=TEXT_MUTED),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(f'<p style="color:{TEXT_MUTED};">Brak danych o datach wizyt.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Najczęstsze zainteresowania klientów</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    interests = df["zainteresowania"].dropna()
    if not interests.empty:
        all_terms = interests.str.split(",").explode().str.strip()
        all_terms = all_terms[all_terms != ""]
        counts = all_terms.value_counts().head(10)
        if not counts.empty:
            fig2 = go.Figure(go.Bar(
                x=counts.values,
                y=counts.index,
                orientation="h",
                marker_color=ACCENT_2,
                marker_line_color=ACCENT,
                marker_line_width=1,
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_MUTED, family="Inter"),
                margin=dict(l=10, r=10, t=10, b=10),
                height=320,
                xaxis=dict(showgrid=True, gridcolor=BORDER, color=TEXT_MUTED),
                yaxis=dict(showgrid=False, color=TEXT, autorange="reversed"),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown(f'<p style="color:{TEXT_MUTED};">Brak jeszcze zapisanych zainteresowań.</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="color:{TEXT_MUTED};">Brak jeszcze zapisanych zainteresowań.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Lista wszystkich klientów</div>', unsafe_allow_html=True)
    df_show = df[["imie", "telefon", "email", "liczba_wizyt", "ostatnia_wizyta", "zainteresowania"]].copy()
    df_show = df_show.sort_values("ostatnia_wizyta", ascending=False)
    df_show.columns = ["Imię", "Telefon", "Email", "Liczba wizyt", "Ostatnia wizyta", "Zainteresowania"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)
