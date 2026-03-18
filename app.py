import streamlit as st
import pandas as pd
import json
import requests
import base64
import math
import plotly.graph_objects as go

# =========================================================
# 1. KONFIGURACJA GITHUB & ZASOBY
# =========================================================
try:
    GITHUB_TOKEN = st.secrets["G_TOKEN"]
    MASTER_PASSWORD = str(st.secrets.get("password", "NowyRozdzial"))
except Exception:
    GITHUB_TOKEN = None
    MASTER_PASSWORD = "NowyRozdzial"

REPO_OWNER = "natpio"
REPO_NAME = "VORTEZA-STACK"
FILE_PATH_PRODUCTS = "products.json"

@st.cache_data
def get_base64_img(url):
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except:
        return None
    return None

# PRÓBA POBRANIA LOGO
LOGO_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png"
LOGO_B64 = get_base64_img(LOGO_URL)

# PRÓBA POBRANIA TŁA (Sprawdza .jpg oraz .png)
BG_URL_JPG = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.jpg"
BG_URL_PNG = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.png"

BG_B64 = get_base64_img(BG_URL_JPG)
if not BG_B64:
    BG_B64 = get_base64_img(BG_URL_PNG)

# =========================================================
# 2. STYLIZACJA (VORTEZA STACK - CLEAN CUT)
# =========================================================
st.set_page_config(page_title="VORTEZA STACK", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    # Jeśli tło istnieje, stosujemy silny filtr przyciemniający (90% czerni)
    bg_style = ""
    if BG_B64:
        bg_style = f"""
            [data-testid="stAppViewContainer"] {{
                background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.9)), 
                            url("data:image/jpeg;base64,{BG_B64}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
        """
    else:
        bg_style = """[data-testid="stAppViewContainer"] { background-color: #050505; }"""

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            
            :root {{
                --v-copper: #B58863;
                --v-bg-panel: rgba(15, 15, 15, 0.98);
            }}

            {bg_style}

            [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{
                background-color: transparent !important;
            }}

            .stApp {{
                color: #FFFFFF;
                font-family: 'Montserrat', sans-serif;
            }}

            /* Sidebar */
            [data-testid="stSidebar"] {{
                background-color: #000000 !important;
                border-right: 2px solid var(--v-copper);
            }}

            /* Karty ładunku - Solidny kontrast */
            .vorteza-card {{
                background: var(--v-bg-panel);
                padding: 30px;
                border-radius: 2px;
                border: 1px solid rgba(181, 136, 99, 0.4);
                border-left: 8px solid var(--v-copper);
                margin-bottom: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
            }}

            h1, h2, h3 {{ 
                color: var(--v-copper) !important; 
                text-transform: uppercase; 
                letter-spacing: 3px; 
                font-weight: 700;
                margin-bottom: 15px;
            }}

            /* Formularze i Labele */
            label p {{
                color: #B58863 !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                font-size: 0.9rem;
            }}

            .sidebar-logo {{
                display: block;
                margin: 0 auto 40px auto;
                max-width: 200px;
            }}

            /* Metryki */
            .stMetric {{ 
                background: #000000; 
                padding: 20px; 
                border: 1px solid #333;
                border-bottom: 4px solid var(--v-copper); 
            }}
            
            [data-testid="stMetricValue"] {{ color: #FFFFFF !important; }}
            [data-testid="stMetricLabel"] {{ color: var(--v-copper) !important; }}

            /* Przyciski */
            .stButton > button {{
                background-color: transparent; 
                color: var(--v-copper); 
                border: 2px solid var(--v-copper);
                font-weight: 700;
                text-transform: uppercase; 
                width: 100%; 
                border-radius: 0px;
                padding: 10px;
            }}
            .stButton > button:hover {{ 
                background-color: var(--v-copper); 
                color: #000000; 
            }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. LOGIKA I POBIERANIE (DOKŁADNE)
# =========================================================
def get_products():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content = resp.json()
            return json.loads(base64.b64decode(content['content']).decode('utf-8'))
    except: pass
    return []

def pack_logic(items, veh):
    remaining = sorted(items, key=lambda x: x['length']*x['width'], reverse=True)
    fleet = []
    while remaining:
        placed_stacks, still_to_pack, curr_w, curr_x, curr_y, max_w_row = [], [], 0, 0, 0, 0
        for item in remaining:
            if curr_w + item['weight'] > veh['weight']:
                still_to_pack.append(item); continue
            added = False
            if item.get('canStack', True):
                for s in placed_stacks:
                    ch = sum(i['height'] for i in s['items'])
                    if (s['l'] == item['length'] and s['w'] == item['width'] and (ch + item['height']) <= veh['h']):
                        s['items'].append(item); curr_w += item['weight']; added = True; break
            if not added:
                if curr_y + item['width'] > veh['w']:
                    curr_y, curr_x = 0, curr_x + max_w_row; max_w_row = 0
                if curr_x + item['length'] <= veh['l']:
                    placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': item['length'], 'w': item['width'], 'items': [item]})
                    curr_y += item['width']; max_w_row = max(max_w_row, item['length']); curr_w += item['weight']
                else: still_to_pack.append(item)
        if not placed_stacks: break
        fleet.append({"stacks": placed_stacks, "weight": curr_w})
        remaining = still_to_pack
    return fleet

def draw_3d(stacks, veh, color_map):
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=[0, veh['l'], veh['l'], 0, 0, 0, veh['l'], veh['l'], 0, 0],
        y=[0, 0, veh['w'], veh['w'], 0, 0, 0, veh['w'], veh['w'], 0],
        z=[0, 0, 0, 0, 0, veh['h'], veh['h'], veh['h'], veh['h'], veh['h']],
        mode='lines', line=dict(color='#B58863', width=4), name='Auto'
    ))
    for s in stacks:
        z_p = 0
        for it in s['items']:
            x0, y0, z0, dx, dy, dz = s['x'], s['y'], z_p, it['length'], it['width'], it['height']
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color_map.get(it['name'], "#B58863"), opacity=0.9, flatshading=True, name=it['name']
            ))
            z_p += it['height']
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=600)
    return fig

# =========================================================
# 4. START
# =========================================================
apply_vorteza_theme()

if "auth" not in st.session_state: st.session_state.auth = False

# LOGOWANIE
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("LOGOWANIE DO SYSTEMU")
        pwd = st.text_input("Hasło:", type="password")
        if st.button("AUTORYZACJA") and pwd == MASTER_PASSWORD:
            st.session_state.auth = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# DANE I SESJA
prods = get_products()
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state:
    st.session_state.colors = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

VEHICLES = {
    "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000, "pallets": 33},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 7000, "pallets": 16},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
    "BUS (10ep)": {"l": 450, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
}

with st.sidebar:
    if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
    st.header("USTAWIENIA")
    v_type = st.selectbox("FLOTA:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    st.divider()
    st.header("DODAJ ŁADUNEK")
    sel = st.selectbox("PRODUKT:", [p['name'] for p in prods], index=None)
    num = st.number_input("SZTUK:", min_value=1, value=1)
    if st.button("DODAJ DO PLANU") and sel:
        p_d = next(p for p in prods if p['name'] == sel)
        ex = next((i for i in st.session_state.cargo if i['name'] == sel), None)
        if ex: ex['total_qty'] += num
        else: st.session_state.cargo.append({"name": sel, "total_qty": num, **p_d})
        st.rerun()
    if st.button("RESTART"): st.session_state.cargo = []; st.rerun()

st.title("VORTEZA STACK")

if st.session_state.cargo:
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("MANIFEST ZAŁADUNKOWY")
    df = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty']]
    ed_df = st.data_editor(df, column_config={"name": "Produkt", "total_qty": "Sztuk"}, disabled=["name"], hide_index=True, use_container_width=True)
    if not ed_df.equals(df):
        for idx, row in ed_df.iterrows(): st.session_state.cargo[idx]['total_qty'] = row['total_qty']
        st.session_state.cargo = [i for i in st.session_state.cargo if i['total_qty'] > 0]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    cases = []
    for e in st.session_state.cargo:
        for _ in range(math.ceil(e['total_qty'] / e.get('itemsPerCase', 1))): cases.append(e.copy())
    
    fleet = pack_logic(cases, veh)
    for i, res in enumerate(fleet):
        with st.expander(f"🚛 POJAZD #{i+1} - {res['weight']} kg", expanded=True):
            c1, c2 = st.columns([2.5, 1])
            with c1: st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.colors), use_container_width=True)
            with c2:
                a = sum(s['l']*s['w'] for s in res['stacks'])
                st.metric("PŁASZCZYZNA (EP)", f"{round(a/9600, 1)} / {veh['pallets']}")
                st.metric("MASA CAŁKOWITA", f"{res['weight']} kg")
                st.progress(min(res['weight']/veh['weight'], 1.0))
                st.write("**SKŁAD:**")
                st.table(pd.DataFrame([it['name'] for s in res['stacks'] for it in s['items']], columns=['Produkt']).value_counts().reset_index())
else:
    st.info("System gotowy. Wybierz pojazd i dodaj ładunek w panelu bocznym.")
