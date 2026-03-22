import streamlit as st, pandas as pd, plotly.graph_objects as go, math
st.set_page_config(layout="wide")
def pack(items, vw, vh):
    q, packed, y = [], [], 0.0
    for i in items:
        for _ in range(math.ceil(i['q']/i.get('ipc',1))):
            q.append({'n':i['n'],'w':i['w'],'l':i['l'],'h':i['h'],'s':i['s']})
    q.sort(key=lambda x: x['w']*x['l'], reverse=True)
    while q:
        l = q.pop(0); lw, ll, lh = (l['l'],l['w'],l['h']) if l['w']<l['l'] and l['l']<=vw else (l['w'],l['l'],l['h'])
        ms = math.floor(vh/lh) if l['s'] else 1; cs = 1
        for _ in range(ms-1):
            for i, sh in enumerate(q):
                if sh['n']==l['n']: q.pop(i); cs+=1; break
        for s in range(cs): packed.append({'n':l['n'],'x':0,'y':y,'z':s*lh,'w':lw,'l':ll,'h':lh,'c':'#d2a679'})
        xw, r_l, j = lw, ll, 0
        while j < len(q):
            c = q[j]; cw, cl, ch = (c['l'],c['w'],c['h']) if x_fit:= (xw+c['l']<=vw and c['w']<=r_l) else (c['w'],c['l'],c['h'])
            if x_fit or (xw+cw<=vw and cl<=r_l):
                q.pop(j); mcs = math.floor(vh/ch) if c['s'] else 1; ccs = 1
                for _ in range(mcs-1):
                    for k, sh in enumerate(q):
                        if sh['n']==c['n']: q.pop(k); ccs+=1; break
                for s in range(ccs): packed.append({'n':c['n'],'x':xw,'y':y,'z':s*ch,'w':cw,'l':cl,'h':ch,'c':'#a88664'})
                xw += cw
            else: j += 1
        y += r_l
    return packed, y
st.sidebar.title("VORTEZA 50")
if 'm' not in st.session_state: st.session_state.m = []
if st.sidebar.button("DODAJ 50x TV 55"): st.session_state.m.append({'n':'TV 55','w':140,'l':20,'h':85,'q':50,'s':True})
if st.sidebar.button("RESET"): st.session_state.m = []
if st.session_state.m:
    it, ldm = pack(st.session_state.m, 245, 265)
    st.metric("LDM", f"{round(ldm/100,2)} m")
    fig = go.Figure()
    fig.add_trace(go.Mesh3d(x=[0,245,245,0,0,245,245,0], y=[0,0,ldm,ldm,0,0,ldm,ldm], z=[0,0,0,0,265,265,265,265], opacity=0.03))
    for i in it:
        x,y,z,w,l,h = i['x'],i['y'],i['z'],i['w'],i['l'],i['h']
        fig.add_trace(go.Mesh3d(x=[x,x+w,x+w,x,x,x+w,x+w,x], y=[y,y,y+l,y+l,y,y,y+l,y+l], z=[z,z,z,z,z+h,z+h,z+h,z+h], color=i['c'], opacity=0.8, flatshading=True))
    st.plotly_chart(fig.update_layout(scene=dict(aspectmode='data', bgcolor='black'), margin=dict(l=0,r=0,t=0,b=0), height=700), use_container_width=True)
