import streamlit as st
import json
import os
from datetime import date

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Humidor", page_icon="🚬", layout="centered")

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

# ── Constants ─────────────────────────────────────────────────────────────────
VITOLAS   = ["Robusto","Toro","Churchill","Corona","Lonsdale","Belicoso","Torpedo","Lancero","Petite Corona","Gordo"]
WRAPPERS  = ["Colorado Claro","Colorado","Colorado Maduro","Maduro","Natural","Claro","Oscuro","Candela"]
ORIGINS   = ["Nicaragua","Cuba","Dominican Republic","Honduras","Ecuador","Mexico","Cameroon","USA","Panama","Brazil"]
STRENGTHS = ["Mild","Mild-Medium","Medium","Medium-Full","Full"]

# ── Load data into session ────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🚬 Humidor")
st.caption("Your personal cigar journal")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Humidor", "Tasting Journal", "Pairings"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — HUMIDOR
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("My Humidor")

    # Add cigar form
    with st.expander("➕ Add a new cigar"):
        with st.form("add_cigar"):
            col1, col2 = st.columns(2)
            with col1:
                brand   = st.text_input("Brand *", placeholder="e.g. Padron")
                vitola  = st.selectbox("Vitola", VITOLAS)
                origin  = st.selectbox("Origin", ORIGINS)
                qty     = st.number_input("Qty in humidor", min_value=0, value=1)
            with col2:
                name     = st.text_input("Name / Line *", placeholder="e.g. 1964 Anniversary")
                wrapper  = st.selectbox("Wrapper", WRAPPERS)
                strength = st.selectbox("Strength", STRENGTHS)
                price    = st.number_input("Price per stick ($)", min_value=0.0, step=0.50)

            purchase_date = st.date_input("Purchase date", value=date.today())
            notes = st.text_area("Notes", placeholder="Flavors, aroma, construction…")

            submitted = st.form_submit_button("Save Cigar", type="primary")
            if submitted:
                if not brand or not name:
                    st.error("Brand and Name are required.")
                else:
                    new_cigar = {
                        "id": len(data["cigars"]) + 1,
                        "brand": brand, "name": name, "vitola": vitola,
                        "wrapper": wrapper, "origin": origin, "strength": strength,
                        "qty": qty, "price": price, "notes": notes,
                        "purchase_date": str(purchase_date),
                        "smoked": False, "rating": 0, "smoked_date": ""
                    }
                    data["cigars"].append(new_cigar)
                    save_data(data)
                    st.success(f"Added {brand} {name} to your humidor!")
                    st.rerun()

    st.divider()

    # Filter
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
        st.info("No cigars found. Add one above!")
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

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — TASTING JOURNAL
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Tasting Journal")

    smoked = [c for c in data["cigars"] if c["smoked"]]

    if not smoked:
        st.info("No smoked cigars yet. Mark a cigar as smoked from the Humidor tab.")
    else:
        # Stats
        rated = [c for c in smoked if c["rating"]]
        avg = sum(c["rating"] for c in rated) / len(rated) if rated else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Smoked", len(smoked))
        col2.metric("Avg Rating", f"{avg:.1f} / 5" if avg else "—")
        col3.metric("Unrated", len(smoked) - len(rated))

        st.divider()

        # Rate unrated cigars
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

        # Full journal
        st.markdown("**All entries:**")
        for cigar in sorted(smoked, key=lambda c: c["smoked_date"], reverse=True):
            with st.container(border=True):
                col1, col2 = st.columns([3,1])
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
            col1, col2 = st.columns([1,1])
            with col1:
                st.markdown(f"🚬 **{cigar_type}**")
            with col2:
                st.markdown(f"🥃 **{spirit}**")
            st.write(description)

    st.divider()
    st.caption("AI-powered personalized pairing recommendations coming soon.")

