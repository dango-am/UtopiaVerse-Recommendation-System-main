import streamlit as st
import pandas as pd
import joblib
import difflib
import base64

# ── Page config (must be the very first st.* call) ───────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Utopiaverse · Discover Your Next Favorite",
    page_icon="🎮",
)

# ── CSS ───────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;600;700&family=Inter:wght@300;400;500&display=swap');

/* ─ Base ─ */
.stApp {
    background: #07070f !important;
    background-image:
        radial-gradient(ellipse 80% 60% at 12% 40%, rgba(90,20,190,.14) 0, transparent 60%),
        radial-gradient(ellipse 60% 50% at 88% 12%, rgba(0,160,230,.09) 0, transparent 50%);
    color: #d4d4ea;
    font-family: 'Inter', sans-serif;
}

/* ─ Subtle grid ─ */
.stApp::after {
    content: '';
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(0,190,255,.016) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,190,255,.016) 1px, transparent 1px);
    background-size: 64px 64px;
    pointer-events: none; z-index: 0;
}

/* ─ Main container ─ */
.main .block-container {
    padding: 0.5rem 2.5rem 3rem !important;
    max-width: 1440px;
}

/* ─ Sidebar ─ */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0b0b1e 0%, #0e0b22 100%) !important;
    border-right: 1px solid rgba(110,30,255,.26) !important;
}
[data-testid="stSidebar"] .block-container { padding-top: 1.2rem !important; }

/* ─ Selectbox ─ */
[data-baseweb="select"] > div {
    background: rgba(255,255,255,.05) !important;
    border: 1px solid rgba(110,30,255,.42) !important;
    border-radius: 8px !important;
    color: #ddddf4 !important;
    transition: border-color .2s, box-shadow .2s;
}
[data-baseweb="select"] > div:hover,
[data-baseweb="select"] > div:focus-within {
    border-color: rgba(0,205,255,.62) !important;
    box-shadow: 0 0 14px rgba(0,205,255,.14) !important;
}

/* ─ Dropdown list ─ */
[data-baseweb="menu"] {
    background: #0e0e22 !important;
    border: 1px solid rgba(110,30,255,.28) !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"] li { color: #ccccde !important; }
[data-baseweb="menu"] li:hover { background: rgba(110,30,255,.18) !important; }

/* ─ Buttons ─ */
.stButton > button {
    background: linear-gradient(135deg, #6a18f0 0%, #00b8f0 100%) !important;
    color: #fff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 0 18px rgba(106,24,240,.4) !important;
    transition: box-shadow .25s ease, transform .2s ease !important;
    padding: .5rem 2rem !important;
}
.stButton > button:hover {
    box-shadow: 0 0 28px rgba(0,184,240,.55) !important;
    transform: translateY(-2px) !important;
}

/* ─ Alerts ─ */
div[data-testid="stAlert"] { border-radius: 10px !important; }

/* ─ Images ─ */
[data-testid="stImage"] img {
    border-radius: 10px !important;
    border: 1px solid rgba(110,30,255,.35) !important;
    box-shadow: 0 6px 26px rgba(0,0,0,.5) !important;
}

/* ─ Expanders ─ */
details {
    background: rgba(255,255,255,.022) !important;
    border: 1px solid rgba(110,30,255,.2) !important;
    border-radius: 8px !important;
    margin-top: .4rem !important;
}
details summary p {
    color: #00ccee !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
}
details > div p { color: #a8a8c8 !important; font-size: .9rem !important; line-height: 1.7 !important; }

/* ─ Dividers ─ */
hr { border-color: rgba(110,30,255,.18) !important; margin: 1.4rem 0 !important; }

/* ─ Spinner ─ */
[data-testid="stSpinner"] > div { border-top-color: #00d4ff !important; }

/* ─ Scrollbar ─ */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #07070f; }
::-webkit-scrollbar-thumb { background: #6a18f0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00c8f0; }

/* ─ Hide Streamlit chrome ─ */
#MainMenu, footer, header { visibility: hidden !important; }

/* ─────────────────────────────────────────────────────
   Custom HTML components
───────────────────────────────────────────────────── */

/* Hero */
.hero-wrap {
    text-align: center;
    padding: 2rem 0 2.5rem;
}

/* ─ Logo glow ─ */
.logo-glow-wrap {
    display: inline-block;
    filter: drop-shadow(0 0 18px rgba(106,24,240,.75))
            drop-shadow(0 0 42px rgba(0,212,255,.38));
    margin-bottom: .75rem;
    animation: logoPulse 3s ease-in-out infinite;
}
.hero-logo-img {
    max-height: 100px;
    max-width: 520px;
    width: auto;
    border: none !important;
    box-shadow: none !important;
    background: transparent;
    border-radius: 0 !important;
}
@keyframes logoPulse {
    0%, 100% {
        filter: drop-shadow(0 0 18px rgba(106,24,240,.75))
                drop-shadow(0 0 42px rgba(0,212,255,.38));
    }
    50% {
        filter: drop-shadow(0 0 30px rgba(106,24,240,1))
                drop-shadow(0 0 60px rgba(0,212,255,.6));
    }
}

.hero-tagline {
    font-family: 'Rajdhani', sans-serif;
    font-size: .92rem;
    color: #a0a0cc;
    letter-spacing: 6px;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    text-shadow: 0 0 12px rgba(0,212,255,.55), 0 0 28px rgba(106,24,240,.4);
}
.hero-badges {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
}
.hero-badge {
    font-size: .7rem;
    font-family: 'Inter', sans-serif;
    color: #44447a;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(110,30,255,.2);
    padding: 3px 14px;
    border-radius: 20px;
    letter-spacing: .8px;
}

/* Telegram banner */
.tg-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 0.6rem auto 0;
    background: linear-gradient(135deg, rgba(0,136,204,.15) 0%, rgba(106,24,240,.15) 100%);
    border: 1px solid rgba(0,136,204,.35);
    border-radius: 30px;
    padding: 8px 22px;
    width: fit-content;
    text-decoration: none;
    transition: box-shadow .25s, transform .2s;
}
.tg-banner:hover {
    box-shadow: 0 0 22px rgba(0,136,204,.35);
    transform: translateY(-2px);
}
.tg-icon { font-size: 1.1rem; }
.tg-text {
    font-family: 'Rajdhani', sans-serif;
    font-size: .85rem;
    font-weight: 700;
    color: #00aaff;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.tg-handle {
    font-family: 'Orbitron', monospace;
    font-size: .72rem;
    color: #6a18f0;
    letter-spacing: 1px;
}

/* Section heads */
.section-head {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #00d4ff;
    text-transform: uppercase;
    letter-spacing: 2px;
    border-left: 3px solid #6a18f0;
    padding-left: 10px;
    margin: 0 0 .9rem;
}

/* Game cards — the signature CRT-scan-line top edge */
.card {
    background: linear-gradient(140deg, rgba(255,255,255,.044) 0%, rgba(255,255,255,.01) 100%);
    border: 1px solid rgba(110,30,255,.28);
    border-radius: 12px;
    padding: 1rem 1.2rem 1.1rem;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6a18f0 0%, #00c8ff 50%, #ff2d78 100%);
}
.card-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: #fff;
    line-height: 1.2;
}
.rating-pill {
    display: inline-block;
    background: linear-gradient(135deg, #6a18f0, #00b8f0);
    color: #fff;
    font-family: 'Orbitron', monospace;
    font-size: .7rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    margin-left: 8px;
    vertical-align: middle;
    letter-spacing: 1px;
}
.tag-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: .5rem; }
.tag {
    font-size: .68rem;
    font-family: 'Inter', sans-serif;
    padding: 2px 9px;
    border-radius: 4px;
}
.tag.g { background: rgba(110,30,255,.14); border: 1px solid rgba(110,30,255,.3); color: #a070ff; }
.tag.p { background: rgba(0,212,255,.09);  border: 1px solid rgba(0,212,255,.26); color: #00d4ff; }

/* Sidebar Telegram card */
.tg-sidebar-card {
    background: linear-gradient(135deg, rgba(0,136,204,.12) 0%, rgba(106,24,240,.12) 100%);
    border: 1px solid rgba(0,136,204,.3);
    border-radius: 10px;
    padding: .8rem 1rem;
    text-align: center;
    margin-top: .4rem;
}
.tg-sidebar-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: .8rem;
    font-weight: 700;
    color: #00aaff;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: .3rem;
}
.tg-sidebar-link {
    font-family: 'Orbitron', monospace;
    font-size: .75rem;
    color: #a070ff;
    text-decoration: none;
    letter-spacing: .8px;
    transition: color .2s;
}
.tg-sidebar-link:hover { color: #00d4ff; }

/* No-data state */
.no-data {
    text-align: center; padding: 5rem 1rem; color: #383858;
}
.no-data-icon { font-size: 4rem; }
.no-data-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.1rem; color: #6a18f0; margin: 1rem 0 .4rem;
}
.no-data-sub { font-size: .88rem; }
</style>
""", unsafe_allow_html=True)


# ── Load Artifacts ────────────────────────────────────────────────────────────────
@st.cache_data
def load_artifacts():
    try:
        df             = pd.read_pickle("processed_new_df.pkl")
        feature_matrix = joblib.load("weighted_features.joblib")
        model          = joblib.load("knn_model_final.joblib")
        return df, feature_matrix, model
    except FileNotFoundError as e:
        st.error(f"Could not find file: {e}")
        return None, None, None
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return None, None, None


df, feature_matrix, model = load_artifacts()


# ── Recommendation Engine ─────────────────────────────────────────────────────────
def get_recommendations(game_name, df_source, matrix_source, model_source, platform='Any', top_n=10):
    matches = df_source[df_source['name'].str.lower() == game_name.lower()]

    if not matches.empty:
        game_idx     = matches.index[0]
        matched_game = matches.iloc[0]['name']
    else:
        all_game_names  = df_source['name'].tolist()
        closest_matches = difflib.get_close_matches(game_name, all_game_names, n=1, cutoff=0.6)
        if not closest_matches:
            return f"No match found for '{game_name}'.", None
        matched_game = closest_matches[0]
        game_idx     = df_source[df_source['name'] == matched_game].index[0]

    game_vector = matrix_source[game_idx]
    distances, indices = model_source.kneighbors(game_vector, n_neighbors=50)

    similar_indices = indices.flatten()
    similar_indices = similar_indices[similar_indices != game_idx]
    recommendations  = df_source.iloc[similar_indices].copy()

    if platform != 'Any':
        platform_col = f'parent_platforms_{platform}'
        if platform_col in df_source.columns:
            recommendations = recommendations[recommendations[platform_col] == 1]

    recommendations = recommendations.head(top_n)
    if recommendations.empty:
        return f"No games found like '{matched_game}' on {platform}.", None

    def get_labels(row, prefix):
        cols = [c for c in df_source.columns if c.startswith(prefix)]
        return ' | '.join([c.replace(prefix, '') for c in cols if row[c] == 1])

    recommendations['Platforms'] = recommendations.apply(lambda x: get_labels(x, 'parent_platforms_'), axis=1)
    recommendations['Genres']    = recommendations.apply(lambda x: get_labels(x, 'genres_'),           axis=1)

    return matched_game, recommendations[['name', 'rating', 'Platforms', 'Genres']]


# ── Helper: turn "Action | RPG | Adventure" into HTML tag spans ───────────────────
def make_tags(pipe_str: str, css_cls: str) -> str:
    if not pipe_str:
        return ""
    return "".join(
        f'<span class="tag {css_cls}">{t.strip()}</span>'
        for t in pipe_str.split("|") if t.strip()
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-family:Orbitron,monospace;font-size:.8rem;color:#6a18f0;'
        'letter-spacing:2px;text-transform:uppercase;margin-bottom:.8rem">⚙ Configuration</div>',
        unsafe_allow_html=True
    )
    st.divider()

    if df is not None:
        platform_cols = sorted(
            c.replace('parent_platforms_', '')
            for c in df.columns
            if c.startswith('parent_platforms_')
            and c.replace('parent_platforms_', '').strip()
        )
        selected_platform = st.selectbox("🕹️ Filter by Platform", ['Any'] + platform_cols)
    else:
        selected_platform = 'Any'

    st.divider()
    st.markdown("""
    <div style="font-family:'Inter',sans-serif;font-size:.76rem;color:#3a3a5a;line-height:2.1">
        📡 <span style="color:#6a18f0">KNN</span> + <span style="color:#00c8f0">TF-IDF</span> engine<br>
        🧩 Weighted feature fusion<br>
        📐 Cosine similarity search<br>
        🏆 Top-10 recommendations
    </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Telegram Bot Link in Sidebar ──────────────────────────────────────────────
    st.markdown("""
    <div class="tg-sidebar-card">
        <div class="tg-sidebar-title">📱 Also on Telegram</div>
        <div style="font-size:1.4rem;margin:.3rem 0">✈️</div>
        <a class="tg-sidebar-link" href="https://t.me/Utopiaverse_bot" target="_blank">
            @Utopiaverse_bot
        </a>
        <div style="font-family:'Inter',sans-serif;font-size:.68rem;color:#3a3a5a;margin-top:.4rem">
            Get recommendations on the go
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Hero Section ──────────────────────────────────────────────────────────────────

def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        data = f.read()
    ext = image_path.split(".")[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

LOGO = get_base64_image("Utopiaverse_logo.jpg")

st.markdown(f"""
<div class="hero-wrap">
  <div class="logo-glow-wrap">
    <img src="{LOGO}" class="hero-logo-img" alt="Utopiaverse Logo"/>
  </div>
  <div class="hero-tagline">DISCOVER &nbsp;·&nbsp; PLAY &nbsp;·&nbsp; REPEAT</div>
  <div class="hero-badges">
    <span class="hero-badge">⚡ KNN Algorithm</span>
    <span class="hero-badge">🔍 TF-IDF Vectorization</span>
    <span class="hero-badge">🎯 Precision Matching</span>
    <span class="hero-badge">🕹️ Platform Filtering</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Main App ──────────────────────────────────────────────────────────────────────
if df is not None and model is not None:

    # Platform-aware game list
    if selected_platform == 'Any':
        game_list = sorted(df['name'].unique())
    else:
        p_col     = f'parent_platforms_{selected_platform}'
        game_list = sorted(df[df[p_col] == 1]['name'].unique())

    # Search panel
    st.markdown('<div class="section-head">🔍 Find Your Next Game</div>', unsafe_allow_html=True)
    game_input = st.selectbox("game_select", game_list, label_visibility="collapsed")

    btn_col, _ = st.columns([1, 3])
    with btn_col:
        go = st.button("⚡ Find Matches", type="primary")

    st.divider()

    # ─ Results ─
    if go:
        with st.spinner("🔮 Scanning the game universe…"):
            title, recs = get_recommendations(
                game_input, df, feature_matrix, model,
                platform=selected_platform, top_n=10,
            )

        if recs is None:
            st.error(title)
        else:
            st.success(f"✅  Found **{len(recs)}** games based on **{title}**")

            # Selected game
            st.markdown('<div class="section-head" style="margin-top:1.4rem">🎯 Selected Game</div>',
                        unsafe_allow_html=True)
            sel = df[df['name'] == title].iloc[0]

            c1, c2 = st.columns([1, 2])
            with c1:
                if pd.notna(sel.get('background_image')):
                    st.image(sel['background_image'], use_container_width=True)
            with c2:
                g_str = ' | '.join(
                    c.replace('genres_', '')
                    for c in df.columns if c.startswith('genres_') and sel[c] == 1
                )
                p_str = ' | '.join(
                    c.replace('parent_platforms_', '')
                    for c in df.columns if c.startswith('parent_platforms_') and sel[c] == 1
                )
                st.markdown(f"""
                <div class="card">
                  <div class="card-title">{sel['name']}</div>
                  <div class="tag-row">{make_tags(g_str, 'g')}</div>
                  <div class="tag-row">{make_tags(p_str, 'p')}</div>
                </div>""", unsafe_allow_html=True)
                if pd.notna(sel.get('description')):
                    with st.expander("📖 Full description"):
                        st.write(sel['description'])

            st.divider()

            # Recommended games
            st.markdown('<div class="section-head">🔥 Recommended Games</div>', unsafe_allow_html=True)

            for _, row in recs.iterrows():
                rf = df[df['name'] == row['name']].iloc[0]
                c1, c2 = st.columns([1, 3])
                with c1:
                    if pd.notna(rf.get('background_image')):
                        st.image(rf['background_image'], use_container_width=True)
                with c2:
                    st.markdown(f"""
                    <div class="card">
                      <div class="card-title">
                        {row['name']}
                        <span class="rating-pill">⭐ {row['rating']:.2f}</span>
                      </div>
                      <div class="tag-row">{make_tags(row['Genres'],    'g')}</div>
                      <div class="tag-row">{make_tags(row['Platforms'], 'p')}</div>
                    </div>""", unsafe_allow_html=True)
                    if pd.notna(rf.get('description')):
                        st.write(rf['description'][:280].rstrip() + "…")
                        with st.expander("Read more"):
                            st.write(rf['description'])
                st.divider()

else:
    st.markdown("""
    <div class="no-data">
      <div class="no-data-icon">⚠️</div>
      <div class="no-data-title">MISSING GAME DATA</div>
      <div class="no-data-sub">Upload model artifacts to activate the recommender.</div>
    </div>""", unsafe_allow_html=True)
