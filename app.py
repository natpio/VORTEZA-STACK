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

# Adresy plików z repozytorium (Upewnij się, że rozszerzenia są poprawne)
LOGO_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png"
BG_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.jpg"

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
# 2. DEFINICJA POJAZDÓW
# =========================================================
VEHICLES = {
    "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000, "pallets": 33},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 7000, "pallets": 16},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
    "BUS (10ep)": {"l": 450, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
}

COLOR_PALETTE = ["#B58863", "#967052", "#7A5B43", "#D4A373", "#A68A64"]

# =========================================================
# 3. STYLIZACJA INTERFEJSU (VORTEZA STACK)
# =========================================================
st.set_page_config(page_title="VORTEZA STACK | SQM", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    # Bardzo mocny overlay (90% czerni), żeby tło było tylko akcentem
    bg_css = ""
    if BG_B64:
        bg_css = f"""
            [data-testid="stAppViewContainer"] {{
                background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.9)), 
                            url("data:image/jpg;base64,{BG_B64}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
        """
    else:
        bg_css = """[data-testid="stAppViewContainer"] { background-color: #050505; }"""

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            
            :root {{
                --v-copper: #B58863;
                --v-bg-panel: rgba(20, 20, 20, 0.95);
            }}

            {bg_css}

            [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{
                background-color: transparent !important;
            }}

            .stApp {{
                color: #FFFFFF;
                font-family: 'Montserrat', sans-serif;
            }}

            /* Sidebar */
            [data-testid="stSidebar"] {{
                background-color: #0A0A0A !important;
                border-right: 2px solid var(--v-copper);
            }}

            /* Panele - teraz z pełniejszym tłem dla czytelności */
            .vorteza-card {{
                background: var(--v-bg-panel);
                padding: 30px;
                border-radius: 2px;
                border: 1px solid rgba(181, 136, 99, 0.3);
                border-left: 6px solid var(--v-copper);
                margin-bottom: 25px;
            }}

            h1, h2, h3 {{ 
                color: var(--v-copper) !important; 
                text-transform: uppercase; 
                letter-spacing: 3px; 
                font-weight: 700;
                margin-bottom: 20px;
            }}

            /* Poprawa widoczności etykiet i tekstu */
            p, label, .stMarkdown {{
                color: #E0E0E0 !important;
            }}
            
            .sidebar-logo {{
                display: block;
                margin: 0 auto 30px auto;
                max-width: 200px;
            }}

            .stMetric {{ 
                background: rgba(0,0,0,0.8); 
                padding: 20px; 
                border-radius: 2px; 
                border-bottom: 3px solid var(--v-copper); 
            }}
            
            [data-testid="stMetricValue"] {{
                color: var(--v-copper) !important;
            }}

            .stButton > button {{
                background-color: transparent; 
                color: var(--v-copper); 
                border: 2px solid var(--v-copper);
                font-weight: 700;
                text-transform: uppercase; 
                width: 100%; 
                padding: 12px;
                border-radius: 0px;
            }}
            .stButton > button:hover {{ 
                background-color: var(--v-copper); 
                color: #000000; 
            }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 4. LOGIKA
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
        mode='lines', line=dict(color='#B58863', width=4), name='Naczepa'
    ))
    for s in stacks:
        z_ptr = 0
        for it in s['items']:
            x0, y0, z0, dx, dy, dz = s['x'], s['y'], z_ptr, it['length'], it['width'], it['height']
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color_map.get(it['name'], "#B58863"), opacity=0.9, flatshading=True, name=it['name']
            ))
            z_ptr += it['height']
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=600)
    return fig

# =========================================================
# 5. START APLIKACJI
# =========================================================
apply_vorteza_theme()

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("LOGOWANIE VORTEZA")
        pwd = st.text_input("Hasło:", type="password")
        if st.button("WEJDŹ"):
            if pwd == MASTER_PASSWORD: st.session_state.auth = True; st.rerun()
            else: st.error("Hasło niepoprawne.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Dane
products_raw = get_products()
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state:
    st.session_state.colors = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(products_raw)}

with st.sidebar:
    if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
    st.header("Konfiguracja")
    v_type = st.selectbox("POJAZD:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    st.divider()
    st.header("Ładunek")
    sel_name = st.selectbox("PRODUKT:", [p['name'] for p in products_raw], index=None)
    qty = st.number_input("SZTUK:", min_value=1, value=1)
    if st.button("DODAJ") and sel_name:
        p_data = next(p for p in products_raw if p['name'] == sel_name)
        ex = next((i for i in st.session_state.cargo if i['name'] == sel_name), None)
        if ex: ex['total_qty'] += qty
        else: st.session_state.cargo.append({"name": sel_name, "total_qty": qty, **p_data})
        st.rerun()
    if st.button("WYCZYŚĆ"): st.session_state.cargo = []; st.rerun()

st.title("VORTEZA STACK")

if st.session_state.cargo:
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("Manifest")
    df = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty']]
    ed_df = st.data_editor(df, column_config={"name": "Produkt", "total_qty": "Ilość"}, disabled=["name"], hide_index=True, use_container_width=True)
    if not ed_df.equals(df):
        for idx, row in ed_df.iterrows(): st.session_state.cargo[idx]['total_qty'] = row['total_qty']
        st.session_state.cargo = [i for i in st.session_state.cargo if i['total_qty'] > 0]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Przygotowanie skrzyń
    p_items = []
    for e in st.session_state.cargo:
        for _ in range(math.ceil(e['total_qty'] / e.get('itemsPerCase', 1))): p_items.append(e.copy())
    
    fleet = pack_logic(p_items, veh)

    for i, res in enumerate(fleet):
        with st.expander(f"🚛 POJAZD #{i+1} | {res['weight']} kg", expanded=True):
            col_v, col_d = st.columns([2.5, 1])
            with col_v: st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.colors), use_container_width=True)
            with col_d:
                area = sum(s['l']*s['w'] for s in res['stacks'])
                st.metric("EP", f"{round(area/9600, 1)} / {veh['pallets']}")
                st.metric("Masa", f"{res['weight']} kg")
                st.progress(min(res['weight']/veh['weight'], 1.0))
                # Zestawienie
                st.write("**Lista:**")
                st.table(pd.DataFrame([it['name'] for s in res['stacks'] for it in s['items']], columns=['Produkt']).value_counts().reset_index())
else:
    st.info("System VORTEZA STACK gotowy. Dodaj produkty z panelu bocznego.")
