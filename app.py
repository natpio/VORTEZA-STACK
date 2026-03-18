import streamlit as st
import pandas as pd
import json
import requests
import base64
import plotly.graph_objects as go

# =========================================================
# KONFIGURACJA GITHUB
# =========================================================
try:
    GITHUB_TOKEN = st.secrets["G_TOKEN"]
except Exception:
    GITHUB_TOKEN = None

REPO_OWNER = "natpio"
REPO_NAME = "VORTEZA-STACK"
FILE_PATH_PRODUCTS = "products.json"

# =========================================================
# STYLIZACJA VORTEZA (Premium Dark & Copper)
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
            .stMetric { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; border-bottom: 2px solid var(--v-copper); }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# FUNKCJE POMOCNICZE WIZUALIZACJI
# =========================================================
def add_box(fig, x, y, z, l, w, h, name, color):
    """Dodaje prostopadłościan (ładunek) do wykresu Plotly."""
    fig.add_trace(go.Mesh3d(
        x=[x, x+l, x+l, x, x, x+l, x+l, x],
        y=[y, y, y+w, y+w, y, y, y+w, y+w],
        z=[z, z, z, z, z+h, z+h, z+h, z+h],
        i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
        color=color, opacity=0.8, flatshading=True, name=name, showlegend=False,
        hovertemplate=f"<b>{name}</b><br>Wymiary: {l}x{w}x{h} cm<extra></extra>"
    ))

# =========================================================
# POBIERANIE DANYCH Z GITHUB
# =========================================================
def get_products_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            decoded_data = base64.b64decode(content['content']).decode('utf-8')
            raw_list = json.loads(decoded_data)
            
            processed = {}
            for item in raw_list:
                processed[item['name']] = {
                    "l": item['length'],
                    "w": item['width'],
                    "h": item['height'],
                    "weight": item['weight'],
                    "stack": item['canStack']
                }
            return processed, None
        else:
            return None, f"Błąd API: {response.status_code} ({response.reason})"
    except Exception as e:
        return None, str(e)

# =========================================================
# SYSTEM LOGOWANIA
# =========================================================
def check_password():
    if "auth_vorteza" not in st.session_state:
        st.session_state["auth_vorteza"] = False
    if not st.session_state["auth_vorteza"]:
        _, c2, _ = st.columns([1, 1.5, 1])
        with c2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center;'>VORTEZA SYSTEMS</h2>", unsafe_allow_html=True)
            pwd = st.text_input("HASŁO DOSTĘPOWE:", type="password")
            if st.button("AUTORYZUJ"):
                if pwd == "NowyRozdzial":
                    st.session_state["auth_vorteza"] = True
                    st.rerun()
                else:
                    st.error("ODMOWA DOSTĘPU")
            st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

# =========================================================
# GŁÓWNA LOGIKA APLIKACJI
# =========================================================
apply_vorteza_theme()

if check_password():
    PRODUCTS, err = get_products_from_github()
    
    if err:
        st.error(f"❌ Problem z bazą produktów: {err}")
        st.stop()

    VEHICLES = {
        "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 24000, "pallets": 33},
        "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 6000, "pallets": 16},
        "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
        "BUS (10ep)": {"l": 485, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
    }

    # Dashboard nagłówkowy
    c_title, c_user = st.columns([4, 1])
    with c_title:
        st.title("VORTEZA CARGO PLANNER PRO")
    with c_user:
        if st.button("WYLOGUJ"):
            st.session_state["auth_vorteza"] = False
            st.rerun()

    # Interfejs planowania
    left_col, right_col = st.columns([1, 2.5], gap="large")

    with left_col:
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("Pojazd")
        v_name = st.selectbox("FLOTA SQM:", list(VEHICLES.keys()))
        v = VEHICLES[v_name]
        
        st.markdown("---")
        st.subheader("Ładunek")
        prod_key = st.selectbox("BAZA PRODUKTÓW:", list(PRODUCTS.keys()))
        qty = st.number_input("ILOŚĆ (szt):", min_value=1, value=1)
        
        if "cargo_list" not in st.session_state:
            st.session_state.cargo_list = []

        if st.button("DODAJ DO PLANU"):
            p_data = PRODUCTS[prod_key]
            st.session_state.cargo_list.append({"name": prod_key, **p_data, "qty": qty})
            st.rerun()

        if st.session_state.cargo_list:
            if st.button("WYCZYŚĆ MANIFEST"):
                st.session_state.cargo_list = []
                st.rerun()
            st.write("---")
            for i, item in enumerate(st.session_state.cargo_list):
                st.caption(f"{i+1}. {item['name']} x{item['qty']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        if st.session_state.cargo_list:
            # Silnik pakowania (algorytm First Fit Decreasing Height)
            to_pack = []
            for entry in st.session_state.cargo_list:
                for _ in range(entry['qty']):
                    to_pack.append(entry)

            to_pack.sort(key=lambda x: x['l']*x['w'], reverse=True)
            stacks = []
            total_weight = 0
            
            for item in to_pack:
                placed = False
                # Próba stackowania (jeśli dozwolone)
                if item['stack']:
                    for s in stacks:
                        h_current = sum(i['h'] for i in s['items'])
                        if s['l'] >= item['l'] and s['w'] >= item['w'] and (h_current + item['h']) <= v['h']:
                            if (total_weight + item['weight']) <= v['weight']:
                                s['items'].append(item)
                                total_weight += item['weight']
                                placed = True
                                break
                
                # Próba postawienia na podłodze
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
            # Rama naczepy
            fig.add_trace(go.Scatter3d(
                x=[0, v['l'], v['l'], 0, 0, 0, v['l'], v['l'], 0, 0],
                y=[0, 0, v['w'], v['w'], 0, 0, 0, v['w'], v['w'], 0],
                z=[0, 0, 0, 0, 0, v['h'], v['h'], v['h'], v['h'], v['h']],
                mode='lines', line=dict(color='#B58863', width=3), name='Pojazd'
            ))

            colors = ['#B58863', '#967052', '#7A5B43', '#D4A373', '#A68A64']
            for i, s in enumerate(stacks):
                z_ptr = 0
                for item in s['items']:
                    add_box(fig, s['x'], s['y'], z_ptr, item['l'], item['w'], item['h'], 
                            item['name'], colors[i % len(colors)])
                    z_ptr += item['h']

            fig.update_layout(
                scene=dict(xaxis_title='L (cm)', yaxis_title='W (cm)', zaxis_title='H (cm)', aspectmode='data'),
                paper_bgcolor='black', margin=dict(l=0,r=0,b=0,t=0), height=600
            )
            st.plotly_chart(fig, use_container_width=True)

            # Raport Załadunku
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            r1, r2, r3 = st.columns(3)
            r1.metric("WAGA CAŁKOWITA", f"{total_weight} kg", f"Limit: {v['weight']} kg")
            r2.metric("PODŁOGA (EP)", f"{len(stacks)} / {v['pallets']}")
            r3.metric("WYKORZYSTANIE WAGI", f"{round((total_weight/v['weight'])*100, 1)}%")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Manifest jest pusty. Wybierz pojazd i produkty, aby rozpocząć planowanie.")
