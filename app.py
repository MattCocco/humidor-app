import streamlit as st
from datetime import date
import anthropic
from supabase import create_client

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="The Cabinet", page_icon="🥃", layout="centered")

# ── Custom CSS — Bold & Modern ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;600;700&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Instrument Sans', sans-serif;
    background-color: #0D0D0D;
    color: #F0EDE6;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 780px; }

/* App title */
.cabinet-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 108px;
    letter-spacing: 0.05em;
    line-height: 1;
    color: #F0EDE6;
    margin: 0;
}
.cabinet-sub {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #C9A84C;
    margin-top: 4px;
}
.cabinet-divider {
    border: none;
    border-top: 1px solid #2A2A2A;
    margin: 20px 0;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #2A2A2A;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #666;
    padding: 12px 20px;
    border: none;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #C9A84C !important;
    border-bottom: 2px solid #C9A84C !important;
    background: transparent !important;
}

/* Containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #161616 !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 4px !important;
}

/* Buttons */
.stButton > button {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-radius: 3px;
    border: 1px solid #2A2A2A;
    background: transparent;
    color: #999;
    transition: all 0.15s;
}

/* Heart buttons — no border, no background */
button[title="Toggle favorite"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    min-height: unset !important;
    padding: 2px 4px !important;
}
}
.stButton > button:hover {
    border-color: #C9A84C;
    color: #C9A84C;
    background: transparent;
}
.stButton > button[kind="primary"] {
    background: #C9A84C;
    color: #0D0D0D;
    border-color: #C9A84C;
    font-weight: 700;
}
.stButton > button[kind="primary"]:hover {
    background: #E2BC5A;
    border-color: #E2BC5A;
    color: #0D0D0D;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 3px !important;
    color: #F0EDE6 !important;
    font-family: 'Instrument Sans', sans-serif !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 36px;
    color: #F0EDE6;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #AAA;
}

/* Radio */
.stRadio > div { gap: 8px; }
.stRadio > div > label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #666;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #C9A84C !important;
    background: #161616 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #2A2A2A;
}

/* Info/success boxes */
.stAlert {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    color: #F0EDE6 !important;
}

/* Divider */
hr { border-color: #2A2A2A !important; }

/* Caption */
.stCaption { color: #666 !important; font-family: 'DM Mono', monospace; font-size: 11px; }

/* Markdown headers */
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.05em; color: #F0EDE6; }

/* Badge styles */
.badge-wishlist {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: #1E1A0F;
    color: #C9A84C;
    border: 1px solid #C9A84C40;
    padding: 2px 7px;
    border-radius: 2px;
    margin-left: 6px;
}
.badge-smoked {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: #3A3A3A;
    color: #E0E0E0;
    border: 1px solid #555;
    padding: 2px 7px;
    border-radius: 2px;
    margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Supabase client ───────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_cigars():
    res = supabase.table("cigars").select("*").order("id").execute()
    return res.data or []

def add_cigar(cigar):
    supabase.table("cigars").insert(cigar).execute()

def update_cigar(cid, updates):
    supabase.table("cigars").update(updates).eq("id", cid).execute()

def delete_cigar(cid):
    supabase.table("cigars").delete().eq("id", cid).execute()

def load_spirits():
    res = supabase.table("spirits").select("*").order("id").execute()
    return res.data or []

def add_spirit(spirit):
    supabase.table("spirits").insert(spirit).execute()

def update_spirit(sid, updates):
    supabase.table("spirits").update(updates).eq("id", sid).execute()

def delete_spirit(sid):
    supabase.table("spirits").delete().eq("id", sid).execute()

# ── Session state ─────────────────────────────────────────────────────────────
for key in ["authenticated","smoking_id","expanded_id","spirit_expanded_id","tasting_id"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "authenticated" else None

# ── Password ──────────────────────────────────────────────────────────────────
def check_password():
    with st.sidebar:
        st.markdown("### 🔐 Editor Access")
        pw = st.text_input("Password", type="password", key="password_input")
        if st.button("Login"):
            if pw == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        if st.session_state.authenticated:
            st.success("✓ Editing enabled")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.rerun()

check_password()
is_admin = st.session_state.authenticated

# ── Claude helpers ────────────────────────────────────────────────────────────
def lookup_cigar(brand, name):
    import json
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""I have a cigar: Brand: {brand}, Name/Line: {name}
Return ONLY a JSON object, no other text:
{{"vitola":"most common vitola","wrapper":"from: Colorado Claro,Colorado,Colorado Maduro,Maduro,Natural,Claro,Oscuro,Candela","origin":"from: Nicaragua,Cuba,Dominican Republic,Honduras,Ecuador,Mexico,Cameroon,USA,Panama,Brazil","strength":"from: Mild,Mild-Medium,Medium,Medium-Full,Full","description":"2 sentence tasting note"}}"""
    msg = client.messages.create(model="claude-opus-4-6", max_tokens=300, messages=[{"role":"user","content":prompt}])
    text = msg.content[0].text.strip()
    if text.startswith("```"): text = text.split("```")[1]; text = text[4:] if text.startswith("json") else text
    return json.loads(text.strip())

def lookup_spirit(brand, name):
    import json
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""I have a spirit: Brand: {brand}, Name: {name}
Return ONLY a JSON object, no other text:
{{"category":"from: Scotch Whisky,Bourbon,Irish Whiskey,Japanese Whisky,Amaro,Rum,Mezcal,Tequila,Cognac,Armagnac,Port,Sherry,Other","region":"region or origin","age":"age statement or NAS","abv":40.0,"description":"2 sentence tasting note"}}"""
    msg = client.messages.create(model="claude-opus-4-6", max_tokens=300, messages=[{"role":"user","content":prompt}])
    text = msg.content[0].text.strip()
    if text.startswith("```"): text = text.split("```")[1]; text = text[4:] if text.startswith("json") else text
    return json.loads(text.strip())

def get_pairing(cigar, spirit):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""Pairing analysis:
Cigar: {cigar['brand']} {cigar['name']} ({cigar['vitola']}, {cigar['wrapper']} wrapper, {cigar['origin']}, {cigar['strength']})
Spirit: {spirit['brand']} {spirit['name']} ({spirit['category']}, {spirit.get('region','')}, {spirit.get('age','')})
Give: 1) Pairing rating: Excellent/Good/Decent/Not Recommended 2) 2-3 sentence explanation 3) One serving tip. Be direct and opinionated."""
    msg = client.messages.create(model="claude-opus-4-6", max_tokens=300, messages=[{"role":"user","content":prompt}])
    return msg.content[0].text.strip()

def get_recommendations(top_cigars, fav_cigars, top_spirits, fav_spirits):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    cigar_context = ""
    if top_cigars:
        cigar_context += "Highest rated cigars: " + ", ".join([f"{c['brand']} {c['name']} ({c['rating']}/5)" for c in top_cigars])
    if fav_cigars:
        cigar_context += "\nFavorite cigars: " + ", ".join([f"{c['brand']} {c['name']}" for c in fav_cigars])
    spirit_context = ""
    if top_spirits:
        spirit_context += "Highest rated spirits: " + ", ".join([f"{s['brand']} {s['name']} ({s['rating']}/5)" for s in top_spirits])
    if fav_spirits:
        spirit_context += "\nFavorite spirits: " + ", ".join([f"{s['brand']} {s['name']}" for s in fav_spirits])

    prompt = f"""Based on this person's taste profile, give them personalized recommendations.

CIGARS:
{cigar_context or "No data yet"}

SPIRITS:
{spirit_context or "No data yet"}

Please provide:
1. **3 Cigars to Try Next** — specific brand and line, with a one sentence reason why based on their taste profile
2. **3 Spirits to Try Next** — specific brand and expression, with a one sentence reason why
3. **One Bold Suggestion** — something slightly outside their comfort zone that you think they'd love, either a cigar or spirit, with a compelling reason

Format each recommendation clearly. Be specific, opinionated, and knowledgeable. Write like a trusted expert who knows their palate well."""
    msg = client.messages.create(model="claude-opus-4-6", max_tokens=600, messages=[{"role":"user","content":prompt}])
    return msg.content[0].text.strip()

# ── Constants ─────────────────────────────────────────────────────────────────
VITOLAS    = ["Robusto","Toro","Churchill","Corona","Lonsdale","Belicoso","Torpedo","Lancero","Petite Corona","Gordo"]
WRAPPERS   = ["Colorado Claro","Colorado","Colorado Maduro","Maduro","Natural","Claro","Oscuro","Candela"]
ORIGINS    = ["Nicaragua","Cuba","Dominican Republic","Honduras","Ecuador","Mexico","Cameroon","USA","Panama","Brazil"]
STRENGTHS  = ["Mild","Mild-Medium","Medium","Medium-Full","Full"]
CATEGORIES = ["Scotch Whisky","Bourbon","Irish Whiskey","Japanese Whisky","Amaro","Rum","Mezcal","Tequila","Cognac","Armagnac","Port","Sherry","Other"]
HALF_STARS = [0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0]

def format_rating(rating):
    if not rating: return "—"
    full = int(rating)
    half = rating - full >= 0.5
    return "⭐" * full + ("½" if half else "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="cabinet-title">THE CABINET</p>', unsafe_allow_html=True)
st.markdown('<p class="cabinet-sub">Cigars & Spirits Journal</p>', unsafe_allow_html=True)
st.markdown('<hr class="cabinet-divider">', unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["HUMIDOR", "SPIRITS", "JOURNAL", "PAIRINGS", "FOR YOU"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — HUMIDOR
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    if is_admin:
        with st.expander("＋  ADD CIGAR"):
            with st.form("lookup_form"):
                col1, col2 = st.columns(2)
                with col1:
                    brand = st.text_input("Brand", placeholder="e.g. Padron")
                with col2:
                    name = st.text_input("Name / Line", placeholder="e.g. 1964 Anniversary")
                lookup = st.form_submit_button("Look Up Details")

            if lookup and brand and name:
                with st.spinner("Looking up..."):
                    try:
                        result = lookup_cigar(brand, name)
                        st.session_state.lookup_result = result
                        st.session_state.lookup_brand = brand
                        st.session_state.lookup_name = name
                        st.success("Found. Review below.")
                    except Exception as e:
                        st.error(f"Lookup failed: {e}")
                        st.session_state.lookup_result = None

            if "lookup_result" in st.session_state and st.session_state.lookup_result:
                r = st.session_state.lookup_result
                with st.form("add_cigar"):
                    col1, col2 = st.columns(2)
                    with col1:
                        vitola  = st.selectbox("Vitola",   VITOLAS,   index=VITOLAS.index(r.get("vitola",VITOLAS[0])) if r.get("vitola") in VITOLAS else 0)
                        origin  = st.selectbox("Origin",   ORIGINS,   index=ORIGINS.index(r.get("origin",ORIGINS[0])) if r.get("origin") in ORIGINS else 0)
                        qty     = st.number_input("Qty", min_value=0, value=1)
                    with col2:
                        wrapper  = st.selectbox("Wrapper",  WRAPPERS,  index=WRAPPERS.index(r.get("wrapper",WRAPPERS[0])) if r.get("wrapper") in WRAPPERS else 0)
                        strength = st.selectbox("Strength", STRENGTHS, index=STRENGTHS.index(r.get("strength",STRENGTHS[0])) if r.get("strength") in STRENGTHS else 0)
                        price    = st.number_input("Price/stick ($)", min_value=0.0, step=0.50)
                    purchase_date = st.date_input("Purchase date", value=date.today())
                    notes = st.text_area("Notes", value=r.get("description",""))
                    if st.form_submit_button("Save", type="primary"):
                        add_cigar({"brand":st.session_state.lookup_brand,"name":st.session_state.lookup_name,"vitola":vitola,"wrapper":wrapper,"origin":origin,"strength":strength,"qty":int(qty),"price":float(price),"notes":notes,"comments":"","purchase_date":str(purchase_date),"smoked":False,"rating":0.0,"smoked_date":"","favorite":False})
                        del st.session_state.lookup_result
                        st.success("Saved.")
                        st.rerun()

    st.divider()
    filter_opt = st.radio("", ["All","In Humidor","Smoked","Favorites"], horizontal=True, key="cigar_filter")
    search = st.text_input("", placeholder="Search…", key="cigar_search")

    cigars = load_cigars()
    if filter_opt == "In Humidor": cigars = [c for c in cigars if not c["smoked"]]
    elif filter_opt == "Smoked": cigars = [c for c in cigars if c["smoked"]]
    elif filter_opt == "Favorites": cigars = [c for c in cigars if c.get("favorite")]
    if search: cigars = [c for c in cigars if search.lower() in f"{c['brand']} {c['name']}".lower()]

    if not cigars:
        st.caption("No cigars found." if not is_admin else "No cigars found. Add one above.")
    else:
        for cigar in cigars:
            cid = cigar["id"]
            is_expanded = st.session_state.expanded_id == cid
            is_smoking  = st.session_state.smoking_id == cid

            with st.container(border=True):
                col1, col2, col3 = st.columns([0.08, 3.5, 1])
                with col1:
                    heart = "❤️" if cigar.get("favorite") else "🤍"
                    if is_admin:
                        if st.button(heart, key=f"fav_{cid}"):
                            update_cigar(cid, {"favorite": not cigar.get("favorite",False)})
                            st.rerun()
                    else:
                        st.write(heart)
                with col2:
                    smoked_badge = '<span class="badge-smoked">Smoked</span>' if cigar["smoked"] else ""
                    st.markdown(f"**{cigar['brand']} {cigar['name']}**{smoked_badge}", unsafe_allow_html=True)
                    st.caption(f"{cigar['vitola']} · {cigar['origin']} · {cigar['wrapper']} · {cigar['strength']}")
                    if cigar["smoked"] and cigar.get("rating"):
                        st.caption(format_rating(cigar["rating"]))
                with col3:
                    if st.button("▼" if not is_expanded else "▲", key=f"exp_{cid}"):
                        st.session_state.expanded_id = None if is_expanded else cid
                        st.session_state.smoking_id = None
                        st.rerun()

                if is_expanded:
                    st.divider()
                    if cigar.get("notes"): st.markdown(f"**Notes** — {cigar['notes']}")
                    if cigar.get("comments"): st.markdown(f"**Comments** — {cigar['comments']}")
                    cols = st.columns(3)
                    if cigar.get("price"): cols[0].caption(f"${cigar['price']:.2f}/stick")
                    if cigar.get("purchase_date"): cols[1].caption(f"Bought {cigar['purchase_date']}")
                    if cigar.get("qty") is not None: cols[2].caption(f"{cigar['qty']} remaining")

                    if is_admin:
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if not cigar["smoked"]:
                                if st.button("Mark Smoked", key=f"smoke_{cid}"):
                                    st.session_state.smoking_id = cid
                                    st.rerun()
                            else:
                                if st.button("Unmark Smoked", key=f"unsmoke_{cid}"):
                                    update_cigar(cid, {"smoked":False,"smoked_date":"","rating":0.0,"comments":""})
                                    st.rerun()
                        with col_c:
                            if st.button("Delete", key=f"del_{cid}"):
                                delete_cigar(cid)
                                st.session_state.expanded_id = None
                                st.rerun()

                if is_smoking and is_admin:
                    st.divider()
                    with st.form(f"smoke_form_{cid}"):
                        rating = st.select_slider("Rating", options=HALF_STARS, value=3.0, format_func=lambda x: f"{x} ⭐")
                        comments = st.text_area("Comments", placeholder="How was it?")
                        smoked_date = st.date_input("Date smoked", value=date.today())
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("Save", type="primary"):
                                update_cigar(cid, {"smoked":True,"smoked_date":str(smoked_date),"rating":float(rating),"comments":comments})
                                st.session_state.smoking_id = None
                                st.rerun()
                        with c2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.smoking_id = None
                                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — SPIRITS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    if is_admin:
        with st.expander("＋  ADD SPIRIT"):
            with st.form("spirit_lookup_form"):
                col1, col2 = st.columns(2)
                with col1:
                    s_brand = st.text_input("Brand", placeholder="e.g. Lagavulin")
                with col2:
                    s_name = st.text_input("Expression", placeholder="e.g. 16 Year")
                is_wishlist = st.checkbox("Wishlist only (haven't bought yet)")
                if st.form_submit_button("Look Up Details"):
                    with st.spinner("Looking up..."):
                        try:
                            s_result = lookup_spirit(s_brand, s_name)
                            st.session_state.spirit_lookup_result = s_result
                            st.session_state.spirit_lookup_brand = s_brand
                            st.session_state.spirit_lookup_name = s_name
                            st.session_state.spirit_lookup_wishlist = is_wishlist
                            st.success("Found. Review below.")
                        except Exception as e:
                            st.error(f"Lookup failed: {e}")
                            st.session_state.spirit_lookup_result = None

            if "spirit_lookup_result" in st.session_state and st.session_state.spirit_lookup_result:
                r = st.session_state.spirit_lookup_result
                with st.form("add_spirit"):
                    col1, col2 = st.columns(2)
                    with col1:
                        s_cat   = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(r.get("category",CATEGORIES[0])) if r.get("category") in CATEGORIES else 0)
                        s_age   = st.text_input("Age", value=r.get("age",""))
                        s_price = st.number_input("Price ($)", min_value=0.0, step=1.0)
                    with col2:
                        s_region = st.text_input("Region", value=r.get("region",""))
                        s_abv    = st.number_input("ABV (%)", min_value=0.0, max_value=100.0, value=float(r.get("abv",40.0)), step=0.5)
                        s_date   = st.date_input("Purchase date", value=date.today())
                    s_notes = st.text_area("Notes", value=r.get("description",""))
                    if st.form_submit_button("Save", type="primary"):
                        add_spirit({"brand":st.session_state.spirit_lookup_brand,"name":st.session_state.spirit_lookup_name,"category":s_cat,"region":s_region,"age":s_age,"abv":float(s_abv),"price":float(s_price),"notes":s_notes,"comments":"","purchase_date":str(s_date),"tried":False,"tried_date":"","rating":0.0,"favorite":False,"wishlist":st.session_state.spirit_lookup_wishlist})
                        del st.session_state.spirit_lookup_result
                        st.success("Saved.")
                        st.rerun()

    st.divider()
    s_filter = st.radio("", ["All","In Cabinet","Wishlist","Tried","Favorites"], horizontal=True, key="spirit_filter")
    s_search = st.text_input("", placeholder="Search…", key="spirit_search")

    spirits = load_spirits()
    if s_filter == "In Cabinet": spirits = [s for s in spirits if not s.get("wishlist") and not s.get("tried")]
    elif s_filter == "Wishlist": spirits = [s for s in spirits if s.get("wishlist")]
    elif s_filter == "Tried": spirits = [s for s in spirits if s.get("tried")]
    elif s_filter == "Favorites": spirits = [s for s in spirits if s.get("favorite")]
    if s_search: spirits = [s for s in spirits if s_search.lower() in f"{s['brand']} {s['name']}".lower()]

    if not spirits:
        st.caption("No spirits found." if not is_admin else "No spirits found. Add one above.")
    else:
        for spirit in spirits:
            sid = spirit["id"]
            is_expanded = st.session_state.spirit_expanded_id == sid
            is_tasting  = st.session_state.tasting_id == sid

            with st.container(border=True):
                col1, col2, col3 = st.columns([0.08, 3.5, 1])
                with col1:
                    heart = "❤️" if spirit.get("favorite") else "🤍"
                    if is_admin:
                        if st.button(heart, key=f"sfav_{sid}"):
                            update_spirit(sid, {"favorite": not spirit.get("favorite",False)})
                            st.rerun()
                    else:
                        st.write(heart)
                with col2:
                    wishlist_badge = '<span class="badge-wishlist">Wishlist</span>' if spirit.get("wishlist") else ""
                    tried_badge = '<span class="badge-smoked">Tried</span>' if spirit.get("tried") else ""
                    st.markdown(f"**{spirit['brand']} {spirit['name']}**{wishlist_badge}{tried_badge}", unsafe_allow_html=True)
                    detail = spirit.get("category","")
                    if spirit.get("region"): detail += f" · {spirit['region']}"
                    if spirit.get("age"): detail += f" · {spirit['age']}"
                    if spirit.get("abv"): detail += f" · {spirit['abv']}%"
                    st.caption(detail)
                    if spirit.get("tried") and spirit.get("rating"):
                        st.caption(format_rating(spirit["rating"]))
                with col3:
                    if st.button("▼" if not is_expanded else "▲", key=f"sexp_{sid}"):
                        st.session_state.spirit_expanded_id = None if is_expanded else sid
                        st.session_state.tasting_id = None
                        st.rerun()

                if is_expanded:
                    st.divider()
                    if spirit.get("notes"): st.markdown(f"**Notes** — {spirit['notes']}")
                    if spirit.get("comments"): st.markdown(f"**Comments** — {spirit['comments']}")
                    cols = st.columns(3)
                    if spirit.get("price"): cols[0].caption(f"${spirit['price']:.2f}")
                    if spirit.get("purchase_date"): cols[1].caption(f"Bought {spirit['purchase_date']}")

                    if is_admin:
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if spirit.get("wishlist"):
                                if st.button("Move to Cabinet", key=f"scab_{sid}"):
                                    update_spirit(sid, {"wishlist":False})
                                    st.rerun()
                            if not spirit.get("tried"):
                                if st.button("Mark Tried", key=f"stried_{sid}"):
                                    st.session_state.tasting_id = sid
                                    st.rerun()
                            else:
                                if st.button("Unmark Tried", key=f"suntried_{sid}"):
                                    update_spirit(sid, {"tried":False,"tried_date":"","rating":0.0,"comments":""})
                                    st.rerun()
                        with col_c:
                            if st.button("Delete", key=f"sdel_{sid}"):
                                delete_spirit(sid)
                                st.session_state.spirit_expanded_id = None
                                st.rerun()

                if is_tasting and is_admin:
                    st.divider()
                    with st.form(f"tasting_form_{sid}"):
                        s_rating = st.select_slider("Rating", options=HALF_STARS, value=3.0, format_func=lambda x: f"{x} ⭐")
                        s_comments = st.text_area("Comments", placeholder="Tasting notes…")
                        tried_date = st.date_input("Date tried", value=date.today())
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("Save", type="primary"):
                                update_spirit(sid, {"tried":True,"tried_date":str(tried_date),"rating":float(s_rating),"comments":s_comments,"wishlist":False})
                                st.session_state.tasting_id = None
                                st.rerun()
                        with c2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.tasting_id = None
                                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — JOURNAL
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    j_tab1, j_tab2 = st.tabs(["CIGARS", "SPIRITS"])

    with j_tab1:
        all_cigars = load_cigars()
        smoked = [c for c in all_cigars if c["smoked"]]
        if not smoked:
            st.caption("No smoked cigars yet.")
        else:
            rated = [c for c in smoked if c.get("rating")]
            avg = sum(c["rating"] for c in rated) / len(rated) if rated else 0
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Smoked", len(smoked))
            col2.metric("Avg Rating", f"{avg:.1f}" if avg else "—")
            col3.metric("Unrated", len(smoked)-len(rated))
            col4.metric("Favorites", len([c for c in smoked if c.get("favorite")]))
            st.divider()
            for cigar in sorted(smoked, key=lambda c: c.get("smoked_date") or "", reverse=True):
                with st.container(border=True):
                    col1, col2 = st.columns([3,1])
                    with col1:
                        fav = "❤️ " if cigar.get("favorite") else ""
                        st.markdown(f"{fav}**{cigar['brand']} {cigar['name']}**")
                        st.caption(f"{cigar['vitola']} · {cigar['origin']} · {cigar['strength']}")
                        if cigar.get("notes"): st.write(cigar["notes"])
                        if cigar.get("comments"): st.info(f"💬 {cigar['comments']}")
                    with col2:
                        st.caption(cigar.get("smoked_date") or "")
                        if cigar.get("rating"):
                            st.write(format_rating(cigar["rating"]))
                            st.caption(f"{cigar['rating']} / 5")

    with j_tab2:
        all_spirits = load_spirits()
        tried = [s for s in all_spirits if s.get("tried")]
        if not tried:
            st.caption("No spirits tasted yet.")
        else:
            s_rated = [s for s in tried if s.get("rating")]
            s_avg = sum(s["rating"] for s in s_rated) / len(s_rated) if s_rated else 0
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tried", len(tried))
            col2.metric("Avg Rating", f"{s_avg:.1f}" if s_avg else "—")
            col3.metric("Unrated", len(tried)-len(s_rated))
            col4.metric("Favorites", len([s for s in tried if s.get("favorite")]))
            st.divider()
            for spirit in sorted(tried, key=lambda s: s.get("tried_date") or "", reverse=True):
                with st.container(border=True):
                    col1, col2 = st.columns([3,1])
                    with col1:
                        fav = "❤️ " if spirit.get("favorite") else ""
                        st.markdown(f"{fav}**{spirit['brand']} {spirit['name']}**")
                        st.caption(f"{spirit['category']} · {spirit.get('region','')} · {spirit.get('age','')}")
                        if spirit.get("notes"): st.write(spirit["notes"])
                        if spirit.get("comments"): st.info(f"💬 {spirit['comments']}")
                    with col2:
                        st.caption(spirit.get("tried_date") or "")
                        if spirit.get("rating"):
                            st.write(format_rating(spirit["rating"]))
                            st.caption(f"{spirit['rating']} / 5")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — PAIRINGS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    p_tab1, p_tab2 = st.tabs(["MY PAIRINGS", "CLASSIC GUIDE"])

    with p_tab1:
        all_cigars = load_cigars()
        all_spirits = load_spirits()
        if not all_cigars or not all_spirits:
            st.info("Add cigars and spirits to your collection first.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                cigar_opts = {f"{c['brand']} {c['name']} ({c['vitola']})": c for c in all_cigars}
                sel_cigar = cigar_opts[st.selectbox("Cigar", list(cigar_opts.keys()))]
            with col2:
                spirit_opts = {f"{s['brand']} {s['name']} ({s['category']})": s for s in all_spirits}
                sel_spirit = spirit_opts[st.selectbox("Spirit", list(spirit_opts.keys()))]

            if st.button("Get Pairing Recommendation", type="primary"):
                with st.spinner("Analyzing..."):
                    try:
                        st.session_state.pairing_result = get_pairing(sel_cigar, sel_spirit)
                    except Exception as e:
                        st.error(f"Failed: {e}")

            if "pairing_result" in st.session_state:
                st.divider()
                st.markdown(st.session_state.pairing_result)

    with p_tab2:
        pairings = [
            ("Full-bodied Nicaraguan","Aged Rum or Single Malt Scotch","The earthiness and pepper of a Nicaraguan pairs beautifully with the caramel and oak of aged rum, or the smoky depth of an Islay Scotch."),
            ("Mild Connecticut Shade","Champagne or Light Bourbon","A creamy, mild cigar won't overpower a delicate sparkling wine. A wheated bourbon like Maker's Mark is another great match."),
            ("Maduro Wrapper","Bourbon or Amaro","The natural sweetness of a maduro wrapper echoes the vanilla and caramel in bourbon. An herbal amaro like Averna also complements the dark, earthy notes."),
            ("Cuban-style Corona","Single Malt Scotch (Highland)","A classic pairing — the grassy, floral notes of a Cuban-style cigar balance well against the fruit and honey of a Highland Scotch."),
            ("Cameroon Wrapper","Cognac or Armagnac","The cedar, spice, and sweetness of a Cameroon wrapper is a natural companion to aged French brandy."),
            ("Habano Wrapper","Añejo Tequila or Mezcal","The spice and complexity of a Habano wrapper finds a match in the agave-forward depth of an añejo or the smoky character of a mezcal."),
        ]
        for cigar_type, spirit, description in pairings:
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1: st.markdown(f"🚬 **{cigar_type}**")
                with col2: st.markdown(f"🥃 **{spirit}**")
                st.write(description)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — FOR YOU (RECOMMENDATIONS)
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("### Picked For You")
    st.caption("Based on your highest rated and favorited cigars and spirits.")
    st.divider()

    all_cigars = load_cigars()
    all_spirits = load_spirits()

    top_cigars  = sorted([c for c in all_cigars if c.get("rating")], key=lambda x: x["rating"], reverse=True)[:3]
    fav_cigars  = [c for c in all_cigars if c.get("favorite")][:3]
    top_spirits = sorted([s for s in all_spirits if s.get("rating")], key=lambda x: x["rating"], reverse=True)[:3]
    fav_spirits = [s for s in all_spirits if s.get("favorite")][:3]

    has_data = top_cigars or fav_cigars or top_spirits or fav_spirits

    if not has_data:
        st.info("Rate some cigars and spirits, or mark some as favorites, and Claude will recommend what to try next.")
    else:
        if top_cigars or fav_cigars:
            st.markdown("**Your Taste Profile — Cigars**")
            cols = st.columns(min(3, max(len(top_cigars), 1)))
            for i, c in enumerate(top_cigars):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{c['brand']}**")
                        st.caption(c['name'])
                        st.write(format_rating(c['rating']))

        st.divider()

        if top_spirits or fav_spirits:
            st.markdown("**Your Taste Profile — Spirits**")
            cols = st.columns(min(3, max(len(top_spirits), 1)))
            for i, s in enumerate(top_spirits):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{s['brand']}**")
                        st.caption(s['name'])
                        st.write(format_rating(s['rating']))

        st.divider()

        if st.button("Generate My Recommendations", type="primary"):
            with st.spinner("Claude is analyzing your taste profile..."):
                try:
                    st.session_state.recommendations = get_recommendations(top_cigars, fav_cigars, top_spirits, fav_spirits)
                except Exception as e:
                    st.error(f"Failed: {e}")

        if "recommendations" in st.session_state:
            st.divider()
            st.markdown(st.session_state.recommendations)
