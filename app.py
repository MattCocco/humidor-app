import streamlit as st
import json
import os
from datetime import date
import anthropic

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Humidor", page_icon="🥃", layout="centered")

# ── Password / session state ──────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "smoking_id" not in st.session_state:
    st.session_state.smoking_id = None
if "expanded_id" not in st.session_state:
    st.session_state.expanded_id = None

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

# ── Data helpers ──────────────────────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"cigars": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_cigar_index(data, cigar_id):
    for i, c in enumerate(data["cigars"]):
        if c["id"] == cigar_id:
            return i
    return None

# ── Claude AI helper ──────────────────────────────────────────────────────────
def lookup_cigar(brand, name):
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

# ── Constants ─────────────────────────────────────────────────────────────────
VITOLAS   = ["Robusto","Toro","Churchill","Corona","Lonsdale","Belicoso","Torpedo","Lancero","Petite Corona","Gordo"]
WRAPPERS  = ["Colorado Claro","Colorado","Colorado Maduro","Maduro","Natural","Claro","Oscuro","Candela"]
ORIGINS   = ["Nicaragua","Cuba","Dominican Republic","Honduras","Ecuador","Mexico","Cameroon","USA","Panama","Brazil"]
STRENGTHS = ["Mild","Mild-Medium","Medium","Medium-Full","Full"]
HALF_STARS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

def format_rating(rating):
    if not rating:
        return "—"
    full = int(rating)
    half = rating - full >= 0.5
    return "⭐" * full + ("½" if half else "")

# ── Load data ─────────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🥃 Humidor")
st.caption("Your personal cigar journal")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Humidor", "Tasting Journal", "Pairings"])

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
                        price    = st.number_input("Price per stick ($)", min_value=0.0, step=0.50)

                    purchase_date = st.date_input("Purchase date", value=date.today())
                    notes = st.text_area("Tasting notes", value=r.get("description", ""), placeholder="Flavors, aroma, construction…")

                    submitted = st.form_submit_button("Save Cigar", type="primary")
                    if submitted:
                        new_cigar = {
                            "id": int(date.today().strftime("%Y%m%d%H%M%S") + str(len(data["cigars"]))),
                            "brand": st.session_state.lookup_brand,
                            "name": st.session_state.lookup_name,
                            "vitola": vitola, "wrapper": wrapper,
                            "origin": origin, "strength": strength,
                            "qty": qty, "price": price, "notes": notes,
                            "purchase_date": str(purchase_date),
                            "smoked": False, "rating": 0,
                            "smoked_date": "", "comments": "",
                            "favorite": False
                        }
                        data["cigars"].append(new_cigar)
                        save_data(data)
                        del st.session_state.lookup_result
                        st.success(f"Added {st.session_state.lookup_brand} {st.session_state.lookup_name}!")
                        st.rerun()

    st.divider()

    # Filter + search
    filter_opt = st.radio("Show", ["All", "In Humidor", "Smoked", "Favorites"], horizontal=True)
    search = st.text_input("Search", placeholder="Search by brand or name…")

    cigars = data["cigars"]
    if filter_opt == "In Humidor":
        cigars = [c for c in cigars if not c["smoked"]]
    elif filter_opt == "Smoked":
        cigars = [c for c in cigars if c["smoked"]]
    elif filter_opt == "Favorites":
        cigars = [c for c in cigars if c.get("favorite")]
    if search:
        cigars = [c for c in cigars if search.lower() in f"{c['brand']} {c['name']}".lower()]

    if not cigars:
        st.info("No cigars found. Add one above!" if is_admin else "The humidor is empty.")
    else:
        for cigar in cigars:
            cid = cigar["id"]
            is_expanded = st.session_state.expanded_id == cid
            is_smoking  = st.session_state.smoking_id == cid

            # ── Cigar row ──
            with st.container(border=True):
                col1, col2, col3 = st.columns([0.08, 3.5, 1])

                # Favorite heart
                with col1:
                    heart = "❤️" if cigar.get("favorite") else "🤍"
                    if is_admin:
                        if st.button(heart, key=f"fav_{cid}", help="Toggle favorite"):
                            idx = get_cigar_index(data, cid)
                            data["cigars"][idx]["favorite"] = not cigar.get("favorite", False)
                            save_data(data)
                            st.rerun()
                    else:
                        st.write(heart)

                # Cigar info
                with col2:
                    name_label = f"**{cigar['brand']} {cigar['name']}**"
                    detail_line = f"{cigar['vitola']} · {cigar['origin']} · {cigar['wrapper']} · {cigar['strength']}"
                    st.markdown(name_label)
                    st.caption(detail_line)
                    if cigar["smoked"] and cigar.get("rating"):
                        st.caption(f"{format_rating(cigar['rating'])} · Smoked {cigar['smoked_date']}")

                # Expand toggle
                with col3:
                    expand_label = "▲ Less" if is_expanded else "▼ Details"
                    if st.button(expand_label, key=f"exp_{cid}"):
                        st.session_state.expanded_id = None if is_expanded else cid
                        st.session_state.smoking_id = None
                        st.rerun()

                # ── Expanded detail panel ──
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
                                    idx = get_cigar_index(data, cid)
                                    data["cigars"][idx]["smoked"] = False
                                    data["cigars"][idx]["smoked_date"] = ""
                                    data["cigars"][idx]["rating"] = 0
                                    data["cigars"][idx]["comments"] = ""
                                    save_data(data)
                                    st.rerun()
                        with col_c:
                            if st.button("🗑 Delete", key=f"del_{cid}"):
                                data["cigars"] = [c for c in data["cigars"] if c["id"] != cid]
                                save_data(data)
                                st.session_state.expanded_id = None
                                st.rerun()

                # ── Smoke rating panel ──
                if is_smoking and is_admin:
                    st.divider()
                    st.markdown("**How was it? Log your smoke:**")
                    with st.form(f"smoke_form_{cid}"):
                        rating = st.select_slider(
                            "Rating",
                            options=HALF_STARS,
                            value=3.0,
                            format_func=lambda x: f"{x} ⭐"
                        )
                        comments = st.text_area("Personal comments", placeholder="e.g. Great smoke for the price, fantastic draw, pepper on the finish…")
                        smoked_date = st.date_input("Date smoked", value=date.today())
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_smoke = st.form_submit_button("Save", type="primary")
                        with col_cancel:
                            cancel = st.form_submit_button("Cancel")

                        if save_smoke:
                            idx = get_cigar_index(data, cid)
                            data["cigars"][idx]["smoked"] = True
                            data["cigars"][idx]["smoked_date"] = str(smoked_date)
                            data["cigars"][idx]["rating"] = rating
                            data["cigars"][idx]["comments"] = comments
                            save_data(data)
                            st.session_state.smoking_id = None
                            st.rerun()
                        if cancel:
                            st.session_state.smoking_id = None
                            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — TASTING JOURNAL
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Tasting Journal")

    smoked = [c for c in data["cigars"] if c["smoked"]]

    if not smoked:
        st.info("No smoked cigars yet. Mark a cigar as smoked from the Humidor tab.")
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

        st.markdown("**All entries:**")
        for cigar in sorted(smoked, key=lambda c: c.get("smoked_date", ""), reverse=True):
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
                    st.caption(cigar.get("smoked_date", ""))
                    if cigar.get("rating"):
                        st.write(format_rating(cigar["rating"]))
                        st.caption(f"{cigar['rating']} / 5")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PAIRINGS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Pairing Guide")
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
