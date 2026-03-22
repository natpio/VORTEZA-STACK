import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math
from datetime import datetime

# ==========================================
# 1. STYLE & CONFIG
# ==========================================
st.set_page_config(page_title="VORTEZA STACK PRO v3.3", layout="wide")

def apply_ui():
    st.markdown("""
        <style>
        .stApp { background-color: #050505; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #d2a679; }
        .metric-card { background: #111; border-left: 4px solid #d2a679; padding: 15px; border-radius: 4px; }
        .metric-val { color: #d2a679; font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CORE PACKING ENGINE
# ==========================================
class CargoPacker:
    def __init__(self, width, length, height):
        self.vw = width
        self.vl = length
        self.vh = height

    def pack(self, manifest_list):
        packed_items = []
        queue = []

        # Rozbicie na fizyczne jednostki
        for item in manifest_list:
            # Gwarancja, że czytamy ze słownika (naprawa AttributeError)
            qty = item.get('qty', 1)
            ipc = item.get('items_per_case', 1)
            num_boxes = math.ceil(qty / ipc)
            
            for _ in range(num_boxes):
                queue.append({
                    'name': item.get('name', 'Product'),
                    'w': item.get('width', 80),
                    'l': item.get('length', 120),
                    'h': item.get('height', 100),
                    'stack': item.get('can_stack', True)
                })

        # Sortowanie po powierzchni podłogi
        queue.sort(key=lambda x: (x['w'] * x['l']), reverse=True)
        
        y_cursor = 0.0
        while queue:
            leader = queue.pop(0)
            lw, ll, lh = leader['w'], leader['l'], leader['h']
            
            # Rotacja dla LDM
            if lw < ll and ll <= self.vw:
                lw, ll = ll, lw
                
            # Obliczanie stosu pionowego
            max_s = math.floor(self.vh / lh) if leader['stack'] else 1
            current_s = 1
            
            # Konsumpcja identycznych przedmiotów do stosu
            idx = 0
            while idx < len(queue) and current_s < max_s:
                if queue[idx]['name'] == leader['name']:
                    queue.pop(idx)
                    current_s += 1
                else:
                    idx += 1
            
            # Rejestracja stosu
            for s in range(current_s):
                packed_items.append({
                    'name': leader['name'],
                    'x': 0, 'y': y_cursor, 'z': s * lh,
                    'w': lw, 'l': ll, 'h': lh,
                    'color': '#d2a679'
                })
            
            # Side-filling (wypełnianie szerokości naczepy)
            x_cursor = lw
            j = 0
            while j < len(queue):
                cand = queue[j]
                cw, cl, ch = cand['w'], cand['l'], cand['h']
                
                fit = False
                if x_cursor + cw <= self.vw and cl <= ll:
                    fit = True
                elif x_cursor + cl <= self.vw and cw <= ll:
                    cw, cl = cl, cw; fit = True
                
                if fit:
                    max_cs = math.floor(self.vh / ch) if cand['stack'] else 1
                    current_cs = 1
                    queue.pop(j)
                    
                    k = 0
                    while k < len(queue) and current_cs < max_cs:
                        if queue[k]['name'] == cand['name']:
                            queue.pop(k); current_cs += 1
                        else:
                            k += 1
                            
                    for cs in range(current_cs):
                        packed_items.append({
                            'name': cand['name'], 'x': x_cursor, 'y': y_cursor, 
                            'z': cs * ch, 'w': cw, 'l': cl, 'h': ch, 'color': '#a88664'
                        })
                    x_cursor += cw
                else:
                    j += 1
            y_cursor += ll
            
        return packed_items, y_cursor

# ==========================================
# 3. RENDERER & UI
# ==========================================
def main():
    apply_ui()
    if 'manifest' not in st.session_state:
        st.session_state.manifest = []

    with st.sidebar:
        st.header("VORTEZA STACK")
        v_choice = st.selectbox("POJAZD:", ["FTL 13.6m", "Solo 8m"])
        dims = {"FTL 13.6m": (245, 1360, 265), "Solo 8m": (245, 800, 250)}
        vw, vl, vh = dims[v_choice]
        
        if st.button("DODAJ 50x TV 55\" (TEST)"):
            st.session_state.manifest.append({
                "name": "TV 55\"", "width": 140, "length": 20, "height": 85, 
                "qty": 50, "can_stack": True, "items_per_case": 1
            })
            st.rerun()
            
        if st.button("WYCZYŚĆ"):
            st.session_state.manifest = []; st.rerun()

    if st.session_state.manifest:
        packer = CargoPacker(vw, vl, vh)
        items, ldm = packer.pack(st.session_state.manifest)
        
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><small>LDM</small><br><div class='metric-val'>{round(ldm/100, 2)}m</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><small>WYKORZYSTANIE</small><br><div class='metric-val'>{round((ldm/vl)*100, 1)}%</div></div>", unsafe_allow_html=True)

        fig = go.Figure()
        # Naczepa
        fig.add_trace(go.Mesh3d(x=[0,vw,vw,0,0,vw,vw,0], y=[0,0,ldm,ldm,0,0,ldm,ldm], z=[0,0,0,0,vh,vh,vh,vh], opacity=0.03, color='white'))
        # Towary
        for it in items:
            x, y, z, w, l, h = it['x'], it['y'], it['z'], it['w'], it['l'], it['h']
            fig.add_trace(go.Mesh3d(
                x=[x,x+w,x+w,x,x,x+w,x+w,x], y=[y,y,y+l,y+l,y,y,y+l,y+l], z=[z,z,z,z,z+h,z+h,z+h,z+h],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=it['color'], opacity=0.85, flatshading=True, name=it['name']
            ))
        fig.update_layout(scene=dict(aspectmode='data', bgcolor='black', xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
                          paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=700)
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
