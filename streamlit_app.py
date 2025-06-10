import streamlit as st
from datetime import date
from sqlalchemy.orm import Session
from collections import Counter

import pandas as pd
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

# --- UI setup ---
st.set_page_config(
    page_title="Measure Filter App",
    page_icon="src/utils/logo.png",
    layout="wide"
)
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

countries = selected_countries if selected_countries else None
policy_types = selected_policy_types if selected_policy_types else None
target_groups = selected_target_groups if selected_target_groups else None
levels = selected_levels if selected_levels else None

# --- Apply filters ---
if st.sidebar.button("Apply Filters"):
    with st.spinner("Loading results..."):
        measures = get_filtered_measures(
            session,
            country=countries,
            date_from=date_from,
            date_to=date_to,
            policy_type=policy_types,
            target_group=target_groups,
            level=levels
        )

        results = []
        for m in measures:
            results.append({
                "id": m.id,
                "country": m.country.name if m.country else None,
                "date": m.date_ref.date if getattr(m, "date_ref", None) else None,
                "policy_type": [pl.policy.name for pl in getattr(m, "policy_links", [])],
                "authority": m.detail_ref.authority if getattr(m, "detail_ref", None) else None,
                "level": [pl.policy.level_type for pl in getattr(m, "policy_links", [])],
            })

        st.session_state["results"] = results
        st.session_state["measures"] = measures

results = st.session_state.get("results", [])
measures = st.session_state.get("measures", [])

if results:
    st.write(f"Total measures found: {len(results)}")
    st.dataframe(results)

    df = pd.DataFrame(results)
    df["date"] = pd.to_datetime(df["date"])

    if not df.empty:
        with st.expander("Measures Over Time"):
            aggregation_option = st.selectbox("Select aggregation interval:", ["Weekly", "Monthly", "Daily"], index=0)
            if aggregation_option == "Daily":
                df["interval"] = df["date"]
            elif aggregation_option == "Monthly":
                df["interval"] = df["date"].dt.to_period("M").apply(lambda r: r.start_time)
            else:
                df["interval"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

            counts = df.groupby("interval").size().reset_index(name="measure_count")
            fig1 = px.line(
                counts,
                x="interval",
                y="measure_count",
                markers=True,
                labels={"interval": aggregation_option, "measure_count": "Number of Measures"},
                title=f"Number of Measures Introduced ({aggregation_option})"
            )
            fig1.update_layout(margin=dict(l=40, r=40, t=40, b=40))
            st.plotly_chart(fig1, use_container_width=True)

        with st.expander("Measures by Country"):
            country_counts = df["country"].value_counts().reset_index()
            country_counts.columns = ["country", "measure_count"]

            top_n_countries = st.slider("Number of top countries to display", 1, len(country_counts), min(10, len(country_counts)))
            country_counts = country_counts.head(top_n_countries)

            fig2 = px.bar(
                country_counts,
                x="measure_count",
                y="country",
                orientation="h",
                labels={"measure_count": "Number of Measures", "country": "Country"},
                title="Top Countries by Number of Measures",
                height=400 + 20 * len(country_counts),
            )
            fig2.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=100, r=40, t=40, b=40))
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("Distribution of Policy Measures by Level"):
            level_data = []
            for m in measures:
                for pl in getattr(m, "policy_links", []):
                    name = pl.policy.name
                    level_type = pl.policy.level_type
                    if name and level_type:
                        level_data.append((name, level_type))

            if level_data:
                df_levels = pd.DataFrame(level_data, columns=["policy", "level_type"])

                top_n_policies = st.slider("Number of top policy measures to display", 1, len(df_levels["policy"].unique()), min(10, len(df_levels["policy"].unique())))
                top_policies = df_levels["policy"].value_counts().head(top_n_policies).index.tolist()
                df_levels = df_levels[df_levels["policy"].isin(top_policies)]

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

        with st.expander("Authority Breakdown and Map"):
            authority_counts = df["authority"].value_counts().reset_index()
            authority_counts.columns = ["authority", "count"]
            authority_counts = authority_counts[authority_counts["authority"].notnull() & (authority_counts["authority"] != "")]

            country_authority = {}
            for m in measures:
                country = m.country
                authority = m.detail_ref.authority if getattr(m, "detail_ref", None) else None
                if country and authority:
                    key = country.iso3.upper()
                    country_authority.setdefault(key, []).append(authority)

            rows = []
            for iso3, authorities in country_authority.items():
                if authorities:
                    dominant = Counter(authorities).most_common(1)[0][0]
                    rows.append({"iso3": iso3, "authority": dominant})
            df_map = pd.DataFrame(rows)

            if not authority_counts.empty and not df_map.empty:
                authority_types = sorted(authority_counts["authority"].unique())
                color_map = px.colors.qualitative.Plotly
                color_scale = {auth: color_map[i % len(color_map)] for i, auth in enumerate(authority_types)}

                col1, col2 = st.columns([1.6, 1.4])

                with col1:
                    fig_map = px.choropleth(
                    df_map,
                    locations="iso3",
                    color="authority",
                    hover_name="iso3",
                    title="Dominant Authority Type by Country",
                    color_discrete_map=color_scale,
                    category_orders={"authority": authority_types}
                    )

                    # Ustawienie właściwego tekstu w hoverze
                    fig_map.update_traces(
                        hovertemplate="<b>%{hovertext}</b><br>Authority Type: %{customdata[0]}<extra></extra>",
                        customdata=df_map[["authority"]]
                    )

                    fig_map.update_layout(
                        geo=dict(showframe=False, showcoastlines=False, projection_type="natural earth"),
                        showlegend=False,
                        margin=dict(l=0, r=0, t=50, b=0),
                        font=dict(size=13)
                    )
                    st.plotly_chart(fig_map, use_container_width=True)

                with col2:
                    fig_pie = px.pie(
                        authority_counts,
                        names="authority",
                        values="count",
                        title="Authority Type Distribution",
                        color="authority",
                        color_discrete_map=color_scale,
                        hole=0.4
                    )
                    fig_pie.update_traces(textinfo="label+percent")
                    fig_pie.update_layout(margin=dict(t=50, b=20))
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No authority data available to display.")
else:
    st.info("Set your filters and click 'Apply Filters' to see results.")
