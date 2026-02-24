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
st.markdown(f"<style>.stApp {{background: url('data:image/jpeg;base64,{get_bg('background.jpg')}') center/cover fixed;}} .block-container {{background: rgba(255,255,255,0.95); padding: 3rem!important; border-radius: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); margin-top: 40px;}} h1 {{color: #1e8449!important; text-align: center; font-family: 'Arial Black';}} .m {{color: #e74c3c; font-weight: bold; font-size: 1.1rem;}} .s {{color: #27ae60; font-weight: bold; font-size: 1.1rem;}}</style>", unsafe_allow_html=True)

if 'init' not in st.session_state:
    st.markdown("<style>.block-container {visibility: hidden;}</style><h1 style='color: white; margin-top: 250px; text-shadow: 2px 2px 8px #000;'>🥗 ResteRetter Pro wird geladen...</h1>", unsafe_allow_html=True)
    time.sleep(2); st.session_state.init = True; st.rerun()

# --- UI ---
st.title("🥗 ResteRetter Pro")
st.markdown("<p style='text-align: center; color: #555;'>Gib deine Zutaten ein und wir finden das perfekte Essen!</p>", unsafe_allow_html=True)
st.caption("_Format: Zutat, Zutat, ..._")
u_in = st.text_input("Was hast du noch im Kühlschrank?", placeholder="z.B. Tomaten, Käse, Eier, Mehl")

if "res" not in st.session_state: st.session_state.res, st.session_state.u_en = None, []

if st.button("JETZT REZEPTE FINDEN") and u_in:
    with st.spinner('⚡ Suche läuft...'):
        # Korrektur der Eingabe-Logik: Teilt bei jedem Komma, egal wie viele
        st.session_state.u_en = [to_en.translate(i.strip().lower()) for i in u_in.split(",") if i.strip()]
        
        # Alle Rezepte für jede Zutat sammeln (Gleichgewichtung)
        ids = set()
        for ing in st.session_state.u_en:
            res_api = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ing}").json()
            if res_api and 'meals' in res_api and res_api['meals']:
                for m in res_api['meals']:
                    ids.add(m['idMeal'])
        
        r_l = []
        for m_id in list(ids)[:12]:
            d = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={m_id}").json()['meals'][0]
            r_i = [d[f'strIngredient{i}'].lower() for i in range(1,21) if d.get(f'strIngredient{i}') and d[f'strIngredient{i}'].strip()]
            
            # Match-Logik: Prüft ob die User-Zutaten im Rezept vorkommen
            match_count = 0
            for user_ing in st.session_state.u_en:
                if any(user_ing in recipe_ing for recipe_ing in r_i):
                    match_count += 1
            
            r_l.append({'d': d, 'm': match_count, 'miss': len(r_i)-match_count, 'i_en': r_i})
        
        # Sortierung: Rezepte mit den wenigsten fehlenden Zutaten oben
        st.session_state.res = sorted(r_l, key=lambda x: x['miss'])

# --- DISPLAY ---
if st.session_state.res is not None:
    if not st.session_state.res:
        st.markdown("---")
        try:
            st.image(Image.open("Hungerbild.jpg"), use_container_width=True)
        except:
            st.warning("Keine Rezepte gefunden.")
        st.error("Leider konnten wir mit diesen Zutaten nichts finden.")
    else:
        for i, item in enumerate(st.session_state.res):
            d = item['d']
            with st.expander(f"{d['strMeal'].upper()} | ✅ {item['m']} | 🛒 {item['miss']}"):
                c1, c2 = st.columns([1, 2])
                c1.image(d['strMealThumb'], use_container_width=True)
                c1.link_button("🌐 Link zur Website", f"https://www.themealdb.com/meal/{d['idMeal']}")
                
                with c2:
                    st.subheader("Zutaten:")
                    for ing in item['i_en']:
                        is_m = any(u in ing for u in st.session_state.u_en)
                        st.markdown(f"<span class='{'s' if is_m else 'm'}'>{'✅' if is_m else '🛒'} {trans(ing)}</span>", unsafe_allow_html=True)
                
                st.markdown("---")
                if st.checkbox("Zubereitung anzeigen", key=f"c_{i}"):
                    # Gliederung der Anleitung
                    instr_de = to_de.translate(d['strInstructions']).replace("\n", " ")
                    steps = re.split(r'(?<=[.!?]) +', instr_de)
                    for j, s in enumerate(steps, 1):
                        if len(s.strip()) > 3: st.write(f"**Schritt {j}:** {s.strip()}")