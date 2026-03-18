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

# Pobieranie tła i logo
BG_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.jpg")
if not BG_B64:
    BG_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.png")
LOGO_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png")

# =========================================================
# 2. STYLIZACJA INTERFEJSU (VORTEZA STACK DARK)
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
            
            [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{ background-color: transparent !important; }}
            .stApp {{ color: #FFFFFF; font-family: 'Montserrat', sans-serif; }}
            [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid var(--v-copper); }}

            /* Panele i Karty */
            .vorteza-card {{
                background: var(--v-bg-panel); padding: 25px; border-radius: 2px;
                border: 1px solid rgba(181, 136, 99, 0.3); border-left: 8px solid var(--v-copper);
                margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.7);
            }}

            /* Stylizacja Tabel (Usunięcie bieli) */
            .stTable, [data-testid="stTable"] {{ 
                background-color: transparent !important; 
                border: 1px solid #333 !important; 
            }}
            th {{ 
                background-color: var(--v-copper) !important; 
                color: black !important; 
                text-transform: uppercase; 
                letter-spacing: 1px; 
                font-size: 0.85rem !important;
                padding: 10px !important;
            }}
            td {{ 
                background-color: #111 !important; 
                color: #EEE !important; 
                border-bottom: 1px solid #222 !important; 
            }}
            
            /* Metryki i Progress Bar */
            .stMetric {{ background: #000; padding: 15px; border: 1px solid #222; border-bottom: 4px solid var(--v-copper); }}
            [data-testid="stMetricValue"] {{ color: #FFF !important; font-weight: 700; }}
            .stProgress > div > div > div > div {{ background-color: var(--v-copper) !important; }}

            h1, h2, h3 {{ color: var(--v-copper) !important; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; }}
            
            .stButton > button {{
                background-color: transparent; color: var(--v-copper); border: 2px solid var(--v-copper);
                font-weight: 700; text-transform: uppercase; width: 100%; border-radius: 0px;
            }}
            .stButton > button:hover {{ background-color: var(--v-copper); color: #000; box-shadow: 0 0 15px var(--v-copper); }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. LOGIKA PAKOWANIA I DANYCH
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
    remaining = sorted(items, key=lambda x: x['length']*x['width'], reverse=True)
    fleet = []
    while remaining:
        placed_stacks, still_to_pack, curr_w, curr_x, curr_y, max_w_row = [], [], 0, 0, 0, 0
        for item in remaining:
            if curr_w + item['weight'] > veh['weight']: still_to_pack.append(item); continue
            added = False
            if item.get('canStack', True):
                for s in placed_stacks:
                    ch = sum(i['height'] for i in s['items'])
                    if (s['l'] == item['length'] and s['w'] == item['width'] and (ch + item['height']) <= veh['h']):
                        s['items'].append(item); curr_w += item['weight']; added = True; break
            if not added:
                if curr_y + item['width'] > veh['w']: curr_y, curr_x = 0, curr_x + max_w_row; max_w_row = 0
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
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=550)
    return fig

# =========================================================
# 4. GŁÓWNA APLIKACJA
# =========================================================
apply_vorteza_theme()
if "auth" not in st.session_state: st.session_state.auth = False

# LOGOWANIE
if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="display:block;margin:auto;max-width:200px;margin-bottom:30px;">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("VORTEZA SYSTEM LOGIN")
        pwd = st.text_input("Hasło dostępowe:", type="password")
        if st.button("WEJDŹ DO SYSTEMU") and pwd == MASTER_PASSWORD: st.session_state.auth = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# DANE I SESJA
prods_base = get_products()
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state:
    st.session_state.colors = {p['name']: ["#B58863", "#967052", "#7A5B43", "#D4A373", "#A68A64"][i%5] for i, p in enumerate(prods_base)}

VEHICLES = {
    "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000, "pallets": 33},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 7000, "pallets": 16},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
    "BUS (10ep)": {"l": 450, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
}

with st.sidebar:
    if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="display:block;margin:auto;max-width:180px;margin-bottom:20px;">', unsafe_allow_html=True)
    st.header("1. POJAZD")
    v_type = st.selectbox("TYP FLOTY:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    
    st.divider()
    
    st.header("2. DODAJ ŁADUNEK")
    t1, t2 = st.tabs(["BAZA", "WŁASNY"])
    with t1:
        sel = st.selectbox("PRODUKT:", [p['name'] for p in prods_base], index=None)
        qty = st.number_input("SZTUK:", min_value=1, value=1, key="db_qty")
        if st.button("DODAJ PRODUKT"):
            if sel:
                p_d = next(p for p in prods_base if p['name'] == sel)
                ex = next((i for i in st.session_state.cargo if i['name'] == sel), None)
                if ex: ex['total_qty'] += qty
                else: st.session_state.cargo.append({"name": sel, "total_qty": qty, **p_d})
                st.rerun()
    with t2:
        c_n = st.text_input("NAZWA:")
        c_l = st.number_input("DŁ [cm]:", 120); c_w = st.number_input("SZER [cm]:", 80); c_h = st.number_input("WYS [cm]:", 100)
        c_wg = st.number_input("WAGA [kg]:", 100); c_qt = st.number_input("SZTUK:", 1, key="c_qty")
        if st.button("DODAJ NIESTANDARDOWY") and c_n:
            st.session_state.cargo.append({"name": c_n, "length": c_l, "width": c_w, "height": c_h, "weight": c_wg, "total_qty": c_qt, "canStack": False, "itemsPerCase": 1})
            st.session_state.colors[c_n] = "#D4A373"; st.rerun()
            
    if st.button("RESTART SYSTEMU"): st.session_state.cargo = []; st.rerun()

st.title("VORTEZA STACK")

if st.session_state.cargo:
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("MANIFEST")
    df = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty']]
    ed_df = st.data_editor(df, disabled=["name"], hide_index=True, use_container_width=True)
    if not ed_df.equals(df):
        for idx, row in ed_df.iterrows(): st.session_state.cargo[idx]['total_qty'] = row['total_qty']
        st.session_state.cargo = [i for i in st.session_state.cargo if i['total_qty'] > 0]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Przygotowanie skrzyń do algorytmu
    cases = []
    for e in st.session_state.cargo:
        for _ in range(math.ceil(e['total_qty'] / e.get('itemsPerCase', 1))): cases.append(e.copy())
    
    fleet = pack_logic(cases, veh)
    for i, res in enumerate(fleet):
        with st.expander(f"🚛 POJAZD #{i+1} - ANALIZA ZAŁADUNKU", expanded=True):
            c1, c2 = st.columns([2.2, 1])
            with c1: st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.colors), use_container_width=True)
            with c2:
                # OBLICZENIA
                a_used = sum(s['l']*s['w'] for s in res['stacks'])
                a_total = veh['l'] * veh['w']
                v_used = sum(it['length']*it['width']*it['height'] for s in res['stacks'] for it in s['items'])
                v_total = veh['l'] * veh['w'] * veh['h']
                ldm = round(max([s['x'] + s['l'] for s in res['stacks']]) / 100, 2) if res['stacks'] else 0
                
                st.markdown("### STATYSTYKI")
                st.metric("METRY BIEŻĄCE (LDM)", f"{ldm} m")
                st.metric("ZAJĘTE EP", f"{round(a_used/9600, 1)} / {veh['pallets']}")
                
                st.write(f"**POWIERZCHNIA:** {round(a_used/10000, 2)} m² ({round(a_used/a_total*100, 1)}%)")
                st.progress(min(a_used/a_total, 1.0))
                
                st.write(f"**OBJĘTOŚĆ:** {round(v_used/1000000, 2)} m³ ({round(v_used/v_total*100, 1)}%)")
                st.progress(min(v_used/v_total, 1.0))
                
                st.write(f"**WAGA:** {res['weight']} / {veh['weight']} kg")
                st.progress(min(res['weight']/veh['weight'], 1.0))
                
                st.markdown("---")
                st.write("**SKŁAD JEDNOSTKOWY:**")
                st.table(pd.Series([it['name'] for s in res['stacks'] for it in s['items']]).value_counts().reset_index().rename(columns={"index": "PRODUKT", 0: "SZT"}))
else:
    st.info("System VORTEZA STACK gotowy do pracy. Dodaj ładunek w panelu bocznym.")
