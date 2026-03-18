import streamlit as st
import pandas as pd
import json
import requests
import base64
import math
import plotly.graph_objects as go

# =========================================================
# 1. KONFIGURACJA GITHUB & ZASOBY (VORTEZA-STACK)
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

# Linki do plików graficznych (Raw GitHub)
URL_LOGO = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png"
URL_BG = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.jpg"

# Funkcja pobierająca obraz i zamieniająca na Base64 (rozwiązuje problem z tłem)
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

LOGO_B64 = get_base64_img(URL_LOGO)
BG_B64 = get_base64_img(URL_BG)

# =========================================================
# 2. KONFIGURACJA POJAZDÓW
# =========================================================
VEHICLES = {
    "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000, "pallets": 33},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 7000, "pallets": 16},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
    "BUS (10ep)": {"l": 450, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
}

COLOR_PALETTE = ["#B58863", "#967052", "#7A5B43", "#D4A373", "#A68A64"]

# =========================================================
# 3. STYLIZACJA VORTEZA (SZYTE TŁO I LOGO)
# =========================================================
st.set_page_config(page_title="VORTEZA CARGO | SQM", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    bg_style = ""
    if BG_B64:
        bg_style = f"""
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                        url("data:image/jpg;base64,{BG_B64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        bg_style = "background-color: #0E0E0E;"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            
            :root {{
                --v-copper: #B58863;
                --v-panel: rgba(15, 15, 15, 0.85);
            }}

            .stApp {{
                {bg_style}
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
# 4. LOGIKA POBIERANIA I PAKOWANIA
# =========================================================
def get_products_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content = resp.json()
            data = json.loads(base64.b64decode(content['content']).decode('utf-8'))
            return sorted(data, key=lambda x: x['name'])
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
    # Rama naczepy
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
# 5. CYKL ŻYCIA APLIKACJI
# =========================================================
apply_vorteza_theme()

if "auth" not in st.session_state: st.session_state.auth = False

# Panel Logowania
if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        if LOGO_B64:
            st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("Autoryzacja VORTEZA")
        pwd = st.text_input("Hasło systemowe:", type="password")
        if st.button("Zaloguj") and pwd == MASTER_PASSWORD:
            st.session_state.auth = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Pobranie danych
prods = get_products_from_github()
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state:
    st.session_state.colors = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

# Sidebar Sterujący
with st.sidebar:
    if LOGO_B64:
        st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
    
    st.header("⚙️ Ustawienia")
    v_name = st.selectbox("POJAZD:", list(VEHICLES.keys()))
    veh = VEHICLES[v_name]
    st.divider()
    
    st.header("📦 Dodaj Sprzęt")
    sel_p = st.selectbox("PRODUKT:", [p['name'] for p in prods], index=None, placeholder="Wybierz z bazy...")
    qty = st.number_input("ILOŚĆ SZTUK:", min_value=1, value=1)
    
    if st.button("DODAJ DO PLANU") and sel_p:
        p_data = next(p for p in prods if p['name'] == sel_p)
        exist = next((i for i in st.session_state.cargo if i['name'] == sel_p), None)
        if exist: exist['total_qty'] += qty
        else: st.session_state.cargo.append({"name": sel_p, "total_qty": qty, **p_data})
        st.rerun()
    
    if st.button("RESTART MANIFESTU"): 
        st.session_state.cargo = []; st.rerun()

# Główny widok planowania
st.title("VORTEZA CARGO PLANNER PRO")

if st.session_state.cargo:
    # Sekcja Edycji
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("📋 Aktywny Manifest")
    df_ed = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty']]
    res_ed = st.data_editor(df_ed, column_config={"name": "Produkt", "total_qty": "Sztuk"}, 
                            disabled=["name"], hide_index=True, use_container_width=True)
    
    if not res_ed.equals(df_ed):
        for idx, row in res_ed.iterrows(): st.session_state.cargo[idx]['total_qty'] = row['total_qty']
        st.session_state.cargo = [i for i in st.session_state.cargo if i['total_qty'] > 0]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Przeliczanie na fizyczne skrzynie
    phys_items = []
    for e in st.session_state.cargo:
        num_cases = math.ceil(e['total_qty'] / e.get('itemsPerCase', 1))
        for _ in range(num_cases): phys_items.append(e.copy())
    
    # Obliczenia załadunku
    fleet = pack_logic(phys_items, veh)

    # Wyświetlanie pojazdów
    for i, res in enumerate(fleet):
        with st.expander(f"🚚 POJAZD #{i+1} | Waga: {res['weight']} kg", expanded=True):
            cv, cs = st.columns([2.5, 1])
            with cv: 
                st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.colors), use_container_width=True)
            with cs:
                st.subheader("Analiza")
                area = sum(s['l']*s['w'] for s in res['stacks'])
                st.metric("Miejsca EP", f"{round(area/9600, 1)} / {veh['pallets']}")
                st.metric("Waga Ładunku", f"{res['weight']} kg")
                
                st.write("**Wykorzystanie:**")
                st.progress(min(res['weight']/veh['weight'], 1.0))
                
                # Tabela sztuk w tym konkretnym aucie
                this_v_items = [it for s in res['stacks'] for it in s['items']]
                v_summ = pd.DataFrame(this_v_items).groupby('name').size().reset_index(name='Skrzyń')
                st.table(v_summ)
else:
    st.info("Logistyka gotowa. Dodaj sprzęt z panelu bocznego, aby wygenerować plan załadunku.")
