import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
import base64
from PIL import Image

# =========================================================
# KONFIGURACJA STRONY I STYLIZACJA (Styl z app2)
# =========================================================
st.set_page_config(page_title="VORTEZA CARGO | SQM", layout="wide", page_icon="🚚")

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

def apply_vorteza_theme():
    # Próba załadowania tła z app2
    bin_str = get_base64_of_bin_file('bg_vorteza.png')
    if bin_str:
        bg_style = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(bg_style, unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background-color: #0E0E0E; }</style>", unsafe_allow_html=True)

    # Implementacja stylów CSS z app2 [cite: 237, 238, 240, 243, 248, 249]
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');

            :root {
                --v-copper: #B58863;
                --v-dark: #0E0E0E;
                --v-panel: rgba(20, 20, 20, 0.9);
                --v-text: #E0E0E0;
            }

            .stApp {
                color: var(--v-text);
                font-family: 'Montserrat', sans-serif;
            }

            h1, h2, h3, .stSubheader {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }

            label[data-testid="stWidgetLabel"] {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                font-size: 0.85rem !important;
                letter-spacing: 1px;
            }

            div[data-baseweb="select"] > div, input {
                background-color: rgba(15, 15, 15, 0.9) !important;
                color: white !important;
                border: 1px solid #444 !important;
            }
            
            .vorteza-card {
                background-color: var(--v-panel);
                padding: 30px;
                border-radius: 5px;
                border-left: 5px solid var(--v-copper);
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
                backdrop-filter: blur(15px);
                margin-bottom: 20px;
            }

            .stButton > button {
                background-color: rgba(0, 0, 0, 0.7);
                color: var(--v-copper);
                border: 1px solid var(--v-copper);
                padding: 15px;
                width: 100%;
                font-weight: 700;
                text-transform: uppercase;
                transition: 0.3s;
            }
            .stButton > button:hover {
                background-color: var(--v-copper);
                color: black;
            }

            /* Stylizacja tabeli wyników */
            .result-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            .result-table td {
                padding: 10px;
                border-bottom: 1px solid #222;
            }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# SYSTEM LOGOWANIA (Styl z app2)
# =========================================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            with st.form("Login"):
                st.markdown("### VORTEZA | CARGO ACCESS")
                pwd = st.text_input("Hasło dostępowe:", type="password")
                submit = st.form_submit_button("ZALOGUJ")
                if submit:
                    if pwd == "NowyRozdzial": [cite: 152]
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("❌ Błędne hasło")
        return False
    return True

# --- GŁÓWNA LOGIKA ---
apply_vorteza_theme()

if check_password():
    # Nagłówek aplikacji (Styl z app2)
    col_logo, col_title, col_logout = st.columns([1, 4, 1])
    with col_logo:
        try:
            logo = Image.open('logo_vorteza.png')
            st.image(logo, use_container_width=True)
        except:
            st.title("VORTEZA")

    with col_title:
        st.markdown("<br>", unsafe_allow_html=True)
        st.title("CARGO PLANNER PRO 3D")
    
    with col_logout:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("WYLOGUJ"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- BAZA DANYCH (Niezmieniona z app1) ---
    VEHICLES = {
        "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 12000, "pallets": 33},
        "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 3500, "pallets": 16},
        "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
        "BUS": {"l": 450, "w": 150, "h": 245, "weight": 1100, "pallets": 8},
    }

    # (Tu wstaw całą listę PRODUCTS z oryginału app1)
    PRODUCTS = {
        "17-23\" - plastic case": {"l": 80, "w": 60, "h": 20, "weight": 20.0, "ipc": 1, "stack": True},
        "24-32\" - plastic case": {"l": 60, "w": 40, "h": 20, "weight": 15.0, "ipc": 1, "stack": True},
        # ... (Dalsza część bazy produktów)
        "Własny ładunek": {"l": 120, "w": 80, "h": 100, "weight": 100.0, "ipc": 1, "stack": True},
    }

    # --- FUNKCJA RYSOWANIA 3D ---
    def add_box(fig, x, y, z, l, w, h, name, color):
        gap = 0.5
        l_g, w_g, h_g = l-gap, w-gap, h-gap
        x_c = [x, x+l_g, x+l_g, x, x, x+l_g, x+l_g, x]
        y_c = [y, y, y+w_g, y+w_g, y, y, y+w_g, y+w_g]
        z_c = [z, z, z, z, z+h_g, z+h_g, z+h_g, z+h_g]
        fig.add_trace(go.Mesh3d(
            x=x_c, y=y_c, z=z_c,
            i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
            color=color, opacity=0.9, flatshading=True, name=name, showlegend=False
        ))

    # --- INTERFEJS PLANOWANIA ---
    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.subheader("Konfiguracja Transportu")
        v_name = st.selectbox("Wybierz pojazd:", list(VEHICLES.keys()))
        v = VEHICLES[v_name]
        
        st.markdown("---")
        st.subheader("Dodaj ładunek")
        selected_prod = st.selectbox("Produkt z bazy SQM:", list(PRODUCTS.keys()))
        qty = st.number_input("Ilość (sztuk):", min_value=1, value=1)

        if "cargo_list" not in st.session_state:
            st.session_state.cargo_list = []

        if st.button("DODAJ DO LISTY"):
            p = PRODUCTS[selected_prod]
            st.session_state.cargo_list.append({
                "name": selected_prod,
                "l": p["l"], "w": p["w"], "h": p["h"],
                "weight": p["weight"], "stack": p["stack"], "qty": qty
            })
            st.rerun()

        if st.session_state.cargo_list:
            if st.button("WYCZYŚĆ LISTĘ"):
                st.session_state.cargo_list = []
                st.rerun()

            st.markdown("### Aktualna lista:")
            for idx, item in enumerate(st.session_state.cargo_list):
                st.text(f"{idx+1}. {item['name']} x{item['qty']}")
    st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if st.session_state.cargo_list:
            st.subheader("Wizualizacja 3D i Wyniki")
            
            # Algorytm pakowania (uproszczony z app1)
            items_to_pack = []
            for entry in st.session_state.cargo_list:
                for _ in range(entry['qty']):
                    items_to_pack.append(entry)

            items_to_pack.sort(key=lambda x: x['l']*x['w'], reverse=True)

            stacks = []
            unplaced = []
            total_w = 0

            for item in items_to_pack:
                placed = False
                for s in stacks:
                    if s['l'] == item['l'] and s['w'] == item['w'] and item['stack']:
                        current_stack_h = sum(i['h'] for i in s['items'])
                        if current_stack_h + item['h'] <= v['h'] and total_w + item['weight'] <= v['weight']:
                            s['items'].append(item)
                            total_w += item['weight']
                            placed = True
                            break
                
                if not placed:
                    for x in range(0, v['l'] - item['l'] + 1, 10):
                        for y in range(0, v['w'] - item['w'] + 1, 10):
                            overlap = False
                            for s in stacks:
                                if not (x + item['l'] <= s['x'] or x >= s['x'] + s['l'] or
                                        y + item['w'] <= s['y'] or y >= s['y'] + s['w']):
                                    overlap = True
                                    break
                            if not overlap and total_w + item['weight'] <= v['weight']:
                                stacks.append({'x': x, 'y': y, 'l': item['l'], 'w': item['w'], 'items': [item]})
                                total_w += item['weight']
                                placed = True
                                break
                        if placed: break
                
                if not placed:
                    unplaced.append(item)

            # Rysowanie (Plotly)
            fig = go.Figure()
            # Obrys pojazdu
            fig.add_trace(go.Scatter3d(
                x=[0, v['l'], v['l'], 0, 0, 0, v['l'], v['l'], 0, 0],
                y=[0, 0, v['w'], v['w'], 0, 0, 0, v['w'], v['w'], 0],
                z=[0, 0, 0, 0, 0, v['h'], v['h'], v['h'], v['h'], v['h']],
                mode='lines', line=dict(color='white', width=2), name='Pojazd'
            ))

            colors = ['#B58863', '#8E6B4E', '#D4A373', '#6B4F36'] # Paleta miedzi
            
            for i, s in enumerate(stacks):
                z_ptr = 0
                for item in s['items']:
                    add_box(fig, s['x'], s['y'], z_ptr, s['l'], s['w'], item['h'], item['name'], colors[i % len(colors)])
                    z_ptr += item['h']

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                scene=dict(
                    xaxis=dict(gridcolor='#333', title='Długość (cm)'),
                    yaxis=dict(gridcolor='#333', title='Szerokość (cm)'),
                    zaxis=dict(gridcolor='#333', title='Wysokość (cm)'),
                    aspectmode='data'
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

            # Podsumowanie w stylu Vorteza
            st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("WYKORZYSTANA WAGA", f"{total_w} kg / {v['weight']} kg")
            m2.metric("ZAJĘTE MIEJSCE", f"{len(stacks)} / {v['pallets']} palet")
            m3.metric("NIEZMIESZCZONE", f"{len(unplaced)} szt.")
            st.markdown('</div>', unsafe_allow_html=True)
