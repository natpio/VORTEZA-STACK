import streamlit as st
import pandas as pd
import json
import requests
import base64
import plotly.graph_objects as go

# =========================================================
# KONFIGURACJA GITHUB (Zgodnie z Twoim repo)
# =========================================================
try:
    # Pobieranie tokena z Secrets Streamlit Cloud
    GITHUB_TOKEN = st.secrets["G_TOKEN"]
except Exception:
    GITHUB_TOKEN = None

REPO_OWNER = "natpio"
REPO_NAME = "rentownosc-transportu"
FILE_PATH_PRODUCTS = "products.json"

# =========================================================
# STYLIZACJA VORTEZA
# =========================================================
st.set_page_config(page_title="VORTEZA CARGO | SQM", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            :root {
                --v-copper: #B58863;
                --v-dark: #0E0E0E;
                --v-panel: rgba(20, 20, 20, 0.85);
                --v-text: #E0E0E0;
            }
            .stApp { background-color: var(--v-dark); color: var(--v-text); font-family: 'Montserrat', sans-serif; }
            h1, h2, h3, .stSubheader { color: var(--v-copper) !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 2px; }
            .vorteza-card {
                background-color: var(--v-panel);
                padding: 25px;
                border-radius: 4px;
                border-left: 4px solid var(--v-copper);
                backdrop-filter: blur(10px);
                margin-bottom: 20px;
                border-top: 1px solid rgba(181, 136, 99, 0.1);
            }
            .stButton > button {
                background-color: transparent; color: var(--v-copper); border: 1px solid var(--v-copper);
                width: 100%; font-weight: 700; text-transform: uppercase; transition: 0.4s;
            }
            .stButton > button:hover { background-color: var(--v-copper); color: black; border: 1px solid var(--v-copper); }
            label[data-testid="stWidgetLabel"] { color: var(--v-copper) !important; text-transform: uppercase; font-weight: 600 !important; }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# POBIERANIE I MAPOWANIE TWOJEGO JSONA
# =========================================================
def get_products_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            decoded_data = base64.b64decode(content['content']).decode('utf-8')
            raw_list = json.loads(decoded_data)
            
            # Konwersja Twojej listy obiektów na słownik dla aplikacji
            processed = {}
            for item in raw_list:
                processed[item['name']] = {
                    "l": item['length'],    # Mapowanie 'length' -> 'l'
                    "w": item['width'],     # Mapowanie 'width' -> 'w'
                    "h": item['height'],    # Mapowanie 'height' -> 'h'
                    "weight": item['weight'],
                    "stack": item['canStack'] # Mapowanie 'canStack' -> 'stack'
                }
            return processed, None
        else:
            return None, f"Błąd API: {response.status_code} - {response.reason}"
    except Exception as e:
        return None, str(e)

# =========================================================
# LOGOWANIE
# =========================================================
def check_password():
    if "auth_cargo" not in st.session_state:
        st.session_state["auth_cargo"] = False
    if not st.session_state["auth_cargo"]:
        _, c2, _ = st.columns([1, 1.5, 1])
        with c2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center;'>VORTEZA CARGO</h2>", unsafe_allow_html=True)
            pwd = st.text_input("HASŁO:", type="password")
            if st.button("AUTORYZUJ"):
                if pwd == "NowyRozdzial":
                    st.session_state["auth_cargo"] = True
                    st.rerun()
                else:
                    st.error("Nieprawidłowe hasło.")
            st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

# --- START ---
apply_vorteza_theme()

if check_password():
    # Pobieranie danych z diagnostyką
    PRODUCTS, err = get_products_from_github()
    
    if err:
        st.error(f"❌ Problem z bazą danych GitHub: {err}")
        if not GITHUB_TOKEN:
            st.warning("WSKAZÓWKA: Brakuje G_TOKEN w Secrets Streamlit Cloud.")
        st.info(f"Szukany plik: {REPO_OWNER}/{REPO_NAME}/{FILE_PATH_PRODUCTS}")
        st.stop()

    VEHICLES = {
        "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 12000, "pallets": 33},
        "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 3500, "pallets": 16},
        "BUS (10ep)": {"l": 485, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
    }

    # Interfejs
    c1, c2 = st.columns([1, 2], gap="large")

    with c1:
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        v_name = st.selectbox("POJAZD:", list(VEHICLES.keys()))
        v = VEHICLES[v_name]
        
        st.markdown("---")
        # Lista produktów z Twojego JSONa
        prod_key = st.selectbox("PRODUKT SQM:", list(PRODUCTS.keys()))
        qty = st.number_input("ILOŚĆ:", min_value=1, value=1)
        
        if "cargo_list" not in st.session_state:
            st.session_state.cargo_list = []

        if st.button("DODAJ DO PLANU"):
            p = PRODUCTS[prod_key]
            st.session_state.cargo_list.append({"name": prod_key, **p, "qty": qty})
            st.rerun()

        if st.session_state.cargo_list:
            if st.button("RESETUJ"):
                st.session_state.cargo_list = []
                st.rerun()
            for i, item in enumerate(st.session_state.cargo_list):
                st.caption(f"{i+1}. {item['name']} x{item['qty']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        if st.session_state.cargo_list:
            # Uproszczony algorytm pakowania
            all_items = []
            for entry in st.session_state.cargo_list:
                for _ in range(entry['qty']):
                    all_items.append(entry)

            all_items.sort(key=lambda x: x['l']*x['w'], reverse=True)
            stacks = []
            total_weight = 0
            
            for item in all_items:
                placed = False
                if item['stack']:
                    for s in stacks:
                        ch = sum(i['h'] for i in s['items'])
                        if s['l'] >= item['l'] and s['w'] >= item['w'] and (ch + item['h']) <= v['h']:
                            if (total_weight + item['weight']) <= v['weight']:
                                s['items'].append(item)
                                total_weight += item['weight']
                                placed = True
                                break
                
                if not placed:
                    for x in range(0, v['l'] - item['l'] + 1, 10):
                        for y in range(0, v['w'] - item['w'] + 1, 10):
                            collision = False
                            for s in stacks:
                                if not (x + item['l'] <= s['x'] or x >= s['x'] + s['l'] or
                                        y + item['w'] <= s['y'] or y >= s['y'] + s['w']):
                                    collision = True
                                    break
                            if not collision and (total_weight + item['weight']) <= v['weight']:
                                stacks.append({'x': x, 'y': y, 'l': item['l'], 'w': item['w'], 'items': [item]})
                                total_weight += item['weight']
                                placed = True
                                break
                        if placed: break

            # Wizualizacja 3D
            fig = go.Figure()
            fig.add_trace(go.Scatter3d(
                x=[0, v['l'], v['l'], 0, 0, 0, v['l'], v['l'], 0, 0],
                y=[0, 0, v['w'], v['w'], 0, 0, 0, v['w'], v['w'], 0],
                z=[0, 0, 0, 0, 0, v['h'], v['h'], v['h'], v['h'], v['h']],
                mode='lines', line=dict(color='#B58863', width=2), name='Pojazd'
            ))

            for s in stacks:
                z_off = 0
                for item in s['items']:
                    fig.add_trace(go.Mesh3d(
                        x=[s['x'], s['x']+item['l'], s['x']+item['l'], s['x'], s['x'], s['x']+item['l'], s['x']+item['l'], s['x']],
                        y=[s['y'], s['y'], s['y']+item['w'], s['y']+item['w'], s['y'], s['y'], s['y']+item['w'], s['y']+item['w']],
                        z=[z_off, z_off, z_off, z_off, z_off+item['h'], z_off+item['h'], z_off+item['h'], z_off+item['h']],
                        i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                        color='#B58863', opacity=0.8, flatshading=True
                    ))
                    z_off += item['h']

            fig.update_layout(scene=dict(xaxis_title='Dł.', yaxis_title='Szer.', zaxis_title='Wys.', aspectmode='data'),
                              paper_bgcolor='black', margin=dict(l=0,r=0,b=0,t=0), height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Dashboard
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("WAGA", f"{total_weight} kg", f"{v['weight']-total_weight} kg wolne")
            m2.metric("MIEJSCA (EP)", f"{len(stacks)} / {v['pallets']}")
            m3.metric("WYKORZYSTANIE", f"{round((total_weight/v['weight'])*100, 1)}%")
            st.markdown('</div>', unsafe_allow_html=True)
