import streamlit as st
import pandas as pd
import json
import requests
import base64
import math
import plotly.graph_objects as go
from io import BytesIO

# =========================================================
# 1. KONFIGURACJA ZASOBÓW I GITHUB
# =========================================================
try:
    # Pobieranie tokena i hasła z Streamlit Secrets
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
    """Pobiera obraz z GitHub i konwertuje do base64 dla CSS/HTML."""
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except:
        return None
    return None

# Zasoby graficzne
BG_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/bg_vorteza.jpg")
LOGO_B64 = get_base64_img(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/logo_vorteza.png")

# =========================================================
# 2. STYLIZACJA INTERFEJSU (VORTEZA STACK DARK PRO)
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
            
            [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{ background-color: transparent !important; }}
            .stApp {{ color: #FFFFFF; font-family: 'Montserrat', sans-serif; }}
            
            .vorteza-card {{
                background: var(--v-bg-panel); padding: 25px; border-radius: 2px;
                border: 1px solid rgba(181, 136, 99, 0.2); border-left: 8px solid var(--v-copper);
                margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            }}
            
            th {{ background-color: var(--v-copper) !important; color: black !important; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem !important; }}
            td {{ background-color: #111 !important; color: #EEE !important; border-bottom: 1px solid #222 !important; }}
            
            .stMetric {{ background: #000; padding: 15px; border: 1px solid #222; border-bottom: 4px solid var(--v-copper); }}
            [data-testid="stMetricValue"] {{ color: #FFF !important; font-weight: 700; }}
            
            .stProgress > div > div > div > div {{ background-color: var(--v-copper) !important; }}
            h1, h2, h3 {{ color: var(--v-copper) !important; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; }}
            
            .stButton > button {{
                background-color: transparent; color: var(--v-copper); border: 2px solid var(--v-copper);
                font-weight: 700; text-transform: uppercase; width: 100%; border-radius: 0px; height: 3em;
            }}
            .stButton > button:hover {{ background-color: var(--v-copper); color: #000; box-shadow: 0 0 15px var(--v-copper); }}
            
            [data-testid="stExpander"] {{ background: rgba(10,10,10,0.8); border: 1px solid #333; }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. LOGIKA BIZNESOWA I PAKOWANIA
# =========================================================
def get_products():
    """Pobiera bazę produktów z JSON na GitHub."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()['content']).decode('utf-8')
            return json.loads(content)
    except:
        pass
    return []

def pack_logic_pro(items, veh, margin=2):
    """Algorytm First-Fit z rotacją 90 stopni i marginesem luzu."""
    v_l, v_w, v_h = veh['l'] - margin, veh['w'] - margin, veh['h']
    # Sortowanie po powierzchni podstawy (malejąco)
    remaining = sorted(items, key=lambda x: x['length'] * x['width'], reverse=True)
    fleet = []

    while remaining:
        placed_stacks, still_to_pack = [], []
        curr_x, curr_y, max_l_in_row, total_w = 0, 0, 0, 0
        
        for item in remaining:
            if total_w + item['weight'] > veh['weight']:
                still_to_pack.append(item); continue
            
            packed = False
            # Sprawdzenie orientacji: standardowa oraz obrócona o 90 stopni
            orientations = [(item['length'], item['width']), (item['width'], item['length'])]
            
            for l, w in orientations:
                # 1. Próba piętrowania w istniejących stosach w tym samym punkcie
                if item.get('canStack', True):
                    for s in placed_stacks:
                        if s['x'] == curr_x and s['y'] == curr_y and s['l'] == l and s['w'] == w:
                            current_h = sum(i['height'] for i in s['items'])
                            if current_h + item['height'] <= v_h:
                                s['items'].append(item); total_w += item['weight']; packed = True; break
                if packed: break
                
                # 2. Próba postawienia obok w rzędzie
                if curr_y + w <= v_w and curr_x + l <= v_l:
                    placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': l, 'w': w, 'items': [item]})
                    curr_y += w; max_l_in_row = max(max_l_in_row, l); total_w += item['weight']; packed = True; break
                
                # 3. Próba otwarcia nowego rzędu (przeskok w osi X)
                elif curr_x + max_l_in_row + l <= v_l:
                    curr_x += max_l_in_row; curr_y = 0; max_l_in_row = l
                    placed_stacks.append({'x': curr_x, 'y': curr_y, 'l': l, 'w': w, 'items': [item]})
                    curr_y += w; total_w += item['weight']; packed = True; break
            
            if not packed: still_to_pack.append(item)
            
        if not placed_stacks: break
        fleet.append({"stacks": placed_stacks, "weight": total_w})
        remaining = still_to_pack
    return fleet

def draw_3d_pro(stacks, veh, color_map):
    """Generuje model 3D naczepy z ładunkiem i wskaźnikiem COG."""
    fig = go.Figure()
    # Rysowanie klatki naczepy
    fig.add_trace(go.Scatter3d(
        x=[0, veh['l'], veh['l'], 0, 0, 0, veh['l'], veh['l'], 0, 0],
        y=[0, 0, veh['w'], veh['w'], 0, 0, 0, veh['w'], veh['w'], 0],
        z=[0, 0, 0, 0, 0, veh['h'], veh['h'], veh['h'], veh['h'], veh['h']],
        mode='lines', line=dict(color='#B58863', width=4), name='Naczepa'
    ))

    sum_mass_x, total_w = 0, 0
    for s in stacks:
        z_curr = 0
        for it in s['items']:
            x0, y0, z0, dx, dy, dz = s['x'], s['y'], z_curr, s['l'], s['w'], it['height']
            sum_mass_x += (x0 + dx/2) * it['weight']
            total_w += it['weight']
            
            # Tworzenie prostopadłościanu ładunku
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color_map.get(it['name'], "#B58863"), opacity=0.85, flatshading=True,
                hoverinfo="text", text=f"<b>{it['name']}</b><br>Waga: {it['weight']}kg<br>Wymiary: {dx}x{dy}x{dz}cm"
            ))
            z_curr += dz

    # Wskaźnik środka ciężkości (Center of Gravity)
    cog_x = 0
    if total_w > 0:
        cog_x = sum_mass_x / total_w
        fig.add_trace(go.Scatter3d(
            x=[cog_x], y=[veh['w']/2], z=[10],
            mode='markers', marker=dict(color='red', size=10, symbol='diamond'),
            name="Środek Ciężkości (COG)"
        ))
        
    fig.update_layout(
        scene=dict(aspectmode='data', bgcolor='rgba(0,0,0,0)', 
                   xaxis=dict(title="Długość (cm)"), yaxis=dict(title="Szerokość (cm)"), zaxis=dict(title="Wysokość (cm)")),
        paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=650,
        legend=dict(font=dict(color="white"))
    )
    return fig, cog_x

# =========================================================
# 4. GŁÓWNA APLIKACJA I UI
# =========================================================
apply_vorteza_theme()

# Zarządzanie sesją autoryzacji
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        if LOGO_B64: st.markdown(f'<img src="data:image/png;base64,{LOGO_B64}" style="width:100%; max-width:400px; display:block; margin:auto; margin-bottom:30px;">', unsafe_allow_html=True)
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("SYSTEM VORTEZA STACK")
        pwd = st.text_input("HASŁO DOSTĘPU:", type="password")
        if st.button("AUTORYZUJ") and pwd == MASTER_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- DANE POJAZDÓW ---
VEHICLES = {
    "Standard FTL (13.6m)": {"l": 1360, "w": 245, "h": 270, "weight": 24000, "pallets": 33},
    "Jumbo / Mega": {"l": 1360, "w": 245, "h": 300, "weight": 22000, "pallets": 33},
    "Zestaw (Pociąg drogowy)": {"l": 1540, "w": 245, "h": 300, "weight": 22000, "pallets": 38},
    "Solówka 7.2m": {"l": 720, "w": 245, "h": 250, "weight": 7000, "pallets": 18},
    "Bus 10ep": {"l": 485, "w": 220, "h": 240, "weight": 1100, "pallets": 10},
}

# --- STAN APLIKACJI ---
if 'cargo' not in st.session_state: st.session_state.cargo = []
if 'colors' not in st.session_state: st.session_state.colors = {}

prods_base = get_products()

# --- SIDEBAR: KONFIGURACJA ---
with st.sidebar:
    if LOGO_B64: st.image(base64.b64decode(LOGO_B64), width=180)
    st.header("1. PARAMETRY TRANSPORTU")
    v_type = st.selectbox("POJAZD DOCELOWY:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    margin = st.slider("LUZ OPERACYJNY (margines cm):", 0, 20, 3)
    
    st.divider()
    
    st.header("2. DODAJ DO ŁADUNKU")
    t1, t2 = st.tabs(["Z BAZY", "WŁASNY"])
    
    with t1:
        sel = st.selectbox("WYBIERZ PRODUKT:", [p['name'] for p in prods_base], index=None)
        q_b = st.number_input("SZTUK:", min_value=1, value=1, key="q_base")
        if st.button("DODAJ PRODUKT"):
            if sel:
                p_d = next(p for p in prods_base if p['name'] == sel)
                # Sprawdź czy już jest, by zsumować
                exists = next((i for i in st.session_state.cargo if i['name'] == sel), None)
                if exists: exists['total_qty'] += q_b
                else: 
                    new_i = p_d.copy()
                    new_i['total_qty'] = q_b
                    if 'itemsPerCase' not in new_i: new_i['itemsPerCase'] = 1
                    st.session_state.cargo.append(new_i)
                st.session_state.colors[sel] = "#B58863"
                st.rerun()

    with t2:
        c_n = st.text_input("NAZWA ŁADUNKU:")
        col_dim1, col_dim2 = st.columns(2)
        with col_dim1: 
            c_l = st.number_input("DŁ [cm]:", value=120)
            c_h = st.number_input("WYS [cm]:", value=100)
            c_qt = st.number_input("ŁĄCZNIE SZT:", min_value=1, value=1)
        with col_dim2: 
            c_w = st.number_input("SZER [cm]:", value=80)
            c_wg = st.number_input("WAGA [kg]:", value=200)
            c_ipc = st.number_input("SZT / PALETA:", min_value=1, value=1)
        
        can_s = st.checkbox("MOŻNA PIĘTROWAĆ?", value=True)
        if st.button("DODAJ NIESTANDARDOWY") and c_n:
            st.session_state.cargo.append({
                "name": c_n, "length": c_l, "width": c_w, "height": c_h, 
                "weight": c_wg, "total_qty": c_qt, "itemsPerCase": c_ipc, "canStack": can_s
            })
            st.session_state.colors[c_n] = "#D4A373"
            st.rerun()

    st.divider()
    if st.button("RESETUJ WSZYSTKO"): st.session_state.cargo = []; st.rerun()
    if st.button("WYLOGUJ (ZAKOŃCZ SESJĘ)"): st.session_state.auth = False; st.rerun()

# --- MAIN: ANALIZA I WIZUALIZACJA ---
st.title("VORTEZA STACK PRO")

if st.session_state.cargo:
    # 1. Edytowalny Manifest
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    st.subheader("MANIFEST ZAŁADUNKOWY")
    
    df_manifest = pd.DataFrame(st.session_state.cargo)[['name', 'total_qty', 'itemsPerCase', 'canStack']]
    df_manifest['JEDNOSTKI'] = df_manifest.apply(lambda x: math.ceil(x['total_qty'] / (x['itemsPerCase'] if x['itemsPerCase'] > 0 else 1)), axis=1)
    
    # Edytor: zmiana ilości na 0 usuwa produkt
    edited_df = st.data_editor(df_manifest, hide_index=True, use_container_width=True)
    
    if not edited_df.equals(df_manifest):
        new_cargo = []
        for idx, row in edited_df.iterrows():
            if row['total_qty'] > 0:
                # Znajdź oryginał, by zachować wymiary
                orig = next(i for i in st.session_state.cargo if i['name'] == row['name'])
                orig.update({
                    'total_qty': row['total_qty'], 
                    'itemsPerCase': max(1, row['itemsPerCase']), 
                    'canStack': row['canStack']
                })
                new_cargo.append(orig)
        st.session_state.cargo = new_cargo
        st.rerun()

    # Eksport CSV
    csv_data = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("EKSPORTUJ LISTĘ ZAŁADUNKOWĄ (CSV)", csv_data, "vorteza_manifest.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Przeliczanie brył do pakowania
    all_units = []
    for item in st.session_state.cargo:
        ipc = item['itemsPerCase'] if item['itemsPerCase'] > 0 else 1
        num_units = math.ceil(item['total_qty'] / ipc)
        for _ in range(num_units):
            all_units.append(item.copy())
    
    # 3. Wykonanie logiki pakowania
    fleet = pack_logic_pro(all_units, veh, margin)
    
    # 4. Wyświetlanie wyników dla każdego pojazdu
    for i, res in enumerate(fleet):
        with st.expander(f"🚛 POJAZD #{i+1} - ANALIZA ROZMIESZCZENIA", expanded=True):
            col_viz, col_stat = st.columns([2, 1])
            
            fig, cog_x = draw_3d_pro(res['stacks'], veh, st.session_state.colors)
            
            with col_viz:
                st.plotly_chart(fig, use_container_width=True)
            
            with col_stat:
                st.markdown("### DANE TECHNICZNE")
                ldm = round(max([s['x'] + s['l'] for s in res['stacks']]) / 100, 2) if res['stacks'] else 0
                st.metric("METRY BIEŻĄCE (LDM)", f"{ldm} m")
                
                # Obliczanie balansu masy (procentowy nacisk na przód/tył)
                front_pct = round((1 - cog_x/veh['l']) * 100, 1)
                st.write(f"**BALANS MASY:** PRZÓD {front_pct}% | TYŁ {100-front_pct}%")
                
                if front_pct < 40 or front_pct > 65:
                    st.warning("⚠️ RYZYKO: Niewłaściwy rozkład masy na osie!")
                
                st.write(f"**WAGA ŁADUNKU:** {res['weight']} / {veh['weight']} kg")
                st.progress(min(res['weight']/veh['weight'], 1.0))
                
                area_used = sum(s['l']*s['w'] for s in res['stacks'])
                area_total = veh['l']*veh['w']
                st.write(f"**WYPEŁNIENIE PODŁOGI:** {round(area_used/area_total*100, 1)}%")
                st.progress(min(area_used/area_total, 1.0))
                
                st.markdown("---")
                st.write("**LISTA JEDNOSTEK W TYM POJEŹDZIE:**")
                # Zliczanie wystąpień nazw produktów
                names = [it['name'] for s in res['stacks'] for it in s['items']]
                st.table(pd.Series(names).value_counts().reset_index().rename(columns={"index": "Produkt", "count": "Szt"}))
else:
    st.info("System gotowy. Dodaj produkty w panelu bocznym, aby rozpocząć planowanie załadunku.")
