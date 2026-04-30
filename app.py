import streamlit as st
from datetime import date
import anthropic
from supabase import create_client

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="The Cabinet", page_icon="🥃", layout="centered")

# ── Supabase client ───────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ── Data helpers — cigars ─────────────────────────────────────────────────────
def load_cigars():
    res = supabase.table("cigars").select("*").order("id").execute()
    return res.data or []

def add_cigar(cigar):
    supabase.table("cigars").insert(cigar).execute()

def update_cigar(cid, updates):
    supabase.table("cigars").update(updates).eq("id", cid).execute()

def delete_cigar(cid):
    supabase.table("cigars").delete().eq("id", cid).execute()

# ── Data helpers — spirits ────────────────────────────────────────────────────
def load_spirits():
    res = supabase.table("spirits").select("*").order("id").execute()
    return res.data or []

def add_spirit(spirit):
    supabase.table("spirits").insert(spirit).execute()

def update_spirit(sid, updates):
    supabase.table("spirits").update(updates).eq("id", sid).execute()

def delete_spirit(sid):
    supabase.table("spirits").delete().eq("id", sid).execute()

# ── Password / session state ──────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "smoking_id" not in st.session_state:
    st.session_state.smoking_id = None
if "expanded_id" not in st.session_state:
    st.session_state.expanded_id = None
if "spirit_expanded_id" not in st.session_state:
    st.session_state.spirit_expanded_id = None
if "tasting_id" not in st.session_state:
    st.session_state.tasting_id = None

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

# ── Claude AI — cigar lookup ──────────────────────────────────────────────────
def lookup_cigar(brand, name):
    import json
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""I have a cigar: Brand: {brand}, Name/Line: {name}

Please return ONLY a JSON object with these exact fields, no other text:
{{
  "vitola": "most common vitola for this cigar",
  "wrapper": "wrapper type from this list: Colorado Claro, Colorado, Colorado Maduro, Maduro, Natural, Claro, Oscuro, Candela",
  "origin": "country from this list: Nicaragua, Cuba, Dominican Republic, Honduras, Ecuador, Mexico, Cameroon, USA, Panama, Brazil",
  "strength": "from this list: Mild, Mild-Medium, Medium, Medium-Full, Full",
  "description": "2 sentence tasting note description"
}}

If you don't recognize the cigar, make your best guess based on the brand origin and style."""
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

# ── Claude AI — spirit lookup ─────────────────────────────────────────────────
def lookup_spirit(brand, name):
    import json
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""I have a spirit: Brand: {brand}, Name/Expression: {name}

Please return ONLY a JSON object with these exact fields, no other text:
{{
  "category": "category from this list: Scotch Whisky, Bourbon, Irish Whiskey, Japanese Whisky, Amaro, Rum, Mezcal, Tequila, Cognac, Armagnac, Port, Sherry, Other",
  "region": "region or origin (e.g. Islay, Speyside, Highland, Kentucky, Jalisco, etc.)",
  "age": "age statement if known, e.g. 12 Year, 18 Year, NAS",
  "abv": "ABV as a number e.g. 46.0",
  "description": "2 sentence tasting note description covering key flavors and character"
}}

If you don't recognize the spirit, make your best guess based on the brand."""
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

# ── Claude AI — cigar + spirit pairing ───────────────────────────────────────
def get_pairing(cigar, spirit):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""I'm pairing a cigar with a spirit. Tell me how well they go together and why.

Cigar: {cigar['brand']} {cigar['name']} ({cigar['vitola']}, {cigar['wrapper']} wrapper, {cigar['origin']}, {cigar['strength']} strength)
Spirit: {spirit['brand']} {spirit['name']} ({spirit['category']}, {spirit.get('region','')}, {spirit.get('age','')})

Please give:
1. A pairing rating: Excellent / Good / Decent / Not Recommended
2. A 2-3 sentence explanation of why they do or don't work together
3. One tip for getting the most out of this pairing (e.g. when to sip, how to prepare)

Be direct and opinionated."""
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()

# ── Constants ─────────────────────────────────────────────────────────────────
VITOLAS    = ["Robusto","Toro","Churchill","Corona","Lonsdale","Belicoso","Torpedo","Lancero","Petite Corona","Gordo"]
WRAPPERS   = ["Colorado Claro","Colorado","Colorado Maduro","Maduro","Natural","Claro","Oscuro","Candela"]
ORIGINS    = ["Nicaragua","Cuba","Dominican Republic","Honduras","Ecuador","Mexico","Cameroon","USA","Panama","Brazil"]
STRENGTHS  = ["Mild","Mild-Medium","Medium","Medium-Full","Full"]
CATEGORIES = ["Scotch Whisky","Bourbon","Irish Whiskey","Japanese Whisky","Amaro","Rum","Mezcal","Tequila","Cognac","Armagnac","Port","Sherry","Other"]
HALF_STARS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

def format_rating(rating):
    if not rating:
        return "—"
    full = int(rating)
    half = rating - full >= 0.5
    return "⭐" * full + ("½" if half else "")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🥃 The Cabinet")
st.caption("Your personal cigar & spirits journal")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Humidor", "Liquor Cabinet", "Tasting Journal", "Pairings", "For You"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — HUMIDOR
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("My Humidor")

    if is_admin:
        with st.expander("➕ Add a new cigar"):
            with st.form("lookup_form"):
                col1, col2 = st.columns(2)
                with col1:
                    brand = st.text_input("Brand *", placeholder="e.g. Padron")
                with col2:
                    name = st.text_input("Name / Line *", placeholder="e.g. 1964 Anniversary")
                lookup = st.form_submit_button("🔍 Look up cigar details")

            if lookup and brand and name:
                with st.spinner("Looking up cigar details..."):
                    try:
                        result = lookup_cigar(brand, name)
                        st.session_state.lookup_result = result
                        st.session_state.lookup_brand = brand
                        st.session_state.lookup_name = name
                        st.success("Details found! Review and save below.")
                    except Exception as e:
                        st.error(f"Lookup failed: {e}. Please try again.")
                        st.session_state.lookup_result = None

            if "lookup_result" in st.session_state and st.session_state.lookup_result:
                r = st.session_state.lookup_result
                st.markdown("**Review details:**")
                with st.form("add_cigar"):
                    col1, col2 = st.columns(2)
                    with col1:
                        vitola   = st.selectbox("Vitola",   VITOLAS,   index=VITOLAS.index(r.get("vitola", VITOLAS[0])) if r.get("vitola") in VITOLAS else 0)
                        origin   = st.selectbox("Origin",   ORIGINS,   index=ORIGINS.index(r.get("origin", ORIGINS[0])) if r.get("origin") in ORIGINS else 0)
                        qty      = st.number_input("Qty in humidor", min_value=0, value=1)
                    with col2:
                        wrapper  = st.selectbox("Wrapper",  WRAPPERS,  index=WRAPPERS.index(r.get("wrapper", WRAPPERS[0])) if r.get("wrapper") in WRAPPERS else 0)
                        strength = st.selectbox("Strength", STRENGTHS, index=STRENGTHS.index(r.get("strength", STRENGTHS[0])) if r.get("strength") in STRENGTHS else 0)
                        price    = st.number_input("Price per bottle ($)", min_value=0.0, step=0.50)

                    purchase_date = st.date_input("Purchase date", value=date.today())
                    notes = st.text_area("Tasting notes", value=r.get("description", ""), placeholder="Flavors, aroma, construction…")

                    submitted = st.form_submit_button("Save Cigar", type="primary")
                    if submitted:
                        new_cigar = {
                            "brand": st.session_state.lookup_brand,
                            "name": st.session_state.lookup_name,
                            "vitola": vitola, "wrapper": wrapper,
                            "origin": origin, "strength": strength,
                            "qty": int(qty), "price": float(price),
                            "notes": notes, "comments": "",
                            "purchase_date": str(purchase_date),
                            "smoked": False, "rating": 0.0,
                            "smoked_date": "", "favorite": False
                        }
                        add_cigar(new_cigar)
                        del st.session_state.lookup_result
                        st.success(f"Added {st.session_state.lookup_brand} {st.session_state.lookup_name}!")
                        st.rerun()

    st.divider()

    filter_opt = st.radio("Show", ["In Humidor", "Smoked", "Favorites", "All"], horizontal=True, key="cigar_filter")
    search = st.text_input("Search", placeholder="e.g. Padron anniversario, nicaraguan robusto…", key="cigar_search")

cigars = load_cigars()
if filter_opt == "In Humidor":
    cigars = [c for c in cigars if not c["smoked"]]
elif filter_opt == "Smoked":
    cigars = [c for c in cigars if c["smoked"]]
elif filter_opt == "Favorites":
    cigars = [c for c in cigars if c.get("favorite")]

if search:
    search_terms = search.lower().split()
    def match_score(cigar):
        haystack = f"{cigar['brand']} {cigar['name']} {cigar['vitola']} {cigar['origin']} {cigar['wrapper']} {cigar['strength']}".lower()
        return sum(1 for term in search_terms if term in haystack)
    scored = [(c, match_score(c)) for c in cigars]
    scored = [(c, s) for c, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    if scored:
        best_score = scored[0][1]
        best_matches = [c for c, s in scored if s == best_score]
        if len(best_matches) == 1 and best_score < len(search_terms):
            st.info(f"Best match found for \"{search}\" — not quite right? Try different keywords.")
        cigars = [c for c, s in scored]
    else:
        st.warning(f"No matches found for \"{search}\". Try fewer or different keywords.")
        cigars = []

    if not cigars:
        st.info("No cigars found. Add one above!" if is_admin else "The humidor is empty.")
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
                        if st.button(heart, key=f"fav_{cid}", help="Toggle favorite"):
                            update_cigar(cid, {"favorite": not cigar.get("favorite", False)})
                            st.rerun()
                    else:
                        st.write(heart)

                with col2:
                    st.markdown(f"**{cigar['brand']} {cigar['name']}**")
                    st.caption(f"{cigar['vitola']} · {cigar['origin']} · {cigar['wrapper']} · {cigar['strength']}")
                    if cigar["smoked"] and cigar.get("rating"):
                        st.caption(f"{format_rating(cigar['rating'])} · Smoked {cigar['smoked_date']}")

                with col3:
                    expand_label = "▲ Less" if is_expanded else "▼ Details"
                    if st.button(expand_label, key=f"exp_{cid}"):
                        st.session_state.expanded_id = None if is_expanded else cid
                        st.session_state.smoking_id = None
                        st.rerun()

                if is_expanded:
                    st.divider()
                    if cigar.get("notes"):
                        st.markdown(f"📝 **Tasting notes:** {cigar['notes']}")
                    if cigar.get("comments"):
                        st.markdown(f"💬 **My comments:** {cigar['comments']}")
                    if cigar.get("price"):
                        st.caption(f"Price: ${cigar['price']:.2f}/stick")
                    if cigar.get("purchase_date"):
                        st.caption(f"Purchased: {cigar['purchase_date']}")
                    if cigar.get("qty") is not None:
                        st.caption(f"In humidor: {cigar['qty']}")

                    if is_admin:
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if not cigar["smoked"]:
                                if st.button("✅ Mark Smoked", key=f"smoke_{cid}"):
                                    st.session_state.smoking_id = cid
                                    st.rerun()
                            else:
                                if st.button("↩️ Unmark Smoked", key=f"unsmoke_{cid}"):
                                    update_cigar(cid, {
                                        "smoked": False,
                                        "smoked_date": "",
                                        "rating": 0.0,
                                        "comments": ""
                                    })
                                    st.rerun()
                        with col_c:
                            if st.button("🗑 Delete", key=f"del_{cid}"):
                                delete_cigar(cid)
                                st.session_state.expanded_id = None
                                st.rerun()

                if is_smoking and is_admin:
                    st.divider()
                    st.markdown("**How was it? Log your smoke:**")
                    with st.form(f"smoke_form_{cid}"):
                        rating = st.select_slider("Rating", options=HALF_STARS, value=3.0, format_func=lambda x: f"{x} ⭐")
                        comments = st.text_area("Personal comments", placeholder="e.g. Great smoke for the price, fantastic draw…")
                        smoked_date = st.date_input("Date smoked", value=date.today())
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_smoke = st.form_submit_button("Save", type="primary")
                        with col_cancel:
                            cancel = st.form_submit_button("Cancel")
                        if save_smoke:
                            update_cigar(cid, {
                                "smoked": True,
                                "smoked_date": str(smoked_date),
                                "rating": float(rating),
                                "comments": comments
                            })
                            st.session_state.smoking_id = None
                            st.rerun()
                        if cancel:
                            st.session_state.smoking_id = None
                            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — LIQUOR CABINET
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("My Liquor Cabinet")

    if is_admin:
        with st.expander("➕ Add a new spirit"):
            with st.form("spirit_lookup_form"):
                col1, col2 = st.columns(2)
                with col1:
                    s_brand = st.text_input("Brand *", placeholder="e.g. Lagavulin")
                with col2:
                    s_name = st.text_input("Name / Expression *", placeholder="e.g. 16 Year")
                is_wishlist = st.checkbox("Add to wishlist only (haven't bought yet)")
                s_lookup = st.form_submit_button("🔍 Look up spirit details")

            if s_lookup and s_brand and s_name:
                with st.spinner("Looking up spirit details..."):
                    try:
                        s_result = lookup_spirit(s_brand, s_name)
                        st.session_state.spirit_lookup_result = s_result
                        st.session_state.spirit_lookup_brand = s_brand
                        st.session_state.spirit_lookup_name = s_name
                        st.session_state.spirit_lookup_wishlist = is_wishlist
                        st.success("Details found! Review and save below.")
                    except Exception as e:
                        st.error(f"Lookup failed: {e}. Please try again.")
                        st.session_state.spirit_lookup_result = None

            if "spirit_lookup_result" in st.session_state and st.session_state.spirit_lookup_result:
                r = st.session_state.spirit_lookup_result
                st.markdown("**Review details:**")
                with st.form("add_spirit"):
                    col1, col2 = st.columns(2)
                    with col1:
                        s_category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(r.get("category", CATEGORIES[0])) if r.get("category") in CATEGORIES else 0)
                        s_age      = st.text_input("Age", value=r.get("age", ""))
                        s_price    = st.number_input("Price ($)", min_value=0.0, step=1.0)
                    with col2:
                        s_region   = st.text_input("Region", value=r.get("region", ""))
                        s_abv      = st.number_input("ABV (%)", min_value=0.0, max_value=100.0, value=float(r.get("abv", 40.0)), step=0.5)
                        s_purchase_date = st.date_input("Purchase date", value=date.today())

                    s_notes = st.text_area("Tasting notes", value=r.get("description", ""), placeholder="Flavors, aroma, finish…")

                    s_submitted = st.form_submit_button("Save Spirit", type="primary")
                    if s_submitted:
                        new_spirit = {
                            "brand": st.session_state.spirit_lookup_brand,
                            "name": st.session_state.spirit_lookup_name,
                            "category": s_category,
                            "region": s_region,
                            "age": s_age,
                            "abv": float(s_abv),
                            "price": float(s_price),
                            "notes": s_notes,
                            "comments": "",
                            "purchase_date": str(s_purchase_date),
                            "tried": False,
                            "tried_date": "",
                            "rating": 0.0,
                            "favorite": False,
                            "wishlist": st.session_state.spirit_lookup_wishlist
                        }
                        add_spirit(new_spirit)
                        del st.session_state.spirit_lookup_result
                        st.success(f"Added {st.session_state.spirit_lookup_brand} {st.session_state.spirit_lookup_name}!")
                        st.rerun()

    st.divider()

    s_filter = st.radio("Show", ["All", "In Cabinet", "Wishlist", "Tried", "Favorites"], horizontal=True, key="spirit_filter")
    s_search = st.text_input("Search", placeholder="Search by brand or name…", key="spirit_search")

    spirits = load_spirits()
    if s_filter == "In Cabinet":
        spirits = [s for s in spirits if not s.get("wishlist") and not s.get("tried")]
    elif s_filter == "Wishlist":
        spirits = [s for s in spirits if s.get("wishlist")]
    elif s_filter == "Tried":
        spirits = [s for s in spirits if s.get("tried")]
    elif s_filter == "Favorites":
        spirits = [s for s in spirits if s.get("favorite")]
    if s_search:
        spirits = [s for s in spirits if s_search.lower() in f"{s['brand']} {s['name']}".lower()]

    if not spirits:
        st.info("No spirits found. Add one above!" if is_admin else "The cabinet is empty.")
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
                        if st.button(heart, key=f"sfav_{sid}", help="Toggle favorite"):
                            update_spirit(sid, {"favorite": not spirit.get("favorite", False)})
                            st.rerun()
                    else:
                        st.write(heart)

                with col2:
                    wishlist_badge = " 🔖" if spirit.get("wishlist") else ""
                    st.markdown(f"**{spirit['brand']} {spirit['name']}**{wishlist_badge}")
                    detail = spirit.get("category", "")
                    if spirit.get("region"):
                        detail += f" · {spirit['region']}"
                    if spirit.get("age"):
                        detail += f" · {spirit['age']}"
                    if spirit.get("abv"):
                        detail += f" · {spirit['abv']}%"
                    st.caption(detail)
                    if spirit.get("tried") and spirit.get("rating"):
                        st.caption(f"{format_rating(spirit['rating'])} · Tried {spirit.get('tried_date','')}")

                with col3:
                    expand_label = "▲ Less" if is_expanded else "▼ Details"
                    if st.button(expand_label, key=f"sexp_{sid}"):
                        st.session_state.spirit_expanded_id = None if is_expanded else sid
                        st.session_state.tasting_id = None
                        st.rerun()

                if is_expanded:
                    st.divider()
                    if spirit.get("notes"):
                        st.markdown(f"📝 **Tasting notes:** {spirit['notes']}")
                    if spirit.get("comments"):
                        st.markdown(f"💬 **My comments:** {spirit['comments']}")
                    if spirit.get("price"):
                        st.caption(f"Price: ${spirit['price']:.2f}")
                    if spirit.get("purchase_date"):
                        st.caption(f"Purchased: {spirit['purchase_date']}")
                    if spirit.get("wishlist"):
                        st.caption("🔖 On your wishlist")

                    if is_admin:
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if spirit.get("wishlist"):
                                if st.button("✅ Move to Cabinet", key=f"scabinet_{sid}"):
                                    update_spirit(sid, {"wishlist": False})
                                    st.rerun()
                            if not spirit.get("tried"):
                                if st.button("🥃 Mark Tried", key=f"stried_{sid}"):
                                    st.session_state.tasting_id = sid
                                    st.rerun()
                            else:
                                if st.button("↩️ Unmark Tried", key=f"suntried_{sid}"):
                                    update_spirit(sid, {
                                        "tried": False,
                                        "tried_date": "",
                                        "rating": 0.0,
                                        "comments": ""
                                    })
                                    st.rerun()
                        with col_c:
                            if st.button("🗑 Delete", key=f"sdel_{sid}"):
                                delete_spirit(sid)
                                st.session_state.spirit_expanded_id = None
                                st.rerun()

                if is_tasting and is_admin:
                    st.divider()
                    st.markdown("**How was it? Log your tasting:**")
                    with st.form(f"tasting_form_{sid}"):
                        s_rating = st.select_slider("Rating", options=HALF_STARS, value=3.0, format_func=lambda x: f"{x} ⭐")
                        s_comments = st.text_area("Personal comments", placeholder="e.g. Incredibly smooth, notes of vanilla and oak…")
                        tried_date = st.date_input("Date tried", value=date.today())
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_tasting = st.form_submit_button("Save", type="primary")
                        with col_cancel:
                            s_cancel = st.form_submit_button("Cancel")
                        if save_tasting:
                            update_spirit(sid, {
                                "tried": True,
                                "tried_date": str(tried_date),
                                "rating": float(s_rating),
                                "comments": s_comments,
                                "wishlist": False
                            })
                            st.session_state.tasting_id = None
                            st.rerun()
                        if s_cancel:
                            st.session_state.tasting_id = None
                            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — TASTING JOURNAL
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Tasting Journal")

    j_tab1, j_tab2 = st.tabs(["Cigars", "Spirits"])

    with j_tab1:
        all_cigars = load_cigars()
        smoked = [c for c in all_cigars if c["smoked"]]

        if not smoked:
            st.info("No smoked cigars yet.")
        else:
            rated = [c for c in smoked if c.get("rating")]
            avg = sum(c["rating"] for c in rated) / len(rated) if rated else 0
            favorites = [c for c in smoked if c.get("favorite")]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Smoked", len(smoked))
            col2.metric("Avg Rating", f"{avg:.1f} / 5" if avg else "—")
            col3.metric("Unrated", len(smoked) - len(rated))
            col4.metric("Favorites", len(favorites))
            st.divider()

            for cigar in sorted(smoked, key=lambda c: c.get("smoked_date") or "", reverse=True):
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        fav = "❤️ " if cigar.get("favorite") else ""
                        st.markdown(f"{fav}**{cigar['brand']} {cigar['name']}**")
                        st.caption(f"{cigar['vitola']} · {cigar['origin']} · {cigar['strength']}")
                        if cigar.get("notes"):
                            st.write(cigar["notes"])
                        if cigar.get("comments"):
                            st.info(f"💬 {cigar['comments']}")
                    with col2:
                        st.caption(cigar.get("smoked_date") or "")
                        if cigar.get("rating"):
                            st.write(format_rating(cigar["rating"]))
                            st.caption(f"{cigar['rating']} / 5")

    with j_tab2:
        all_spirits = load_spirits()
        tried = [s for s in all_spirits if s.get("tried")]

        if not tried:
            st.info("No spirits tasted yet.")
        else:
            s_rated = [s for s in tried if s.get("rating")]
            s_avg = sum(s["rating"] for s in s_rated) / len(s_rated) if s_rated else 0
            s_favorites = [s for s in tried if s.get("favorite")]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Tried", len(tried))
            col2.metric("Avg Rating", f"{s_avg:.1f} / 5" if s_avg else "—")
            col3.metric("Unrated", len(tried) - len(s_rated))
            col4.metric("Favorites", len(s_favorites))
            st.divider()

            for spirit in sorted(tried, key=lambda s: s.get("tried_date") or "", reverse=True):
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        fav = "❤️ " if spirit.get("favorite") else ""
                        st.markdown(f"{fav}**{spirit['brand']} {spirit['name']}**")
                        st.caption(f"{spirit['category']} · {spirit.get('region','')} · {spirit.get('age','')}")
                        if spirit.get("notes"):
                            st.write(spirit["notes"])
                        if spirit.get("comments"):
                            st.info(f"💬 {spirit['comments']}")
                    with col2:
                        st.caption(spirit.get("tried_date") or "")
                        if spirit.get("rating"):
                            st.write(format_rating(spirit["rating"]))
                            st.caption(f"{spirit['rating']} / 5")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — PAIRINGS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Pairings")

    p_tab1, p_tab2 = st.tabs(["My Pairings", "Classic Guide"])

    with p_tab1:
        st.markdown("Choose a cigar from your humidor and type in any spirit — great for cigar bars or bottle shops.")

        all_cigars = load_cigars()

        if not all_cigars:
            st.info("Add cigars to your humidor first.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                cigar_options = {f"{c['brand']} {c['name']} ({c['vitola']})": c for c in all_cigars}
                selected_cigar_key = st.selectbox("Choose a cigar", list(cigar_options.keys()))
                selected_cigar = cigar_options[selected_cigar_key]
            with col2:
                spirit_query = st.text_input("Type any spirit", placeholder="e.g. Lagavulin 16, Averna Amaro, Blanton's…")

            if st.button("🔍 Get Pairing Recommendation", type="primary"):
                if not spirit_query:
                    st.warning("Please enter a spirit name.")
                else:
                    with st.spinner("Analyzing pairing..."):
                        try:
                            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                            prompt = f"""I'm pairing a cigar with a spirit. Tell me how well they go together.

Cigar: {selected_cigar['brand']} {selected_cigar['name']} ({selected_cigar['vitola']}, {selected_cigar['wrapper']} wrapper, {selected_cigar['origin']}, {selected_cigar['strength']} strength)
Spirit: {spirit_query}

Please give:
1. A pairing rating: Excellent / Good / Decent / Not Recommended
2. A 2-3 sentence explanation of why they do or don't work together
3. One tip for getting the most out of this pairing

Be direct and opinionated."""
                            message = client.messages.create(
                                model="claude-opus-4-6",
                                max_tokens=300,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            st.session_state.pairing_result = message.content[0].text.strip()
                            st.session_state.pairing_spirit_query = spirit_query
                            st.session_state.pairing_cigar = selected_cigar
                        except Exception as e:
                            st.error(f"Failed: {e}")

            if "pairing_result" in st.session_state:
                st.divider()
                st.markdown(st.session_state.pairing_result)

                if is_admin:
                    st.divider()
                    st.markdown("**Want to add this spirit to your cabinet?**")
                    with st.form("add_pairing_spirit"):
                        col1, col2 = st.columns(2)
                        with col1:
                            add_cat   = st.selectbox("Category", CATEGORIES)
                            add_region = st.text_input("Region", placeholder="e.g. Islay, Kentucky…")
                            add_price  = st.number_input("Price ($)", min_value=0.0, step=1.0)
                        with col2:
                            add_age   = st.text_input("Age", placeholder="e.g. 16 Year, NAS")
                            add_abv   = st.number_input("ABV (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.5)
                            add_wish  = st.checkbox("Add to wishlist only")
                        add_notes = st.text_area("Notes", placeholder="Tasting notes…")
                        if st.form_submit_button("Add to Cabinet", type="primary"):
                            parts = st.session_state.pairing_spirit_query.strip().rsplit(" ", 1)
                            s_brand = parts[0] if len(parts) > 1 else st.session_state.pairing_spirit_query
                            s_name  = parts[1] if len(parts) > 1 else ""
                            add_spirit({
                                "brand": s_brand,
                                "name": s_name,
                                "category": add_cat,
                                "region": add_region,
                                "age": add_age,
                                "abv": float(add_abv),
                                "price": float(add_price),
                                "notes": add_notes,
                                "comments": "",
                                "purchase_date": str(date.today()),
                                "tried": False,
                                "tried_date": "",
                                "rating": 0.0,
                                "favorite": False,
                                "wishlist": add_wish
                            })
                            st.success(f"Added {st.session_state.pairing_spirit_query} to your cabinet!")

    with p_tab2:
        st.caption("Classic cigar & spirit pairings to inspire your next smoke.")

        pairings = [
            ("Full-bodied Nicaraguan", "Aged Rum or Single Malt Scotch", "The earthiness and pepper of a Nicaraguan pairs beautifully with the caramel and oak of aged rum, or the smoky depth of an Islay Scotch."),
            ("Mild Connecticut Shade", "Champagne or Light Bourbon", "A creamy, mild cigar won't overpower a delicate sparkling wine. A wheated bourbon like Maker's Mark is another great match."),
            ("Maduro Wrapper", "Bourbon or Amaro", "The natural sweetness of a maduro wrapper echoes the vanilla and caramel in bourbon. An herbal amaro like Averna also complements the dark, earthy notes."),
            ("Cuban-style Corona", "Single Malt Scotch (Highland)", "A classic pairing — the grassy, floral notes of a Cuban-style cigar balance well against the fruit and honey of a Highland Scotch like Dalmore or Glenmorangie."),
            ("Cameroon Wrapper", "Cognac or Armagnac", "The cedar, spice, and sweetness of a Cameroon wrapper is a natural companion to aged French brandy — a true old-world combination."),
            ("Habano Wrapper", "Añejo Tequila or Mezcal", "The spice and complexity of a Habano wrapper finds a match in the agave-forward depth of an añejo or the smoky character of a mezcal."),
        ]

        for cigar_type, spirit, description in pairings:
            with st.container(border=True):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"🚬 **{cigar_type}**")
                with col2:
                    st.markdown(f"🥃 **{spirit}**")
                st.write(description)
                
# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — FOR YOU (RECOMMENDATIONS)
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Picked For You")
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
        if top_cigars:
            st.markdown("**Your Top Cigars**")
            cols = st.columns(len(top_cigars))
            for i, c in enumerate(top_cigars):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{c['brand']}**")
                        st.caption(c['name'])
                        st.write(format_rating(c['rating']))

        if top_spirits:
            st.markdown("**Your Top Spirits**")
            cols = st.columns(len(top_spirits))
            for i, s in enumerate(top_spirits):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{s['brand']}**")
                        st.caption(s['name'])
                        st.write(format_rating(s['rating']))

        st.divider()

        if st.button("✨ Generate My Recommendations", type="primary"):
            with st.spinner("Claude is analyzing your taste profile..."):
                try:
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
3. **One Bold Suggestion** — something slightly outside their comfort zone that you think they'd love, with a compelling reason

Be specific, opinionated, and knowledgeable. Write like a trusted expert who knows their palate well."""

                    message = client.messages.create(
                        model="claude-opus-4-6",
                        max_tokens=600,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state.recommendations = message.content[0].text.strip()
                except Exception as e:
                    st.error(f"Failed: {e}")

        if "recommendations" in st.session_state:
            st.divider()
            st.markdown(st.session_state.recommendations)
