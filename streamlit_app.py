import streamlit as st
from datetime import date
from sqlalchemy.orm import Session
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from src.database.connection import engine
from src.database.model import Country, PolicyMeasureLevel
from src.database.filter import get_filtered_measures

# --- Session setup ---
if "db_session" not in st.session_state:
    st.session_state["db_session"] = Session(engine)
session = st.session_state["db_session"]

def cleanup_session():
    db_session = st.session_state.get("db_session", None)
    if db_session:
        db_session.close()

# --- Helper options from DB ---
def get_country_options(session):
    return [c.name for c in session.query(Country).order_by(Country.name).all()]

def get_policy_type_options(session):
    return sorted(set([p.name for p in session.query(PolicyMeasureLevel).all()]))

def get_level_options(session):
    return sorted(set([p.level_type for p in session.query(PolicyMeasureLevel).all() if p.level_type]))

# --- UI ---
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

# --- Apply filters and show results ---
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
                "authority": m.detail_ref.authority if getattr(m, "detail_ref", None) else None,
                "level": [pl.policy.level_type for pl in getattr(m, "policy_links", [])],
            })

    st.write(f"Total measures found: {len(results)}")
    if results:
        st.dataframe(results)

        df = pd.DataFrame(results)
        df["date"] = pd.to_datetime(df["date"])

        if not df.empty:
            # --- CHART 1: Measures over time ---
            with st.expander("📈 Measures Over Time"):
                df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)
                counts = df.groupby("week").size().reset_index(name="measure_count")

                fig1 = px.line(
                    counts,
                    x="week",
                    y="measure_count",
                    markers=True,
                    labels={"week": "Week", "measure_count": "Number of Measures"},
                    title="Number of Measures Introduced Per Week"
                )
                fig1.update_layout(margin=dict(l=40, r=40, t=40, b=40))
                st.plotly_chart(fig1, use_container_width=True)

            # --- CHART 2: Measures by country ---
            with st.expander("🌍 Measures by Country"):
                country_counts = df["country"].value_counts().reset_index()
                country_counts.columns = ["country", "measure_count"]

                fig2 = px.bar(
                    country_counts,
                    x="measure_count",
                    y="country",
                    orientation="h",
                    labels={"measure_count": "Number of Measures", "country": "Country"},
                    title="Number of Measures Introduced by Country",
                    height=400 + 20 * len(country_counts),
                )
                fig2.update_layout(
                    yaxis=dict(autorange="reversed"),
                    margin=dict(l=100, r=40, t=40, b=40),
                )
                st.plotly_chart(fig2, use_container_width=True)

            # --- CHART 3: Authority distribution (pie) ---
            with st.expander("🏛️ Authority Breakdown"):
                authority_counts = df["authority"].value_counts().reset_index()
                authority_counts.columns = ["authority", "count"]
                authority_counts = authority_counts[authority_counts["authority"].notnull() & (authority_counts["authority"] != "")]

                if not authority_counts.empty:
                    fig3 = px.pie(
                        authority_counts,
                        names="authority",
                        values="count",
                        title="Distribution of Authority Types",
                        hole=0.4
                    )
                    fig3.update_traces(textinfo="label+percent")
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("No authority data available to show.")

            # --- CHART 4: Policy Measures by Level ---
            with st.expander("📊 Distribution of Policy Measures by Level"):
                level_data = []
                for m in measures:
                    for pl in getattr(m, "policy_links", []):
                        name = pl.policy.name
                        level_type = pl.policy.level_type
                        if name and level_type:
                            level_data.append((name, level_type))

                if level_data:
                    df_levels = pd.DataFrame(level_data, columns=["policy", "level_type"])

                    fig4 = px.histogram(
                        df_levels,
                        y="policy",
                        color="level_type",
                        barmode="stack",
                        labels={"policy": "Policy Name", "level_type": "Policy Level"},
                        title="Policy Measure Distribution by Level",
                        orientation="h",
                        height=30 + 20 * len(df_levels["policy"].unique())
                    )
                    fig4.update_layout(
                        yaxis=dict(categoryorder="total ascending"),
                        margin=dict(l=200, r=40, t=50, b=40)
                    )
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("No policy level data available to display.")

            # --- CHART 5: Map - Dominant authority by country ---
            with st.expander("🗺️ Dominant Authority Type by Country"):
                country_authority = {}
                for m in measures:
                    country = m.country
                    authority = m.detail_ref.authority if getattr(m, "detail_ref", None) else None
                    if country and authority:
                        key = country.iso3.upper()
                        if key not in country_authority:
                            country_authority[key] = []
                        country_authority[key].append(authority)

                rows = []
                for iso3, authorities in country_authority.items():
                    if authorities:
                        dominant = Counter(authorities).most_common(1)[0][0]
                        rows.append({"iso3": iso3, "authority": dominant})

                if rows:
                    df_map = pd.DataFrame(rows)

                    fig5 = px.choropleth(
                        df_map,
                        locations="iso3",
                        color="authority",
                        hover_name="iso3",
                        title="Dominant Authority Type per Country",
                        color_discrete_sequence=px.colors.qualitative.Plotly,
                        category_orders={"authority": sorted(df_map["authority"].unique())}
                    )

                    fig5.update_traces(
                        hovertemplate="<b>%{hovertext}</b><br>Authority Type: %{z}<extra></extra>"
                    )

                    fig5.update_layout(
                        geo=dict(showframe=False, showcoastlines=False, projection_type="natural earth"),
                        legend_title_text="Authority Type",
                        margin=dict(l=0, r=0, t=50, b=0),
                        font=dict(size=13)
                    )

                    st.plotly_chart(fig5, use_container_width=True)
                else:
                    st.info("No authority data available to display on map.")
        else:
            st.warning("No data available to generate charts.")
    else:
        st.info("No results found. Adjust your filters and try again.")
else:
    st.info("Set your filters and click 'Apply Filters' to see results.")
