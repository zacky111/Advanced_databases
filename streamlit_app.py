import streamlit as st
from datetime import date
from src.database.filter import get_filtered_measures
from sqlalchemy.orm import Session
from src.database.connection import engine
from src.database.model import Country, PolicyMeasureLevel

# Store the session in Streamlit's session state
if "db_session" not in st.session_state:
    st.session_state["db_session"] = Session(engine)
session = st.session_state["db_session"]

def cleanup_session():
    db_session = st.session_state.get("db_session", None)
    if db_session:
        db_session.close()

# Helper functions to get filter options from the database
def get_country_options(session):
    return [c.name for c in session.query(Country).order_by(Country.name).all()]

def get_policy_type_options(session):
    return sorted(set([p.name for p in session.query(PolicyMeasureLevel).all()]))

def get_level_options(session):
    return sorted(set([p.level_type for p in session.query(PolicyMeasureLevel).all() if p.level_type]))

st.title("Measure Filter App")

# --- Sidebar filters ---
st.sidebar.header("Filter Options")

country_options = get_country_options(session)
policy_type_options = get_policy_type_options(session)
level_options = get_level_options(session)

selected_countries = st.sidebar.multiselect("Countries", country_options)
selected_policy_types = st.sidebar.multiselect("Policy Type", policy_type_options)
selected_target_groups = st.sidebar.multiselect("Target Group", policy_type_options)
selected_levels = st.sidebar.multiselect("Level", level_options)
date_from = st.sidebar.date_input("Start Date", value=date(2020, 1, 1))
date_to = st.sidebar.date_input("End Date", value=date(2020, 2, 29))

# Convert selections
countries = selected_countries if selected_countries else None
policy_types = selected_policy_types if selected_policy_types else None
target_groups = selected_target_groups if selected_target_groups else None
levels = selected_levels if selected_levels else None

if st.sidebar.button("Apply Filters"):
    with st.spinner("Loading results..."):
        results = []
        measures = get_filtered_measures(
            session,
            country=countries,
            date_from=date_from,
            date_to=date_to,
            policy_type=policy_types,
            target_group=target_groups,
            level=levels
        )
        for m in measures:
            results.append({
                "id": m.id,
                "country": m.country.name if m.country else None,
                "date": m.date_ref.date if getattr(m, "date_ref", None) else None,
                "policy_type": [pl.policy.name for pl in getattr(m, "policy_links", [])],
                "details": m.detail_ref.details if getattr(m, "detail_ref", None) else None,
                "level": [pl.policy.level_type for pl in getattr(m, "policy_links", [])],
            })

    st.write(f"Total measures found: {len(results)}")
    if results:
        st.dataframe(results)
    else:
        st.info("No results found. Adjust your filters and try again.")
else:
    st.info("Set your filters and click 'Apply Filters' to see results.")

# Close the session at the end (optional, but only if you know the app is shutting down)
# session.close()