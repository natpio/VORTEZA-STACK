import streamlit as st
import pandas as pd
import json
import requests
import base64
import plotly.graph_objects as go
from PIL import Image

# =========================================================
# KONFIGURACJA GITHUB (Dane z app2)
# =========================================================
try:
    GITHUB_TOKEN = st.secrets["G_TOKEN"]
except Exception:
    GITHUB_TOKEN = "BRAK"

REPO_OWNER = "natpio"
REPO_NAME = "rentownosc-transportu"
# Ścieżka do Twojego nowego pliku w repozytorium
FILE_PATH_PRODUCTS = "products.json"

# =========================================================
# KONFIGURACJA STRONY I STYLIZACJA
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
            .stButton > button:hover { background-color: var(--v-copper); color: black; }
            label[data-testid="stWidgetLabel"] { color: var(--v-copper) !important; text-transform: uppercase; font-weight: 600 !important; }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# POBIERANIE DANYCH Z GITHUB
# =========================================================
def get_products_from_github():
    """Pobiera listę produktów z GitHub API."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH_PRODUCTS}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN != "BRAK" else {}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            decoded_data = base64.b64decode(content['content']).decode('utf-8')
            return json.loads(decoded_data)
        else:
            return None
    except Exception:
        return None

# =========================================================
# SYSTEM LOGOWANIA
# =========================================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center;'>VORTEZA SYSTEMS</h2>", unsafe_allow_html=True)
            pwd = st.text_input("PASSWORD:", type="password")
            if st.button("AUTHORIZE"):
                if pwd == "NowyRozdzial":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("ACCESS DENIED")
            st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

# --- INICJALIZACJA ---
apply_vorteza_theme()

if check_password():
    # Pobieranie produktów
    github_products = get_products_from_github()
    
    if github_products:
        PRODUCTS = github_products
        st.toast("✅ Produkty załadowane z GitHub", icon="☁️")
    else:
        # Fallback - Dane awaryjne jeśli GitHub nie odpowie
        PRODUCTS = {
            "Europaleta (Fallback)": {"l": 120, "w": 80, "h": 150, "weight": 400.0, "stack": False},
            "Case Standard (Fallback)": {"l": 60, "w": 40, "h": 50, "weight": 25.0, "stack": True}
        }
        st.error("⚠️ Nie udało się pobrać produktów z GitHub. Używam listy awaryjnej.")

    VEHICLES = {
        "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 12000, "pallets": 33},
        "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 3500, "pallets": 16},
        "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
        "BUS (10ep)": {"l": 485, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
    }

    # Nagłówek
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("CARGO PLANNER PRO 3D")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- INTERFEJS ---
    left_col, right_col = st.columns([1, 2], gap="large")

    with left_col:
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        v_name = st.selectbox("Vehicle Fleet:", list(VEHICLES.keys()))
        v = VEHICLES[v_name]
        
        st.markdown("---")
        prod_key = st.selectbox("Select SQM Item:", list(PRODUCTS.keys()))
        qty = st.number_input("Quantity:", min_value=1, value=1)
        
        if "cargo_list" not in st.session_state:
            st.session_state.cargo_list = []

        if st.button("ADD TO MANIFEST"):
            p = PRODUCTS[prod_key]
            st.session_state.cargo_list.append({
                "name": prod_key, "l": p["l"], "w": p["w"], "h": p["h"],
                "weight": p["weight"], "stack": p["stack"], "qty": qty
            })
            st.rerun()

        if st.session_state.cargo_list:
            if st.button("RESET MANIFEST"):
                st.session_state.cargo_list = []
                st.rerun()
            for i, item in enumerate(st.session_state.cargo_list):
                st.caption(f"{i+1}. {item['name']} x{item['qty']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        if st.session_state.cargo_list:
            # Silnik pakowania (Logika app1)
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
                        current_h = sum(i['h'] for i in s['items'])
                        if s['l'] >= item['l'] and s['w'] >= item['w'] and (current_h + item['h']) <= v['h']:
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

            # Plotly 3D (Styl Vorteza)
            fig = go.Figure()
            fig.add_trace(go.Scatter3d(
                x=[0, v['l'], v['l'], 0, 0, 0, v['l'], v['l'], 0, 0],
                y=[0, 0, v['w'], v['w'], 0, 0, 0, v['w'], v['w'], 0],
                z=[0, 0, 0, 0, 0, v['h'], v['h'], v['h'], v['h'], v['h']],
                mode='lines', line=dict(color='#B58863', width=3), name='Cargo Area'
            ))

            for s in stacks:
                z_off = 0
                for item in s['items']:
                    fig.add_trace(go.Mesh3d(
                        x=[s['x'], s['x']+item['l'], s['x']+item['l'], s['x'], s['x'], s['x']+item['l'], s['x']+item['l'], s['x']],
                        y=[s['y'], s['y'], s['y']+item['w'], s['y']+item['w'], s['y'], s['y'], s['y']+item['w'], s['y']+item['w']],
                        z=[z_off, z_off, z_off, z_off, z_off+item['h'], z_off+item['h'], z_off+item['h'], z_off+item['h']],
                        i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                        color='#B58863', opacity=0.7, flatshading=True
                    ))
                    z_off += item['h']

            fig.update_layout(scene=dict(xaxis_title='L (cm)', yaxis_title='W (cm)', zaxis_title='H (cm)', aspectmode='data'),
                              paper_bgcolor='black', margin=dict(l=0,r=0,b=0,t=0), height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Podsumowanie
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("LOAD", f"{total_weight} kg")
            m2.metric("FLOOR", f"{len(stacks)} EP")
            m3.metric("UTILIZATION", f"{round((total_weight/v['weight'])*100, 1)}%")
            st.markdown('</div>', unsafe_allow_html=True)
