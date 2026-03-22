import streamlit as st
import pandas as pd
import json
import requests
import base64
import math
import plotly.graph_objects as go

# =========================================================
# 1. KONFIGURACJA ZASOBÓW I GITHUB
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
    except: return None
    return None

BG_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.jpg")
if not BG_B64:
    BG_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.png")
LOGO_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png")

# =========================================================
# 2. STYLIZACJA INTERFEJSU
# =========================================================
st.set_page_config(page_title="VORTEZA STACK", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    bg_style = f"""
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(rgba(0,0,0,0.92), rgba(0,0,0,0.92)), 
                        url("data:image/jpeg;base64,{BG_B64}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
    """ if BG_B64 else "[data-testid='stAppViewContainer'] { background-color: #050505; }"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            :root {{ --v-copper: #B58863; --v-bg-panel: rgba(15, 15, 15, 0.98); }}
            {bg_style}
            [data-testid="stSidebar"] {{ 
                background-color: rgba(0, 0, 0, 0.85) !important; 
                border-right: 2px solid var(--v-copper);
                backdrop-filter: blur(10px);
            }}
            [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{ background-color: transparent !important; }}
            .stApp {{ color: #FFFFFF; font-family: 'Montserrat', sans-serif; }}
            .vorteza-card {{
                background: var(--v-bg-panel); padding: 25px; border-radius: 2px;
                border: 1px solid rgba(181, 136, 99, 0.3); border-left: 8px solid var(--v-copper);
                margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.7);
            }}
            th {{ background-color: var(--v-copper) !important; color: black !important; text-transform: uppercase; font-size: 0.85rem !important; }}
            td {{ background-color: #111 !important; color: #EEE !important; }}
            .stMetric {{ background: #000; padding: 15px; border-bottom: 4px solid var(--v-copper); }}
            h1, h2, h3 {{ color: var(--v-copper) !important; text-transform: uppercase; font-weight: 700; }}
            .stButton > button {{
                background-color: transparent; color: var(--v-copper); border: 2px solid var(--v-copper);
                font-weight: 700; width: 100%; border-radius: 0px;
            }}
            .stButton > button:hover {{ background-color: var(--v-copper); color: #000; }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. LOGIKA PAKOWANIA
# =========================================================
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
    # Sortowanie dla algorytmu Next Fit Decreasing Height (uproszczony)
    remaining = sorted(items, key=lambda x: x['length']*x['width'], reverse=True)
    fleet = []
    
    while remaining:
        placed_stacks, still_to_pack, curr_w, curr_x, curr_y, max_w_row = [], [], 0, 0, 0, 0
        for item in remaining:
            # Sprawdzenie wagi
            if curr_w + item['weight'] > veh['weight']: 
                still_to_pack.append(item); continue
            
            added = False
            # Próba piętrowania (Stacking)
            if item.get('canStack', True):
                for s in placed_stacks:
                    ch = sum(it['height'] for it in s['items'])
                    if (s['l'] == item['length'] and s['w'] == item['width'] and (ch + item['height']) <= veh['h']):
                        s['items'].append(item)
                        curr_w += item['weight']
                        added = True
                        break
            
            if not added:
                # Sprawdzenie miejsca na podłodze (Algorytm rzędowy)
                if curr_y + item['width'] > veh['w']: 
                    curr_y, curr_x = 0, curr_x + max_w_row
                    max_w_row = 0
                
                if curr_x + item['length'] <= veh['l']:
                    placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': item['length'], 'w': item['width'], 'items': [item]})
                    curr_y += item['width']
                    max_w_row = max(max_w_row, item['length'])
                    curr_w += item['weight']
                else:
                    still_to_pack.append(item)
        
        if not placed_stacks: break
        fleet.append({"stacks": placed_stacks, "weight": curr_w})
        remaining = still_to_pack
    return fleet

def draw_3d(stacks, veh, color_map):
    fig = go.Figure()
    # Obrys pojazdu
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
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=550)
    return fig

# =========================================================
# 4. GŁÓWNA APLIKACJA
# =========================================================
apply_vorteza_theme()
if "auth" not in st.session_state: st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    _, col_login, _ = st.columns([0.5, 2, 0.5])
    with col_login:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="display:block;margin:auto;max-width:450px;width:100%;margin-bottom:30px;">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("VORTEZA LOGIN")
        pwd = st.text_input("Hasło:", type="password")
        if st.button("WEJDŹ") and pwd == MASTER_PASSWORD: 
            st.session_state.auth = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- DANE ---
prods_base = get_products()
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state:
    st.session_state.colors = {p['name']: ["#B58863", "#967052", "#7A5B43", "#D4A373", "#A68A64"][i%5] for i, p in enumerate(prods_base)}

VEHICLES = {
    "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 7000},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500},
    "BUS (10ep)": {"l": 450, "w": 220, "h": 245, "weight": 1100},
}

# --- SIDEBAR ---
with st.sidebar:
    if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="display:block;margin:auto;max-width:180px;margin-bottom:20px;">', unsafe_allow_html=True)
    st.header("1. POJAZD")
    v_type = st.selectbox("TYP:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    
    st.header("2. TOWAR")
    if prods_base:
        p_names = [p['name'] for p in prods_base]
        sel_p = st.selectbox("PRODUKT:", p_names)
        p_qty = st.number_input("ILOŚĆ:", min_value=1, value=1)
        if st.button("DODAJ DO LISTY"):
            p_data = next(p for p in prods_base if p['name'] == sel_p)
            for _ in range(p_qty):
                st.session_state.cargo.append(p_data.copy())
            st.rerun()
    
    if st.button("WYCZYŚĆ LISTĘ"):
        st.session_state.cargo = []
        st.rerun()

# --- PANEL GŁÓWNY ---
st.title("🚚 VORTEZA STACK ANALYZER")

if not st.session_state.cargo:
    st.info("Twoja lista ładunkowa jest pusta. Dodaj towary z panelu bocznego.")
else:
    fleet = pack_logic(st.session_state.cargo, veh)
    
    # Metryki ogólne
    m_col1, m_col2, m_col3 = st.columns(3)
    total_items = len(st.session_state.cargo)
    total_weight = sum(p['weight'] for p in st.session_state.cargo)
    m_col1.metric("ŁADUNEK", f"{total_items} szt.")
    m_col2.metric("WAGA CAŁK.", f"{total_weight} kg")
    m_col3.metric("POTRZEBNE AUTA", f"{len(fleet)} x {v_type}")

    # Wyświetlanie aut
    for idx, truck in enumerate(fleet):
        with st.expander(f"AUTO NR {idx+1} (Waga: {truck['weight']} kg)", expanded=(idx==0)):
            col_viz, col_info = st.columns([2, 1])
            with col_viz:
                st.plotly_chart(draw_3d(truck['stacks'], veh, st.session_state.colors), use_container_width=True)
            with col_info:
                st.markdown("### SKŁAD AUTA")
                item_counts = {}
                for s in truck['stacks']:
                    for it in s['items']:
                        item_counts[it['name']] = item_counts.get(it['name'], 0) + 1
                
                df_truck = pd.DataFrame([{"Produkt": k, "Sztuk": v} for k, v in item_counts.items()])
                st.table(df_truck)

    st.markdown("### PEŁNA LISTA ŁADUNKOWA")
    df_all = pd.DataFrame(st.session_state.cargo)
    if not df_all.empty:
        st.dataframe(df_all[["name", "length", "width", "height", "weight"]], use_container_width=True)
