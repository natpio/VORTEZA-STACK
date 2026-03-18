import streamlit as st
import pandas as pd
import json
import requests
import base64
import math
import plotly.graph_objects as go

# =========================================================
# 1. KONFIGURACJA GITHUB & ZASOBY
# =========================================
try:
    GITHUB_TOKEN = st.secrets["G_TOKEN"]
    MASTER_PASSWORD = str(st.secrets.get("password", "NowyRozdzial"))
except Exception:
    GITHUB_TOKEN = None
    MASTER_PASSWORD = "NowyRozdzial"

REPO_OWNER = "natpio"
REPO_NAME = "VORTEZA-STACK"
FILE_PATH_PRODUCTS = "products.json"

# ADRESY ZASOBÓW
LOGO_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png"
BG_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.png"

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

LOGO_B64 = get_base64_img(LOGO_URL)
BG_B64 = get_base64_img(BG_URL)

# =========================================================
# 2. STYLIZACJA (WYMUSZENIE TŁA)
# =========================================================
st.set_page_config(page_title="VORTEZA CARGO | SQM", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    if BG_B64:
        # Wstrzykujemy styl bezpośrednio do kontenera widoku Streamlit
        st.markdown(f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
                
                :root {{
                    --v-copper: #B58863;
                }}

                /* KLUCZOWA POPRAWKA TŁA */
                [data-testid="stAppViewContainer"] {{
                    background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), 
                                url("data:image/png;base64,{BG_B64}");
                    background-size: cover;
                    background-position: center;
                    background-attachment: fixed;
                }}

                /* Przezroczystość dla głównego bloku */
                [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{
                    background-color: transparent !important;
                }}

                .stApp {{
                    color: #E0E0E0;
                    font-family: 'Montserrat', sans-serif;
                }}

                [data-testid="stSidebar"] {{
                    background-color: rgba(10, 10, 10, 0.95) !important;
                    border-right: 1px solid var(--v-copper);
                }}

                .vorteza-card {{
                    background: rgba(20, 20, 20, 0.8);
                    padding: 25px;
                    border-radius: 4px;
                    border: 1px solid rgba(181, 136, 99, 0.2);
                    border-left: 5px solid var(--v-copper);
                    backdrop-filter: blur(10px);
                    margin-bottom: 20px;
                }}

                h1, h2, h3 {{ color: var(--v-copper) !important; text-transform: uppercase; letter-spacing: 2.5px; }}
                
                .sidebar-logo {{
                    display: block;
                    margin: 0 auto 30px auto;
                    max-width: 200px;
                }}

                .stMetric {{ background: rgba(0,0,0,0.6); padding: 15px; border-radius: 4px; border-bottom: 3px solid var(--v-copper); }}
                
                .stButton > button {{
                    background-color: transparent; color: var(--v-copper); border: 1px solid var(--v-copper);
                    text-transform: uppercase; width: 100%; transition: 0.3s;
                }}
                .stButton > button:hover {{ background-color: var(--v-copper); color: black; }}
            </style>
        """, unsafe_allow_html=True)

# =========================================================
# 3. POZOSTAŁA LOGIKA (BEZ ZMIAN)
# =========================================================
VEHICLES = {
    "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000, "pallets": 33},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 7000, "pallets": 16},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
    "BUS (10ep)": {"l": 450, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
}

def get_products():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return json.loads(base64.b64decode(resp.json()['content']).decode('utf-8'))
    except: pass
    return []

def pack_logic(items, veh):
    rem = sorted(items, key=lambda x: x['length']*x['width'], reverse=True)
    fleet = []
    while rem:
        placed, still, cw, cx, cy, mw = [], [], 0, 0, 0, 0
        for it in rem:
            if cw + it['weight'] > veh['weight']: still.append(it); continue
            added = False
            if it.get('canStack', True):
                for s in placed:
                    h = sum(i['height'] for i in s['items'])
                    if s['l'] == it['length'] and s['w'] == it['width'] and (h + it['height']) <= veh['h']:
                        s['items'].append(it); cw += it['weight']; added = True; break
            if not added:
                if cy + it['width'] > veh['w']: cy, cx = 0, cx + mw; mw = 0
                if cx + it['length'] <= veh['l']:
                    placed.append({'x': cx, 'y': cy, 'l': it['length'], 'w': it['width'], 'items': [it]})
                    cy += it['width']; mw = max(mw, it['length']); cw += it['weight']
                else: still.append(it)
        if not placed: break
        fleet.append({"stacks": placed, "weight": cw})
        rem = still
    return fleet

def draw_3d(stacks, veh, colors):
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=[0, veh['l'], veh['l'], 0, 0, 0, veh['l'], veh['l'], 0, 0],
        y=[0, 0, veh['w'], veh['w'], 0, 0, 0, veh['w'], veh['w'], 0],
        z=[0, 0, 0, 0, 0, veh['h'], veh['h'], veh['h'], veh['h'], veh['h']],
        mode='lines', line=dict(color='#B58863', width=4), name='Auto'
    ))
    for s in stacks:
        zp = 0
        for it in s['items']:
            x0, y0, z0, dx, dy, dz = s['x'], s['y'], zp, it['length'], it['width'], it['height']
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=colors.get(it['name'], "#B58863"), opacity=0.9, name=it['name']
            ))
            zp += it['height']
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0))
    return fig

# =========================================================
# 4. START
# =========================================================
apply_vorteza_theme()

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, cl, _ = st.columns([1, 1.2, 1])
    with cl:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("LOGOWANIE")
        pwd = st.text_input("Hasło:", type="password")
        if st.button("Wejdź") and pwd == MASTER_PASSWORD: st.session_state.auth = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

prods = get_products()
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state:
    st.session_state.colors = {p['name']: ["#B58863", "#967052", "#7A5B43", "#D4A373", "#A68A64"][i%5] for i, p in enumerate(prods)}

with st.sidebar:
    if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
    v_name = st.selectbox("POJAZD:", list(VEHICLES.keys()))
    veh = VEHICLES[v_name]
    st.divider()
    sel_p = st.selectbox("PRODUKT:", [p['name'] for p in prods], index=None)
    qty = st.number_input("SZTUK:", min_value=1, value=1)
    if st.button("DODAJ") and sel_p:
        p_data = next(p for p in prods if p['name'] == sel_p)
        ex = next((i for i in st.session_state.cargo if i['name'] == sel_p), None)
        if ex: ex['total_qty'] += qty
        else: st.session_state.cargo.append({"name": sel_p, "total_qty": qty, **p_data})
        st.rerun()
    if st.button("RESTART"): st.session_state.cargo = []; st.rerun()

st.title("VORTEZA CARGO PLANNER PRO")

if st.session_state.cargo:
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    df_ed = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty']]
    res_ed = st.data_editor(df_ed, disabled=["name"], hide_index=True, use_container_width=True)
    if not res_ed.equals(df_ed):
        for idx, row in res_ed.iterrows(): st.session_state.cargo[idx]['total_qty'] = row['total_qty']
        st.session_state.cargo = [i for i in st.session_state.cargo if i['total_qty'] > 0]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    p_items = []
    for e in st.session_state.cargo:
        for _ in range(math.ceil(e['total_qty'] / e.get('itemsPerCase', 1))): p_items.append(e.copy())
    
    fleet = pack_logic(p_items, veh)
    for i, res in enumerate(fleet):
        with st.expander(f"🚚 POJAZD #{i+1}", expanded=True):
            cv, cs = st.columns([2.5, 1])
            with cv: st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.colors), use_container_width=True)
            with cs:
                st.metric("Waga", f"{res['weight']} kg")
                st.metric("Miejsca EP", f"{round(sum(s['l']*s['w'] for s in res['stacks'])/9600, 1)}")
                st.table(pd.DataFrame([it for s in res['stacks'] for it in s['items']]).groupby('name').size().reset_index(name='Skrzyń'))
