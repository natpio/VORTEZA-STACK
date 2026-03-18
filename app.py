import streamlit as st
import pandas as pd
import json
import requests
import base64
import math
import plotly.graph_objects as go

# =========================================================
# 1. KONFIGURACJA ZASOBÓW I AUTORYZACJI
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
LOGO_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png")

# =========================================================
# 2. STYLIZACJA INTERFEJSU (VORTEZA DARK PRO)
# =========================================================
st.set_page_config(page_title="VORTEZA STACK PRO", layout="wide", page_icon="🚚")

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
                background-color: rgba(0, 0, 0, 0.9) !important; 
                border-right: 2px solid var(--v-copper);
                backdrop-filter: blur(12px);
            }}
            .stApp {{ color: #FFFFFF; font-family: 'Montserrat', sans-serif; }}
            .vorteza-card {{
                background: var(--v-bg-panel); padding: 20px; border-radius: 2px;
                border: 1px solid rgba(181, 136, 99, 0.2); border-left: 6px solid var(--v-copper);
                margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}
            th {{ background-color: var(--v-copper) !important; color: black !important; text-transform: uppercase; }}
            td {{ background-color: #111 !important; color: #EEE !important; }}
            .stMetric {{ background: #000; padding: 10px; border: 1px solid #222; border-bottom: 3px solid var(--v-copper); }}
            h1, h2, h3 {{ color: var(--v-copper) !important; text-transform: uppercase; letter-spacing: 1px; }}
            .stButton > button {{
                background-color: transparent; color: var(--v-copper); border: 2px solid var(--v-copper);
                font-weight: 700; text-transform: uppercase; width: 100%; border-radius: 0px;
            }}
            .stButton > button:hover {{ background-color: var(--v-copper); color: #000; }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. ZAAWANSOWANA LOGIKA PAKOWANIA (ROTACJA + STOSY)
# =========================================================
def pack_logic_pro(items, veh, margin=2):
    v_l, v_w, v_h = veh['l'] - margin, veh['w'] - margin, veh['h']
    remaining = sorted(items, key=lambda x: x['length'] * x['width'], reverse=True)
    fleet = []

    while remaining:
        placed_stacks, still_to_pack = [], []
        curr_x, curr_y, max_l_in_row, total_w = 0, 0, 0, 0
        
        for item in remaining:
            if total_w + item['weight'] > veh['weight']:
                still_to_pack.append(item); continue
            
            packed = False
            # Próba rotacji (prosto i 90 stopni)
            for l, w in [(item['length'], item['width']), (item['width'], item['length'])]:
                # 1. Sprawdź czy wejdzie na wysokość w istniejący stos
                if item.get('canStack', True):
                    for s in placed_stacks:
                        if s['x'] == curr_x and s['y'] == curr_y and s['l'] == l and s['w'] == w:
                            current_h = sum(i['height'] for i in s['items'])
                            if current_h + item['height'] <= v_h:
                                s['items'].append(item); total_w += item['weight']; packed = True; break
                if packed: break
                
                # 2. Jeśli nie, spróbuj postawić obok w tym samym rzędzie
                if curr_y + w <= v_w and curr_x + l <= v_l:
                    placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': l, 'w': w, 'items': [item]})
                    curr_y += w; max_l_in_row = max(max_l_in_row, l); total_w += item['weight']; packed = True; break
                
                # 3. Jeśli nie mieści się w rzędzie, otwórz nowy rząd
                elif curr_x + max_l_in_row + l <= v_l:
                    curr_x += max_l_in_row; curr_y = 0; max_l_in_row = l
                    placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': l, 'w': w, 'items': [item]})
                    curr_y += w; total_w += item['weight']; packed = True; break
            
            if not packed: still_to_pack.append(item)
            
        if not placed_stacks: break
        fleet.append({"stacks": placed_stacks, "weight": total_w})
        remaining = still_to_pack
    return fleet

# =========================================================
# 4. WIZUALIZACJA 3D (COG + ETYKIETY)
# =========================================================
def draw_3d_pro(stacks, veh, color_map):
    fig = go.Figure()
    # Obrys naczepy
    fig.add_trace(go.Scatter3d(
        x=[0, veh['l'], veh['l'], 0, 0, 0, veh['l'], veh['l'], 0, 0],
        y=[0, 0, veh['w'], veh['w'], 0, 0, 0, veh['w'], veh['w'], 0],
        z=[0, 0, 0, 0, 0, veh['h'], veh['h'], veh['h'], veh['h'], veh['h']],
        mode='lines', line=dict(color='#B58863', width=4), name='Auto'
    ))

    sum_mass_x, total_w = 0, 0
    for s in stacks:
        z_curr = 0
        for it in s['items']:
            x0, y0, z0, dx, dy, dz = s['x'], s['y'], z_curr, s['l'], s['w'], it['height']
            # Obliczenia środka ciężkości
            sum_mass_x += (x0 + dx/2) * it['weight']
            total_w += it['weight']
            
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color_map.get(it['name'], "#B58863"), opacity=0.85, flatshading=True,
                hoverinfo="text", text=f"<b>{it['name']}</b><br>Waga: {it['weight']}kg<br>Wym: {dx}x{dy}x{dz}"
            ))
            z_curr += dz

    # Wskaźnik COG (Center of Gravity)
    if total_w > 0:
        cog_x = sum_mass_x / total_w
        fig.add_trace(go.Scatter3d(x=[cog_x], y=[veh['w']/2], z=[10], mode='markers', marker=dict(color='red', size=8), name="COG"))
        
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=600)
    return fig, cog_x if total_w > 0 else 0

# =========================================================
# 5. GŁÓWNA APLIKACJA
# =========================================================
apply_vorteza_theme()
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="width:100%;margin-bottom:30px;">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("LOGOWANIE SYSTEMOWE")
        pwd = st.text_input("HASŁO:", type="password")
        if st.button("WEJDŹ") and pwd == MASTER_PASSWORD: st.session_state.auth = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Konfiguracja floty
VEHICLES = {
    "Standard FTL (13.6m)": {"l": 1360, "w": 245, "h": 270, "weight": 24000, "pallets": 33},
    "Jumbo / Mega": {"l": 1360, "w": 245, "h": 300, "weight": 22000, "pallets": 33},
    "Solówka 7.2m": {"l": 720, "w": 245, "h": 250, "weight": 7000, "pallets": 18},
    "Bus 10ep": {"l": 485, "w": 220, "h": 240, "weight": 1100, "pallets": 10},
}

if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state: st.session_state.colors = {}

with st.sidebar:
    if LOGO_B64: st.image(base64.b64decode(LOGO_B64), width=150)
    st.header("1. PARAMETRY")
    v_type = st.selectbox("POJAZD:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    margin = st.slider("LUZ OPERACYJNY (cm):", 0, 15, 3)
    
    st.divider()
    st.header("2. DODAJ ŁADUNEK")
    c_n = st.text_input("NAZWA:")
    col_l, col_w = st.columns(2)
    with col_l: c_l = st.number_input("DŁ [cm]:", value=120)
    with col_w: c_w = st.number_input("SZER [cm]:", value=80)
    col_h, col_wg = st.columns(2)
    with col_h: c_h = st.number_input("WYS [cm]:", value=100)
    with col_wg: c_wg = st.number_input("WAGA [kg]:", value=200)
    col_q, col_i = st.columns(2)
    with col_q: c_qt = st.number_input("SZTUK:", min_value=1, value=1)
    with col_i: c_ipc = st.number_input("SZT/PAL:", min_value=1, value=1)
    
    can_s = st.checkbox("PIĘTROWALNE?", value=True)
    
    if st.button("DODAJ DO PLANU") and c_n:
        st.session_state.cargo.append({
            "name": c_n, "length": c_l, "width": c_w, "height": c_h, 
            "weight": c_wg, "total_qty": c_qt, "itemsPerCase": c_ipc, "canStack": can_s
        })
        if c_n not in st.session_state.colors:
            st.session_state.colors[c_n] = ["#B58863", "#D4A373", "#967052", "#A68A64"][len(st.session_state.colors)%4]
        st.rerun()

    st.divider()
    if st.button("RESTART"): st.session_state.cargo = []; st.rerun()
    if st.button("WYLOGUJ"): st.session_state.auth = False; st.rerun()

st.title("VORTEZA STACK PRO")

if st.session_state.cargo:
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("MANIFEST ZAŁADUNKOWY (EDYCYJNY)")
    
    df_temp = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty', 'itemsPerCase', 'canStack']]
    df_temp['JEDNOSTKI'] = df_temp.apply(lambda x: math.ceil(x['total_qty']/x['itemsPerCase']), axis=1)
    
    edited_df = st.data_editor(df_temp, hide_index=True, use_container_width=True)
    
    # Obsługa zmian i usuwania (ilość 0 = usunięcie)
    if not edited_df.equals(df_temp):
        new_cargo = []
        for idx, row in edited_df.iterrows():
            if row['total_qty'] > 0:
                orig = next(i for i in st.session_state.cargo if i['name'] == row['name'])
                orig.update({'total_qty': row['total_qty'], 'itemsPerCase': max(1, row['itemsPerCase']), 'canStack': row['canStack']})
                new_cargo.append(orig)
        st.session_state.cargo = new_cargo
        st.rerun()
        
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("POBIERZ LISTĘ (CSV)", csv, "vorteza_manifest.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

    # Przygotowanie jednostek
    all_units = []
    for item in st.session_state.cargo:
        num = math.ceil(item['total_qty'] / item['itemsPerCase'])
        for _ in range(num): all_units.append(item.copy())
    
    fleet = pack_logic_pro(all_units, veh, margin)
    
    for i, res in enumerate(fleet):
        with st.expander(f"🚛 POJAZD #{i+1} - ANALIZA ROZMIESZCZENIA", expanded=True):
            viz_col, stat_col = st.columns([2, 1])
            fig, cog_x = draw_3d_pro(res['stacks'], veh, st.session_state.colors)
            
            with viz_col:
                st.plotly_chart(fig, use_container_width=True)
            
            with stat_col:
                st.markdown("### STATYSTYKI")
                ldm = round(max([s['x'] + s['l'] for s in res['stacks']]) / 100, 2) if res['stacks'] else 0
                st.metric("METRY BIEŻĄCE (LDM)", f"{ldm} m")
                
                # Balans osi
                front_load = round((1 - cog_x/veh['l']) * 100, 1)
                st.write(f"**BALANS MASY:** PRZÓD {front_load}% | TYŁ {100-front_load}%")
                if front_load < 40 or front_load > 65:
                    st.error("⚠️ UWAGA: Niewłaściwy nacisk na osie!")
                
                st.write(f"**WAGA:** {res['weight']} / {veh['weight']} kg")
                st.progress(min(res['weight']/veh['weight'], 1.0))
                
                area_u = sum(s['l']*s['w'] for s in res['stacks'])
                st.write(f"**POWIERZCHNIA:** {round(area_u/(veh['l']*veh['w'])*100, 1)}%")
                st.progress(min(area_u/(veh['l']*veh['w']), 1.0))
                
                st.write("**SKŁAD POJAZDU:**")
                st.table(pd.Series([it['name'] for s in res['stacks'] for it in s['items']]).value_counts())
else:
    st.info("System VORTEZA STACK PRO gotowy. Dodaj towary, aby wygenerować plan załadunku.")
