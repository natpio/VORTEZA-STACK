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

# Adresy plików z repozytorium
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
# 2. DEFINICJA POJAZDÓW I KOLORÓW
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
    bg_overlay = "linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85))" # Mocniejsze przyciemnienie
    
    bg_css = f"""
        background: {bg_overlay}, url("data:image/jpg;base64,{BG_B64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """ if BG_B64 else "background-color: #0E0E0E;"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            
            :root {{
                --v-copper: #B58863;
                --v-text: #FFFFFF;
                --v-panel: rgba(10, 10, 10, 0.9);
            }}

            /* Kontener Główny */
            [data-testid="stAppViewContainer"] {{
                {bg_css}
            }}

            [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{
                background-color: transparent !important;
            }}

            /* Poprawa czytelności czcionki */
            .stApp {{
                color: var(--v-text);
                font-family: 'Montserrat', sans-serif;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.8); /* Cień pod tekstem */
            }}

            /* Sidebar */
            [data-testid="stSidebar"] {{
                background-color: rgba(5, 5, 5, 0.98) !important;
                border-right: 2px solid var(--v-copper);
            }}

            /* Karty i Panele */
            .vorteza-card {{
                background: var(--v-panel);
                padding: 25px;
                border-radius: 4px;
                border: 1px solid rgba(181, 136, 99, 0.4);
                border-left: 6px solid var(--v-copper);
                backdrop-filter: blur(12px);
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}

            h1, h2, h3, .stSubheader {{ 
                color: var(--v-copper) !important; 
                text-transform: uppercase; 
                letter-spacing: 2.5px; 
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
            }}
            
            label p {{ /* Etykiety pól inputów */
                color: #FFFFFF !important;
                font-weight: 600 !important;
                font-size: 1.1rem !important;
            }}

            .sidebar-logo {{
                display: block;
                margin: 0 auto 30px auto;
                max-width: 220px;
                filter: drop-shadow(0 0 10px rgba(181, 136, 99, 0.3));
            }}

            /* Metryki */
            [data-testid="stMetricValue"] {{
                color: var(--v-copper) !important;
                font-weight: 700 !important;
            }}
            
            .stMetric {{ 
                background: rgba(0,0,0,0.7); 
                padding: 15px; 
                border-radius: 4px; 
                border-bottom: 3px solid var(--v-copper); 
            }}
            
            /* Przyciski */
            .stButton > button {{
                background-color: transparent; 
                color: var(--v-copper); 
                border: 2px solid var(--v-copper);
                font-weight: 700;
                text-transform: uppercase; 
                width: 100%; 
                transition: 0.3s ease;
                padding: 10px;
            }}
            .stButton > button:hover {{ 
                background-color: var(--v-copper); 
                color: #000000; 
                box-shadow: 0 0 15px rgba(181, 136, 99, 0.4);
            }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 4. LOGIKA DANYCH GITHUB
# =========================================================
def get_products():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content = resp.json()
            return json.loads(base64.b64decode(content['content']).decode('utf-8'))
    except:
        pass
    return []

def pack_logic(items, veh):
    # Sortowanie po powierzchni (największe najpierw)
    remaining = sorted(items, key=lambda x: x['length']*x['width'], reverse=True)
    fleet = []
    
    while remaining:
        placed_stacks = []
        still_to_pack = []
        curr_w, curr_x, curr_y, max_w_row = 0, 0, 0, 0
        
        for item in remaining:
            if curr_w + item['weight'] > veh['weight']:
                still_to_pack.append(item)
                continue
            
            added = False
            # Próba sztaplowania
            if item.get('canStack', True):
                for s in placed_stacks:
                    curr_h = sum(i['height'] for i in s['items'])
                    if (s['l'] == item['length'] and s['w'] == item['width'] and (curr_h + item['height']) <= veh['h']):
                        s['items'].append(item)
                        curr_w += item['weight']
                        added = True
                        break
            
            if not added:
                # Nowy rząd w naczepie
                if curr_y + item['width'] > veh['w']:
                    curr_y, curr_x = 0, curr_x + max_w_row
                    max_w_row = 0
                
                # Czy zmieści się na długość
                if curr_x + item['length'] <= veh['l']:
                    placed_stacks.append({
                        'x': curr_x, 'y': curr_y, 'l': item['length'], 
                        'w': item['width'], 'items': [item]
                    })
                    curr_y += item['width']
                    max_w_row = max(max_w_row, item['length'])
                    curr_w += item['weight']
                else:
                    still_to_pack.append(item)
        
        if not placed_stacks: break
        fleet.append({"stacks": placed_stacks, "weight": curr_w})
        remaining = still_to_pack
    return fleet

def draw_3d_fleet(stacks, veh, color_map):
    fig = go.Figure()
    # Obrys pojazdu
    fig.add_trace(go.Scatter3d(
        x=[0, veh['l'], veh['l'], 0, 0, 0, veh['l'], veh['l'], 0, 0],
        y=[0, 0, veh['w'], veh['w'], 0, 0, 0, veh['w'], veh['w'], 0],
        z=[0, 0, 0, 0, 0, veh['h'], veh['h'], veh['h'], veh['h'], veh['h']],
        mode='lines', line=dict(color='#B58863', width=4), name='Pojazd'
    ))
    
    for s in stacks:
        z_offset = 0
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], z_offset
            dx, dy, dz = item['length'], item['width'], item['height']
            
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color_map.get(item['name'], "#B58863"), 
                opacity=0.9, flatshading=True, name=item['name']
            ))
            z_offset += item['height']
            
    fig.update_layout(
        scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0,r=0,b=0,t=0),
        height=600
    )
    return fig

# =========================================================
# 5. CYKL ŻYCIA APLIKACJI
# =========================================================
apply_vorteza_theme()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- EKRAN LOGOWANIA ---
if not st.session_state.authenticated:
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.write("") # Odstęp
        if LOGO_B64:
            st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("SYSTEM VORTEZA STACK")
        pwd = st.text_input("Hasło dostępowe:", type="password")
        if st.button("AUTORYZACJA"):
            if pwd == MASTER_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- GŁÓWNA APLIKACJA ---
products_raw = get_products()
if 'cargo_list' not in st.session_state: st.session_state.cargo_list = []
if 'color_map' not in st.session_state:
    st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(products_raw)}

with st.sidebar:
    if LOGO_B64:
        st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" class="sidebar-logo">', unsafe_allow_html=True)
    
    st.header("1. Wybór Floty")
    v_type = st.selectbox("TYP POJAZDU:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    
    st.divider()
    
    st.header("2. Dodaj ładunek")
    sel_name = st.selectbox("SZUKAJ PRODUKTU:", [p['name'] for p in products_raw], index=None, placeholder="Wpisz nazwę...")
    qty = st.number_input("LICZBA SZTUK:", min_value=1, value=1)
    
    if st.button("DODAJ DO MANIFESTU") and sel_name:
        p_data = next(p for p in products_raw if p['name'] == sel_name)
        existing = next((item for item in st.session_state.cargo_list if item['name'] == sel_name), None)
        if existing:
            existing['total_qty'] += qty
        else:
            st.session_state.cargo_list.append({"name": sel_name, "total_qty": qty, **p_data})
        st.rerun()
    
    if st.button("RESETUJ CAŁY PLAN"):
        st.session_state.cargo_list = []
        st.rerun()

# Panel Główny
st.title("VORTEZA STACK")

if st.session_state.cargo_list:
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("📋 Aktywny Manifest")
    
    # Konwersja do DataFrame dla edytora
    df_manifest = pd.DataFrame(st.session_state.cargo_list)[['name', 'total_qty']]
    edited_df = st.data_editor(
        df_manifest, 
        column_config={"name": "Produkt", "total_qty": "Sztuk (edytuj)"},
        disabled=["name"], 
        hide_index=True, 
        use_container_width=True
    )
    
    # Synchronizacja zmian z edytora
    if not edited_df.equals(df_manifest):
        for idx, row in edited_df.iterrows():
            st.session_state.cargo_list[idx]['total_qty'] = row['total_qty']
        st.session_state.cargo_list = [i for i in st.session_state.cargo_list if i['total_qty'] > 0]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Przygotowanie fizycznych jednostek do pakowania (uwzględniając itemsPerCase)
    all_physical_items = []
    for entry in st.session_state.cargo_list:
        items_per_case = entry.get('itemsPerCase', 1)
        num_cases = math.ceil(entry['total_qty'] / items_per_case)
        for _ in range(num_cases):
            all_physical_items.append(entry.copy())
    
    # Obliczanie pakowania
    fleet_results = pack_logic(all_physical_items, veh)

    # Wyświetlanie wyników
    for i, transport in enumerate(fleet_results):
        with st.expander(f"🚛 POJAZD #{i+1} | Załadunek: {transport['weight']} kg", expanded=True):
            col_viz, col_data = st.columns([2.5, 1])
            
            with col_viz:
                st.plotly_chart(draw_3d_fleet(transport['stacks'], veh, st.session_state.color_map), use_container_width=True)
            
            with col_data:
                st.markdown("### Raport")
                total_area = sum(s['l']*s['w'] for s in transport['stacks'])
                ep_usage = round(total_area / 9600, 1) # 1 EP = 80x120 = 9600 cm2
                
                st.metric("Wykorzystanie EP", f"{ep_usage} / {veh['pallets']}")
                st.metric("Masa całkowita", f"{transport['weight']} kg")
                
                st.write("**Stan ładowności:**")
                st.progress(min(transport['weight'] / veh['weight'], 1.0))
                
                # Zliczanie produktów w tym konkretnym aucie
                this_v_items = [it['name'] for s in transport['stacks'] for it in s['items']]
                st.write("**Skład pojazdu:**")
                summary_df = pd.Series(this_v_items).value_counts().reset_index()
                summary_df.columns = ['Produkt', 'Skrzyń']
                st.table(summary_df)
else:
    st.info("System gotowy. Dodaj produkty z panelu bocznego, aby wygenerować plan załadunku.")
