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
    MASTER_PASSWORD = str(st.secrets["password"])
except Exception:
    GITHUB_TOKEN = None
    MASTER_PASSWORD = "NowyRozdzial"

REPO_OWNER = "natpio"
REPO_NAME = "VORTEZA-STACK"
FILE_PATH_PRODUCTS = "products.json"

# DOKŁADNE NAZWY Z TWOJEGO SCREENSHOTU
LOGO_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png"
BG_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.jpg"

VEHICLES = {
    "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000, "pallets": 33},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 7000, "pallets": 16},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
    "BUS (10ep)": {"l": 450, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
}

COLOR_PALETTE = ["#B58863", "#967052", "#7A5B43", "#D4A373", "#A68A64"]

# =========================================================
# 2. STYLIZACJA (DESIGN VORTEZA)
# =========================================================
st.set_page_config(page_title="VORTEZA CARGO | SQM", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            
            :root {{
                --v-copper: #B58863;
                --v-dark: #0E0E0E;
                --v-panel: rgba(15, 15, 15, 0.8);
            }}

            .stApp {{
                background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{BG_URL}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                color: #E0E0E0;
                font-family: 'Montserrat', sans-serif;
            }}

            [data-testid="stSidebar"] {{
                background-color: rgba(10, 10, 10, 0.95) !important;
                border-right: 1px solid var(--v-copper);
            }}

            .vorteza-card {{
                background: var(--v-panel);
                padding: 25px;
                border-radius: 4px;
                border: 1px solid rgba(181, 136, 99, 0.2);
                border-left: 5px solid var(--v-copper);
                backdrop-filter: blur(15px);
                margin-bottom: 20px;
            }}

            h1, h2, h3 {{ color: var(--v-copper) !important; text-transform: uppercase; letter-spacing: 2.5px; font-weight: 700; }}
            
            .sidebar-logo {{
                display: block;
                margin: 0 auto 30px auto;
                max-width: 200px;
            }}

            .stMetric {{ background: rgba(0,0,0,0.5); padding: 15px; border-radius: 4px; border-bottom: 3px solid var(--v-copper); }}
            
            .stButton > button {{
                background-color: transparent; color: var(--v-copper); border: 1px solid var(--v-copper);
                font-weight: 700; text-transform: uppercase; transition: 0.4s; width: 100%;
            }}
            .stButton > button:hover {{ background-color: var(--v-copper); color: black; }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. LOGIKA I POBIERANIE
# =========================================================
def get_products():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content = resp.json()
            data = json.loads(base64.b64decode(content['content']).decode('utf-8'))
            return sorted(data, key=lambda x: x['name'])
        return []
    except: return []

def pack_logic(items, veh):
    remaining = sorted(items, key=lambda x: x['length']*x['width'], reverse=True)
    fleet = []
    while remaining:
        placed_stacks, still_to_pack, curr_w, curr_x, curr_y, max_w_row = [], [], 0, 0, 0, 0
        for item in remaining:
            if curr_w + item['weight'] > veh['weight']:
                still_to_pack.append(item)
                continue
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
        mode='lines', line=dict(color='#B58863', width=4), name='Pojazd'
    ))
    for s in stacks:
        z_ptr = 0
        for item in s['items']:
            x0, y0, z0, dx, dy, dz = s['x'], s['y'], z_ptr, item['length'], item['width'], item['height']
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color_map.get(item['name'], "#B58863"), opacity=0.9, flatshading=True, name=item['name']
            ))
            z_ptr += item['height']
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=600)
    return fig

# =========================================================
# 4. START APLIKACJI
# =========================================================
apply_vorteza_theme()

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col_login, _ = st.columns([1,1.2,1])
    with col_login:
        st.markdown(f'<img src="{LOGO_URL}" class="sidebar-logo">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("Autoryzacja SQM")
        pwd = st.text_input("Hasło systemowe:", type="password")
        if st.button("Wejdź") and pwd == MASTER_PASSWORD:
            st.session_state.auth = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

prods = get_products()
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state:
    st.session_state.colors = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

with st.sidebar:
    st.markdown(f'<img src="{LOGO_URL}" class="sidebar-logo">', unsafe_allow_html=True)
    st.header("1. Pojazd")
    v_name = st.selectbox("TYP AUTA:", list(VEHICLES.keys()))
    veh = VEHICLES[v_name]
    st.divider()
    st.header("2. Dodaj ładunek")
    sel_p = st.selectbox("PRODUKT:", [p['name'] for p in prods], index=None, placeholder="Szukaj...")
    qty = st.number_input("ILOŚĆ SZTUK:", min_value=1, value=1)
    if st.button("DODAJ") and sel_p:
        p_data = next(p for p in prods if p['name'] == sel_p)
        exist = next((i for i in st.session_state.cargo if i['name'] == sel_p), None)
        if exist: exist['total_qty'] += qty
        else: st.session_state.cargo.append({"name": sel_p, "total_qty": qty, **p_data})
        st.rerun()
    if st.button("WYCZYŚĆ WSZYSTKO"): st.session_state.cargo = []; st.rerun()

# Główny widok
st.title("VORTEZA CARGO PLANNER PRO")

if st.session_state.cargo:
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("Manifest ładunkowy")
    df_ed = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty']]
    res_ed = st.data_editor(df_ed, column_config={"name": "Produkt", "total_qty": "Sztuk"}, disabled=["name"], hide_index=True, use_container_width=True)
    if not res_ed.equals(df_ed):
        for idx, row in res_ed.iterrows(): st.session_state.cargo[idx]['total_qty'] = row['total_qty']
        st.session_state.cargo = [i for i in st.session_state.cargo if i['total_qty'] > 0]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    phys_items = []
    for e in st.session_state.cargo:
        for _ in range(math.ceil(e['total_qty'] / e.get('itemsPerCase', 1))): phys_items.append(e.copy())
    
    fleet = pack_logic(phys_items, veh)

    for i, res in enumerate(fleet):
        with st.expander(f"🚛 POJAZD #{i+1} (Załadunek: {res['weight']} kg)", expanded=True):
            col_v, col_s = st.columns([2.5, 1])
            with col_v: st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.colors), use_container_width=True)
            with col_s:
                st.subheader("Raport")
                area = sum(s['l']*s['w'] for s in res['stacks'])
                st.metric("Miejsca EP", f"{round(area/9600, 1)}")
                st.metric("Waga", f"{res['weight']} kg")
                st.progress(min(res['weight']/veh['weight'], 1.0))
                st.table(pd.DataFrame([it for s in res['stacks'] for it in s['items']]).groupby('name').size().reset_index(name='Skrzyń'))
else:
    st.info("System gotowy. Wybierz sprzęt z panelu bocznego, aby rozpocząć planowanie transportu.")
