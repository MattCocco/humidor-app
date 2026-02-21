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
    # Strip markdown code fences if present
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
            # Step 1 — brand and name lookup
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
                        st.error(f"Lookup failed: {e}. Please fill in details manually.")
                        st.session_state.lookup_result = None

            # Step 2 — review and save
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
                            "id": len(data["cigars"]) + 1,
                            "brand": st.session_state.lookup_brand,
                            "name": st.session_state.lookup_name,
                            "vitola": vitola, "wrapper": wrapper,
                            "origin": origin, "strength": strength,
                            "qty": qty, "price": price, "notes": notes,
                            "purchase_date": str(purchase_date),
                            "smoked": False, "rating": 0, "smoked_date": ""
                        }
                        data["cigars"].append(new_cigar)
                        save_data(data)
                        del st.session_state.lookup_result
                        st.success(f"Added {st.session_state.lookup_brand} {st.session_state.lookup_name}!")
                        st.rerun()

    st.divider()

    # Filter + search
    filter_opt = st.radio("Show", ["All", "In Humidor", "Smoked"], horizontal=True)
    search = st.text_input("Search", placeholder="Search by brand or name…")

    cigars = data["cigars"]
    if filter_opt == "In Humidor":
        cigars = [c for c in cigars if not c["smoked"]]
    elif filter_opt == "Smoked":
        cigars = [c for c in cigars if c["smoked"]]
    if search:
        cigars = [c for c in cigars if search.lower() in f"{c['brand']} {c['name']}".lower()]

    if not cigars:
        st.info("No cigars found. Add one above!" if is_admin else "The humidor is empty.")
    else:
        for cigar in cigars:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{cigar['brand']} {cigar['name']}**")
                    st.caption(f"{cigar['vitola']} · {cigar['origin']} · {cigar['wrapper']} · {cigar['strength']}")
                    if cigar["qty"] > 0:
                        st.caption(f"🗃 {cigar['qty']} in humidor")
                    if cigar["smoked"] and cigar["rating"]:
                        st.caption("⭐" * cigar["rating"])
                    if cigar["notes"]:
                        st.caption(f"📝 {cigar['notes']}")
                with col2:
                    if is_admin:
                        if not cigar["smoked"]:
                            if st.button("Mark Smoked", key=f"smoke_{cigar['id']}"):
                                cigar["smoked"] = True
                                cigar["smoked_date"] = str(date.today())
                                save_data(data)
                                st.rerun()
                        else:
                            st.caption(f"Smoked {cigar['smoked_date']}")
                        if st.button("Delete", key=f"del_{cigar['id']}"):
                            data["cigars"] = [c for c in data["cigars"] if c["id"] != cigar["id"]]
                            save_data(data)
                            st.rerun()
                    else:
                        if cigar["smoked"]:
                            st.caption(f"Smoked {cigar['smoked_date']}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — TASTING JOURNAL
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Tasting Journal")

    smoked = [c for c in data["cigars"] if c["smoked"]]

    if not smoked:
        st.info("No smoked cigars yet.")
    else:
        rated = [c for c in smoked if c["rating"]]
        avg = sum(c["rating"] for c in rated) / len(rated) if rated else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Smoked", len(smoked))
        col2.metric("Avg Rating", f"{avg:.1f} / 5" if avg else "—")
        col3.metric("Unrated", len(smoked) - len(rated))

        st.divider()

        if is_admin:
            unrated = [c for c in smoked if not c["rating"]]
            if unrated:
                st.markdown("**Rate your smokes:**")
                for cigar in unrated:
                    with st.container(border=True):
                        st.markdown(f"**{cigar['brand']} {cigar['name']}** · {cigar['smoked_date']}")
                        rating = st.slider("Rating", 1, 5, 3, key=f"rate_{cigar['id']}")
                        tasting_notes = st.text_area("Tasting notes", key=f"notes_{cigar['id']}", placeholder="What did you taste? How was the draw, burn, finish?")
                        if st.button("Save Rating", key=f"save_{cigar['id']}"):
                            cigar["rating"] = rating
                            if tasting_notes:
                                cigar["notes"] = tasting_notes
                            save_data(data)
                            st.rerun()
                st.divider()

        st.markdown("**All entries:**")
        for cigar in sorted(smoked, key=lambda c: c["smoked_date"], reverse=True):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{cigar['brand']} {cigar['name']}**")
                    st.caption(f"{cigar['vitola']} · {cigar['origin']} · {cigar['strength']}")
                    if cigar["notes"]:
                        st.write(cigar["notes"])
                with col2:
                    st.caption(cigar["smoked_date"])
                    if cigar["rating"]:
                        st.write("⭐" * cigar["rating"])

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
