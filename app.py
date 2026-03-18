import streamlit as st
import pandas as pd
import json
import requests
import base64
import math
import plotly.graph_objects as go
from io import BytesIO

# =========================================================
# 1. KONFIGURACJA I ZASOBY
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
# 2. STYLIZACJA (VORTEZA DARK THEME)
# =========================================================
st.set_page_config(page_title="VORTEZA STACK PRO", layout="wide", page_icon="🚚")

def apply_theme():
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
                background: var(--v-bg-panel); padding: 20px; border-radius: 4px;
                border: 1px solid rgba(181, 136, 99, 0.2); border-left: 5px solid var(--v-copper);
                margin-bottom: 20px;
            }}
            th {{ background-color: var(--v-copper) !important; color: black !important; }}
            .stMetric {{ background: #111; padding: 10px; border: 1px solid #222; border-radius: 4px; }}
            h1, h2, h3 {{ color: var(--v-copper) !important; text-transform: uppercase; }}
            .stButton > button {{ border-radius: 0px; border: 2px solid var(--v-copper); background: transparent; color: var(--v-copper); font-weight: bold; }}
            .stButton > button:hover {{ background: var(--v-copper); color: black; }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. ZAAWANSOWANA LOGIKA PAKOWANIA (Z ROTACJĄ)
# =========================================================
def pack_logic_pro(items, veh, margin=2):
    # Uwzględnienie marginesu (luzu)
    v_l = veh['l'] - margin
    v_w = veh['w'] - margin
    v_h = veh['h']
    
    remaining = sorted(items, key=lambda x: x['length']*x['width'], reverse=True)
    fleet = []
    
    while remaining:
        placed_stacks = []
        still_to_pack = []
        curr_w, curr_x, curr_y, max_l_row = 0, 0, 0, 0
        
        for item in remaining:
            if curr_w + item['weight'] > veh['weight']:
                still_to_pack.append(item)
                continue
            
            # Próba dopasowania (z rotacją)
            it_l, it_w = item['length'], item['width']
            can_fit = False
            
            # Sprawdź czy wejdzie prosto lub obrócone
            for l, w in [(it_l, it_w), (it_w, it_l)]:
                if curr_y + w <= v_w and curr_x + l <= v_l:
                    # Sprawdź stackowanie w istniejących stosach
                    stacked = False
                    if item.get('canStack', True):
                        for s in placed_stacks:
                            if s['l'] == l and s['w'] == w and s['x'] == curr_x and s['y'] == curr_y:
                                if sum(i['height'] for i in s['items']) + item['height'] <= v_h:
                                    s['items'].append(item); curr_w += item['weight']; stacked = True; break
                    
                    if not stacked:
                        if curr_y + w <= v_w:
                            placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': l, 'w': w, 'items': [item]})
                            curr_y += w; max_l_row = max(max_l_row, l); curr_w += item['weight']
                        else:
                            curr_y = 0; curr_x += max_l_row; max_l_row = 0
                            if curr_x + l <= v_l:
                                placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': l, 'w': w, 'items': [item]})
                                curr_y += w; max_l_row = max(max_l_row, l); curr_w += item['weight']
                            else: still_to_pack.append(item)
                    can_fit = True; break
            
            if not can_fit: still_to_pack.append(item)
            
        if not placed_stacks: break
        fleet.append({"stacks": placed_stacks, "weight": curr_w})
        remaining = still_to_pack
    return fleet

# =========================================================
# 4. WIZUALIZACJA 3D (Z ETYKIETAMI I ŚRODKIEM CIĘŻKOŚCI)
# =========================================================
def draw_3d_pro(stacks, veh, color_map):
    fig = go.Figure()
    
    # Obrys naczepy
    fig.add_trace(go.Scatter3d(
        x=[0, veh['l'], veh['l'], 0, 0, 0, veh['l'], veh['l'], 0, 0],
        y=[0, 0, veh['w'], veh['w'], 0, 0, 0, veh['w'], veh['w'], 0],
        z=[0, 0, 0, 0, 0, veh['h'], veh['h'], veh['h'], veh['h'], veh['h']],
        mode='lines', line=dict(color='#B58863', width=4), name='Naczepa'
    ))

    total_mass_x = 0
    total_weight = 0

    for s in stacks:
        z_p = 0
        for it in s['items']:
            x0, y0, z0, dx, dy, dz = s['x'], s['y'], z_p, s['l'], s['w'], it['height']
            
            # Środek ciężkości ładunku
            total_mass_x += (x0 + dx/2) * it['weight']
            total_weight += it['weight']

            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color_map.get(it['name'], "#B58863"), opacity=0.85,
                hoverinfo="text", text=f"PRODUKT: {it['name']}<br>WAGA: {it['weight']}kg<br>WYM: {dx}x{dy}x{dz}"
            ))
            z_p += dz

    # Wskaźnik środka ciężkości (COG)
    if total_weight > 0:
        cog_x = total_mass_x / total_weight
        fig.add_trace(go.Scatter3d(
            x=[cog_x], y=[veh['w']/2], z=[5],
            mode='markers+text', marker=dict(color='red', size=10),
            text=["ŚRODEK CIĘŻKOŚCI"], textposition="top center", name="COG"
        ))

    fig.update_layout(scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0))
    return fig, total_weight, total_mass_x / total_weight if total_weight > 0 else 0

# =========================================================
# 5. UI I GŁÓWNA PĘTLA
# =========================================================
apply_theme()
if "auth" not in st.session_state: st.session_state.auth = False

# --- LOGOWANIE ---
if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="width:450px; display:block; margin:auto; margin-bottom:30px;">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("Autoryzacja Systemu Logistycznego")
        pwd = st.text_input("Hasło dostępu:", type="password")
        if st.button("ZALOGUJ") and pwd == MASTER_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- DANE ---
VEHICLES = {
    "FTL (Standard)": {"l": 1360, "w": 245, "h": 270, "weight": 24000, "pallets": 33},
    "Jumbo": {"l": 1540, "w": 245, "h": 300, "weight": 22000, "pallets": 38},
    "Solówka 7.5t": {"l": 720, "w": 245, "h": 245, "weight": 7000, "pallets": 18},
}

if 'cargo' not in st.session_state: st.session_state.cargo = []

with st.sidebar:
    if LOGO_B64: st.image(base64.b64decode(LOGO_B64), width=150)
    st.header("USTAWIENIA POJAZDU")
    v_type = st.selectbox("TYP POJAZDU:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    margin = st.slider("LUZ ŁADUNKOWY (cm):", 0, 10, 2)
    
    st.divider()
    st.header("DODAJ TOWAR")
    c_n = st.text_input("NAZWA/ID:")
    col1, col2 = st.columns(2)
    with col1:
        c_l = st.number_input("DŁ [cm]:", value=120)
        c_h = st.number_input("WYS [cm]:", value=100)
        c_qt = st.number_input("SZTUK:", value=1)
    with col2:
        c_w = st.number_input("SZER [cm]:", value=80)
        c_wg = st.number_input("WAGA [kg]:", value=500)
        c_ipc = st.number_input("SZT/PALETA:", value=1)
    
    can_s = st.checkbox("PIĘTROWALNE?", value=True)
    
    if st.button("DODAJ DO MANIFESTU") and c_n:
        st.session_state.cargo.append({
            "name": c_n, "length": c_l, "width": c_w, "height": c_h, 
            "weight": c_wg, "total_qty": c_qt, "itemsPerCase": c_ipc, "canStack": can_s
        })
        st.rerun()
    
    if st.button("WYLOGUJ"):
        st.session_state.auth = False
        st.rerun()

# --- PANEL GŁÓWNY ---
st.title("VORTEZA STACK PRO")

if st.session_state.cargo:
    # Manifest i Edycja
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("AKTUALNY MANIFEST")
    df_manifest = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty', 'itemsPerCase', 'canStack']]
    
    # Dodanie kolumny obliczeniowej do tabeli (tylko podgląd)
    df_manifest['PALETY'] = df_manifest.apply(lambda x: math.ceil(x['total_qty']/x['itemsPerCase']), axis=1)
    
    edited_df = st.data_editor(df_manifest, key="editor", hide_index=True, use_container_width=True)
    
    # Obsługa usuwania i edycji
    if not edited_df.equals(df_manifest):
        new_cargo = []
        for idx, row in edited_df.iterrows():
            if row['total_qty'] > 0:
                orig = next(i for i in st.session_state.cargo if i['name'] == row['name'])
                orig.update({'total_qty': row['total_qty'], 'itemsPerCase': max(1, row['itemsPerCase']), 'canStack': row['canStack']})
                new_cargo.append(orig)
        st.session_state.cargo = new_cargo
        st.rerun()
    
    # Eksport CSV
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("POBIERZ LISTĘ ZAŁADUNKOWĄ (CSV)", data=csv, file_name="manifest_vorteza.csv", mime="text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

    # Obliczenia brył
    all_cases = []
    for item in st.session_state.cargo:
        num = math.ceil(item['total_qty'] / item['itemsPerCase'])
        for _ in range(num): all_cases.append(item.copy())
    
    # Pakowanie
    fleet = pack_logic_pro(all_cases, veh, margin)
    
    # Wyświetlanie wyników
    for i, res in enumerate(fleet):
        with st.expander(f"🚛 PLAN ZAŁADUNKU #{i+1}", expanded=True):
            col_viz, col_stat = st.columns([2, 1])
            
            fig, weight, cog_x = draw_3d_pro(res['stacks'], veh, {})
            
            with col_viz:
                st.plotly_chart(fig, use_container_width=True)
            
            with col_stat:
                st.markdown("### ANALIZA TECHNICZNA")
                ldm = round(max([s['x'] + s['l'] for s in res['stacks']]) / 100, 2) if res['stacks'] else 0
                st.metric("METRY BIEŻĄCE (LDM)", f"{ldm} m")
                
                # Rozkład masy
                front_pct = round((1 - cog_x/veh['l']) * 100, 1)
                st.write(f"**ROZKŁAD MASY:** Przód {front_pct}% | Tył {100-front_pct}%")
                if front_pct < 40 or front_pct > 70:
                    st.warning("⚠️ Nierównomierny rozkład masy! Ryzyko przeciążenia osi.")
                
                st.write(f"**WAGA CAŁKOWITA:** {weight} / {veh['weight']} kg")
                st.progress(min(weight/veh['weight'], 1.0))
                
                vol_used = sum(it['length']*it['width']*it['height'] for s in res['stacks'] for it in s['items'])
                vol_total = veh['l']*veh['w']*veh['h']
                st.write(f"**WYPEŁNIENIE KUBATURY:** {round(vol_used/vol_total*100, 1)}%")
                st.progress(min(vol_used/vol_total, 1.0))
                
                st.write("**LISTA JEDNOSTEK:**")
                st.table(pd.Series([it['name'] for s in res['stacks'] for it in s['items']]).value_counts())

else:
    st.info("System gotowy. Dodaj towary w panelu bocznym, aby rozpocząć optymalizację.")
