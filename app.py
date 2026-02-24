import streamlit as st, requests, base64, time, re
from deep_translator import GoogleTranslator
from PIL import Image

# --- TOOLS ---
@st.cache_resource
def get_tools(): return GoogleTranslator(source='de', target='en'), GoogleTranslator(source='en', target='de')
to_en, to_de = get_tools()

@st.cache_data(show_spinner=False)
def trans(text): return to_de.translate(text).capitalize()

def get_bg(p):
    try: return base64.b64encode(open(p, "rb").read()).decode()
    except: return ""

# --- STYLE ---
st.set_page_config(page_title="ResteRetter Pro", page_icon="🥗")
st.markdown(f"""
<style>
    .stApp {{background: url('data:image/jpeg;base64,{get_bg('background.jpg')}') center/cover fixed;}}
    .block-container {{
        background-color: rgba(255, 255, 255, 0.98); 
        padding: 2rem!important; 
        border-radius: 25px; 
        margin-top: 20px;
    }}
    /* Erzwinge schwarze Schrift für alle Texte oben */
    .stMarkdown p, .stCaption {{
        color: #000000 !important; 
        font-weight: 500 !important;
    }}
    h1 {{color: #1e8449 !important; text-align: center;}}
    
    /* Expander-Titel Fix für Handy */
    summary {{
        background-color: #f0f2f6 !important;
        color: #000000 !important;
        border-radius: 10px;
        padding: 10px !important;
        font-weight: bold !important;
    }}
    .m {{color: #e74c3c; font-weight: bold;}}
    .s {{color: #27ae60; font-weight: bold;}}
</style>
""", unsafe_allow_html=True)

if 'init' not in st.session_state:
    st.markdown("<h1 style='color: white; text-align: center; margin-top: 200px;'>🥗 Lädt...</h1>", unsafe_allow_html=True)
    time.sleep(1.5); st.session_state.init = True; st.rerun()

# --- UI ---
st.title("🥗 ResteRetter Pro")
st.markdown("<p style='text-align: center;'>Gib deine Zutaten ein und wir finden das perfekte Essen!</p>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 0.8rem; margin-bottom: -15px;'>Format: Zutat, Zutat, ...</p>", unsafe_allow_html=True)

# Eingabefeld
u_in = st.text_input("Was hast du noch im Kühlschrank?", placeholder="z.B. Tomaten, Käse")

if "res" not in st.session_state: st.session_state.res, st.session_state.u_en = None, []

if st.button("JETZT REZEPTE FINDEN") and u_in:
    with st.spinner('⚡ Suche läuft...'):
        # Unterstützung für beliebig viele Zutaten
        st.session_state.u_en = [to_en.translate(i.strip().lower()) for i in u_in.split(",") if i.strip()]
        
        ids = set()
        for ing in st.session_state.u_en:
            r = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ing}").json()
            if r and 'meals' in r and r['meals']:
                for m in r['meals']: ids.add(m['idMeal'])
        
        r_l = []
        for m_id in list(ids)[:12]:
            d = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={m_id}").json()['meals'][0]
            r_i = [d[f'strIngredient{i}'].lower() for i in range(1,21) if d.get(f'strIngredient{i}') and d[f'strIngredient{i}'].strip()]
            match = sum(1 for user_ing in st.session_state.u_en if any(user_ing in ri for ri in r_i))
            r_l.append({'d': d, 'm': match, 'miss': len(r_i)-match, 'i_en': r_i})
        
        st.session_state.res = sorted(r_l, key=lambda x: x['miss'])

# --- DISPLAY ---
if st.session_state.res is not None:
    if not st.session_state.res:
        try: st.image("Hungerbild.jpg", use_container_width=True)
        except: st.warning("Nichts gefunden.")
    else:
        for i, item in enumerate(st.session_state.res):
            d = item['d']
            # Header in Großbuchstaben für bessere Handy-Sichtbarkeit
            with st.expander(f"{d['strMeal'].upper()} | ✅ {item['m']} | 🛒 {item['miss']}"):
                c1, c2 = st.columns([1, 2])
                c1.image(d['strMealThumb'], use_container_width=True)
                c1.link_button("🌐 Link zur Website", f"https://www.themealdb.com/meal/{d['idMeal']}")
                
                with c2:
                    st.subheader("Zutaten:")
                    for ing in item['i_en']:
                        is_m = any(u in ing for u in st.session_state.u_en)
                        st.markdown(f"<span class='{'s' if is_m else 'm'}'>{'✅' if is_m else '🛒'} {trans(ing)}</span>", unsafe_allow_html=True)
                
                if st.checkbox("Zubereitung anzeigen", key=f"c_{i}"):
                    instr = to_de.translate(d['strInstructions']).replace("\n", " ")
                    for j, s in enumerate(re.split(r'(?<=[.!?]) +', instr), 1):
                        if len(s.strip()) > 3: st.write(f"**Schritt {j}:** {s.strip()}")
