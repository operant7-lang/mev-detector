import streamlit as st
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="MEV Sandwich Detector",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Inter:wght@300;400;500;600;700;900&display=swap');

.stApp { background: #000; font-family: 'Inter', sans-serif; }
header { visibility: hidden; }

body::before {
    content: '';
    position: fixed;
    top: -100%;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(transparent, rgba(204,0,0,0.4), transparent);
    animation: scanline 6s linear infinite;
    z-index: 9999;
    pointer-events: none;
}

@keyframes scanline {
    0% { top: -2px; }
    100% { top: 100vh; }
}

body::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(204,0,0,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(204,0,0,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
}

.nav {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 64px;
    background: rgba(0,0,0,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(204,0,0,0.2);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 3rem;
    z-index: 1000;
}

.nav-brand {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.nav-accent {
    width: 4px;
    height: 20px;
    background: #cc0000;
    box-shadow: 0 0 8px #cc0000;
}

.nav-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    color: #cc0000;
    letter-spacing: 0.15em;
}

.nav-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #cc0000;
    box-shadow: 0 0 6px #cc0000;
    animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.2; }
}

.page {
    position: relative;
    z-index: 1;
    padding: 100px 3rem 3rem;
    max-width: 1400px;
    margin: 0 auto;
}

.hero {
    padding: 4rem 0 3rem;
    border-bottom: 1px solid rgba(204,0,0,0.15);
    margin-bottom: 2rem;
}

.hero-tag {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #cc0000;
    margin-bottom: 1.2rem;
}

.hero-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: clamp(2.5rem, 6vw, 5rem);
    font-weight: 700;
    line-height: 1.05;
    color: #fff;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.hero-title .red { color: #cc0000; text-shadow: 0 0 20px rgba(204,0,0,0.4); }

.hero-sub {
    font-size: 0.95rem;
    color: #555;
    max-width: 580px;
    line-height: 1.8;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: rgba(204,0,0,0.1);
    border: 1px solid rgba(204,0,0,0.15);
    margin-bottom: 1px;
}

.stat-cell {
    background: #080808;
    padding: 2rem;
    position: relative;
    overflow: hidden;
    transition: background 0.3s;
}

.stat-cell:hover { background: #0d0000; }

.stat-index {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    color: #333;
    margin-bottom: 0.75rem;
}

.stat-label {
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 0.75rem;
}

.stat-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    color: #fff;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.stat-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #cc0000;
}

.panel {
    background: #080808;
    border: 1px solid rgba(204,0,0,0.15);
    border-top: none;
    padding: 2rem;
    margin-bottom: 1px;
}

.panel-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #444;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(204,0,0,0.1);
    margin-bottom: 1.5rem;
}

.footer {
    border-top: 1px solid rgba(204,0,0,0.1);
    padding-top: 2rem;
    margin-top: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.footer-left {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #333;
}

.footer-right a {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #cc0000;
    text-decoration: none;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

[data-testid="metric-container"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="nav">
    <div class="nav-brand">
        <div class="nav-accent"></div>
        MEV Sandwich Detector
    </div>
    <div class="nav-status">
        <div class="nav-dot"></div>
        LIVE / ETHEREUM MAINNET
    </div>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_data():
    conn = psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=os.getenv("SUPABASE_PORT"),
        dbname=os.getenv("SUPABASE_DB"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD")
    )
    df = pd.read_sql("SELECT * FROM mev_sandwiches ORDER BY block_timestamp DESC", conn)
    conn.close()
    return df

df = load_data()
df['time'] = pd.to_datetime(df['block_timestamp'], unit='s')

total_sandwiches = len(df)
unique_bots = df['bot_address'].nunique() if len(df) > 0 else 0
unique_victims = df['victim_address'].nunique() if len(df) > 0 else 0
blocks_scanned = df['block_number'].nunique() if len(df) > 0 else 0

st.markdown('<div class="page">', unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-tag">// MEV Research Tool / Ethereum Mainnet</div>
    <div class="hero-title">
        Sandwich Attacks<br>
        <span class="red">Exposed in Real Time</span>
    </div>
    <div class="hero-sub">
        MEV bots exploit Ethereum users by sandwiching their DEX trades.
        This tool detects sandwich attacks in real time — identifying the bots,
        the victims, and the value extracted from each attack.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stat-grid">
    <div class="stat-cell">
        <div class="stat-index">// 01</div>
        <div class="stat-label">Sandwiches Detected</div>
        <div class="stat-value">{total_sandwiches:,}</div>
        <div class="stat-sub">confirmed attacks</div>
    </div>
    <div class="stat-cell">
        <div class="stat-index">// 02</div>
        <div class="stat-label">MEV Bots Identified</div>
        <div class="stat-value">{unique_bots}</div>
        <div class="stat-sub">unique attackers</div>
    </div>
    <div class="stat-cell">
        <div class="stat-index">// 03</div>
        <div class="stat-label">Victims</div>
        <div class="stat-value">{unique_victims:,}</div>
        <div class="stat-sub">wallets attacked</div>
    </div>
    <div class="stat-cell">
        <div class="stat-index">// 04</div>
        <div class="stat-label">Blocks Scanned</div>
        <div class="stat-value">{blocks_scanned:,}</div>
        <div class="stat-sub">ethereum blocks</div>
    </div>
</div>
""", unsafe_allow_html=True)

if len(df) > 0:
    # Bot rankings
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="panel"><div class="panel-title">// Most Active MEV Bots</div>', unsafe_allow_html=True)
        bot_stats = df.groupby('bot_address').agg(
            attacks=('id', 'count'),
        ).reset_index().sort_values('attacks', ascending=False).head(10)
        bot_stats.columns = ['Bot Address', 'Attacks']
        bot_stats['Bot Address'] = bot_stats['Bot Address'].str[:16] + "..."
        st.dataframe(bot_stats.reset_index(drop=True), use_container_width=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="panel"><div class="panel-title">// Most Targeted Contracts (DEX Routers)</div>', unsafe_allow_html=True)
        token_stats = df.groupby('token_address').agg(
            attacks=('id', 'count'),
        ).reset_index().sort_values('attacks', ascending=False).head(10)
        token_stats.columns = ['Contract', 'Attacks']
        token_stats['Contract'] = token_stats['Contract'].str[:16] + "..."
        st.dataframe(token_stats.reset_index(drop=True), use_container_width=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)

    # Timeline
    st.markdown('<div class="panel"><div class="panel-title">// Attack Timeline</div>', unsafe_allow_html=True)
    timeline = df.groupby(df['time'].dt.floor('h')).size().reset_index()
    timeline.columns = ['Time', 'Attacks']
    st.line_chart(timeline.set_index('Time'), height=160, color="#cc0000")
    st.markdown('</div>', unsafe_allow_html=True)

    # Recent attacks
    st.markdown('<div class="panel"><div class="panel-title">// Recent Sandwich Attacks</div>', unsafe_allow_html=True)
    display_df = df[['block_number', 'bot_address', 'victim_address', 'frontrun_tx', 'time']].head(20).copy()
    display_df.columns = ['Block', 'Bot', 'Victim', 'Frontrun TX', 'Time']
    display_df['Bot'] = display_df['Bot'].str[:14] + "..."
    display_df['Victim'] = display_df['Victim'].str[:14] + "..."
    display_df['Frontrun TX'] = display_df['Frontrun TX'].str[:16] + "..."
    st.dataframe(display_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="panel">
        <div class="panel-title">// Status</div>
        <div style="color:#444; font-family:'Share Tech Mono',monospace; font-size:0.8rem; padding:2rem 0;">
            Scanning blocks... No sandwich attacks detected yet. Check back in a few minutes.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="footer">
    <div class="footer-left">
        Monitoring Uniswap V2, V3, Sushiswap, 1inch on Ethereum mainnet
    </div>
    <div class="footer-right">
        <a href="https://github.com/Operant7-lang/mev-detector">View Source</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)