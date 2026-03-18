import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
import base64
from PIL import Image

# =========================================================
# KONFIGURACJA STRONY I STYLIZACJA (Styl Vorteza)
# =========================================================
st.set_page_config(page_title="VORTEZA CARGO | SQM", layout="wide", page_icon="🚚")

def apply_vorteza_theme():
    # Stylizacja CSS identyczna z app2
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');

            :root {
                --v-copper: #B58863;
                --v-dark: #0E0E0E;
                --v-panel: rgba(20, 20, 20, 0.85);
                --v-text: #E0E0E0;
            }

            .stApp {
                background-color: var(--v-dark);
                color: var(--v-text);
                font-family: 'Montserrat', sans-serif;
            }

            /* Nagłówki */
            h1, h2, h3, .stSubheader {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 2px;
            }

            /* Karty / Panele */
            .vorteza-card {
                background-color: var(--v-panel);
                padding: 25px;
                border-radius: 4px;
                border-left: 4px solid var(--v-copper);
                backdrop-filter: blur(10px);
                margin-bottom: 20px;
                border-top: 1px solid rgba(181, 136, 99, 0.1);
            }

            /* Inputy i Selektory */
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, input {
                background-color: rgba(30, 30, 30, 0.9) !important;
                border: 1px solid #333 !important;
                color: white !important;
            }

            label[data-testid="stWidgetLabel"] {
                color: var(--v-copper) !important;
                text-transform: uppercase;
                font-size: 0.8rem !important;
                font-weight: 600 !important;
            }

            /* Przyciski */
            .stButton > button {
                background-color: transparent;
                color: var(--v-copper);
                border: 1px solid var(--v-copper);
                width: 100%;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                transition: 0.4s;
            }
            .stButton > button:hover {
                background-color: var(--v-copper);
                color: black;
                border: 1px solid var(--v-copper);
            }

            /* Tabela wyników */
            .metric-box {
                text-align: center;
                padding: 15px;
                border: 1px solid #333;
                background: rgba(255,255,255,0.03);
            }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# SYSTEM LOGOWANIA
# =========================================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center;'>VORTEZA SYSTEMS</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; font-size:0.8rem;'>CARGO LOGISTICS GATEWAY</p>", unsafe_allow_html=True)
            pwd = st.text_input("PASSWORD:", type="password")
            if st.button("AUTHORIZE ACCESS"):
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
    # Nagłówek górny
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("CARGO PLANNER PRO 3D")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- BAZA DANYCH (Połączona) ---
    VEHICLES = {
        "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 12000, "pallets": 33},
        "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 3500, "pallets": 16},
        "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
        "BUS (10ep)": {"l": 485, "w": 220, "h": 245, "weight": 1100, "pallets": 10},
    }

    # Rozszerzona baza produktów z SQM
    PRODUCTS = {
        "17-23\" - plastic case": {"l": 80, "w": 60, "h": 20, "weight": 20.0, "stack": True},
        "24-32\" - plastic case": {"l": 60, "w": 40, "h": 20, "weight": 15.0, "stack": True},
        "55\" TV - flightcase": {"l": 140, "w": 40, "h": 95, "weight": 65.0, "stack": False},
        "75\" TV - flightcase": {"l": 185, "w": 45, "h": 120, "weight": 95.0, "stack": False},
        "P6 LED Panel (Box)": {"l": 60, "w": 60, "h": 20, "weight": 12.0, "stack": True},
        "P3 LED Panel (Case 6)": {"l": 110, "w": 65, "h": 85, "weight": 85.0, "stack": False},
        "Truss 2m - Alu": {"l": 200, "w": 30, "h": 30, "weight": 15.0, "stack": True},
        "Subwoofer 18\"": {"l": 70, "w": 80, "h": 60, "weight": 55.0, "stack": True},
        "Europaleta (EPAL)": {"l": 120, "w": 80, "h": 150, "weight": 400.0, "stack": False},
        "Custom Cargo": {"l": 100, "w": 100, "h": 100, "weight": 10.0, "stack": True},
    }

    # --- LOGIKA APLIKACJI ---
    left_col, right_col = st.columns([1, 2], gap="large")

    with left_col:
        st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
        st.subheader("Transport Settings")
        v_name = st.selectbox("Vehicle Fleet:", list(VEHICLES.keys()))
        v = VEHICLES[v_name]
        
        st.markdown("---")
        st.subheader("Inventory Management")
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
            
            st.markdown("**Current Manifest:**")
            for i, item in enumerate(st.session_state.cargo_list):
                st.caption(f"{i+1}. {item['name']} x{item['qty']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        if st.session_state.cargo_list:
            # Uproszczony silnik pakowania 3D
            all_items = []
            for entry in st.session_state.cargo_list:
                for _ in range(entry['qty']):
                    all_items.append(entry)

            # Sortowanie dla lepszego wypełnienia
            all_items.sort(key=lambda x: x['l']*x['w'], reverse=True)

            stacks = []
            total_weight = 0
            
            # Algorytm podłogowy (First Fit Decreasing)
            for item in all_items:
                placed = False
                # Próba sztaplowania
                if item['stack']:
                    for s in stacks:
                        current_h = sum(i['h'] for i in s['items'])
                        if s['l'] >= item['l'] and s['w'] >= item['w'] and (current_h + item['h']) <= v['h']:
                            if (total_weight + item['weight']) <= v['weight']:
                                s['items'].append(item)
                                total_weight += item['weight']
                                placed = True
                                break
                
                # Nowa pozycja na podłodze
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

            # Wizualizacja Plotly (Paleta Vorteza)
            fig = go.Figure()
            
            # Obrys pojazdu (Miedziany szkielet)
            fig.add_trace(go.Scatter3d(
                x=[0, v['l'], v['l'], 0, 0, 0, v['l'], v['l'], 0, 0],
                y=[0, 0, v['w'], v['w'], 0, 0, 0, v['w'], v['w'], 0],
                z=[0, 0, 0, 0, 0, v['h'], v['h'], v['h'], v['h'], v['h']],
                mode='lines', line=dict(color='#B58863', width=3), name='Cargo Area'
            ))

            def add_vorteza_box(fig, x, y, z, l, w, h, name):
                fig.add_trace(go.Mesh3d(
                    x=[x, x+l, x+l, x, x, x+l, x+l, x],
                    y=[y, y, y+w, y+w, y, y, y+w, y+w],
                    z=[z, z, z, z, z+h, z+h, z+h, z+h],
                    i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                    color='#B58863', opacity=0.7, flatshading=True, name=name
                ))

            for s in stacks:
                z_off = 0
                for item in s['items']:
                    add_vorteza_box(fig, s['x'], s['y'], z_off, item['l'], item['w'], item['h'], item['name'])
                    z_off += item['h']

            fig.update_layout(
                scene=dict(
                    xaxis=dict(gridcolor='#222', backgroundcolor='black'),
                    yaxis=dict(gridcolor='#222', backgroundcolor='black'),
                    zaxis=dict(gridcolor='#222', backgroundcolor='black'),
                    aspectmode='data'
                ),
                paper_bgcolor='black',
                margin=dict(l=0,r=0,b=0,t=0),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            # Podsumowanie
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("PAYLOAD LOADED", f"{total_weight} kg", f"{v['weight']-total_weight} kg left")
            with m2:
                st.metric("FLOOR OCCUPANCY", f"{len(stacks)} Pallets", f"{v['pallets']} max")
            with m3:
                util = round((total_weight/v['weight'])*100, 1)
                st.metric("EFFICIENCY", f"{util}%")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Manifest is empty. Add items to visualize cargo placement.")
