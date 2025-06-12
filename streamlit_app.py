import streamlit as st
from datetime import date
from sqlalchemy.orm import Session
from collections import Counter

import pandas as pd
import plotly.express as px
from plotly import graph_objects as go

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

        ### ---------------- FOLD 1 ----------------------------------------
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

        ### ---------------- FOLD 2 ----------------------------------------
        with st.expander("Measures by Country"):
            country_counts = df["country"].value_counts().reset_index()
            country_counts.columns = ["country", "measure_count"]

            top_n_countries = st.slider("Number of top countries to display", 0, len(country_counts), min(10, len(country_counts)))
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

        ### ---------------- FOLD 3 ----------------------------------------
        with st.expander("Distribution of Policy Measures by Level"):
            hierarchy_data = []

            for m in measures:
                level_1_names = []
                level_2_names = []
                for pl in getattr(m, "policy_links", []):
                    if pl.policy.level_type.strip() == "Level 1":
                        level_1_names.append(pl.policy.name.strip())
                    elif pl.policy.level_type.strip() == "Level 2":
                        level_2_names.append(pl.policy.name.strip())

                for l1 in level_1_names:
                    for l2 in level_2_names:
                        hierarchy_data.append((l1, l2))

            if hierarchy_data:
                df_hier = pd.DataFrame(hierarchy_data, columns=["level_1", "level_2"])

                level1_counts = df_hier["level_1"].value_counts().reset_index()
                level1_counts.columns = ["level_1", "count"]

                st.markdown("<h4 style='text-align:left; margin-top:0'>Distribution of Policy Measures by Level 1</h4>", unsafe_allow_html=True)

                fig_main = px.pie(
                    level1_counts,
                    names="level_1",
                    values="count",
                    hole=0.4
                )
                fig_main.update_traces(textinfo="label+percent")
                fig_main.update_layout(margin=dict(t=50, b=30))
                st.plotly_chart(fig_main, use_container_width=True)

                st.markdown("<h4 style='text-align:left; margin-top:2em'>Level 2 Breakdown by Level 1 Category</h4>", unsafe_allow_html=True)
                cols = st.columns(len(level1_counts))

                for i, l1_value in enumerate(level1_counts["level_1"]):
                    with cols[i]:
                        subset = df_hier[df_hier["level_1"] == l1_value]
                        level2_counts = subset["level_2"].value_counts().reset_index()
                        level2_counts.columns = ["level_2", "count"]

                        st.markdown(f"<h5 style='text-align:center; margin-bottom:0.5em'>{l1_value}</h5>", unsafe_allow_html=True)

                        fig_sub = px.pie(
                            level2_counts,
                            names="level_2",
                            values="count",
                            hole=0.3
                        )
                        fig_sub.update_traces(textinfo="percent")
                        fig_sub.update_layout(
                            height=300,
                            showlegend=True,
                            legend=dict(orientation="h", y=-0.25, x=0, font=dict(size=9)),
                            margin=dict(t=0, b=60)
                        )
                        st.plotly_chart(fig_sub, use_container_width=True)
            else:
                st.info("No hierarchical Level 1 → Level 2 data available.")

        ### ---------------- FOLD 4 ----------------------------------------
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
                authority_labels = {
                    "Cb": "Central Bank",
                    "Sup": "Supervisor",
                    "Gov": "Government",
                    "Mof": "Ministry of Finance",
                    "Res": "Resolution Authority",
                    "Other": "Other"
                }

                authority_counts["label"] = authority_counts["authority"]
                authority_counts["legend_name"] = authority_counts["authority"].map(lambda x: f"{x} – {authority_labels.get(x, 'Unknown')}")

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
                    labels = authority_counts["label"]
                    values = authority_counts["count"]
                    authorities = authority_counts["authority"]
                    legend_names = authority_counts["legend_name"]

                    fig_pie = go.Figure(
                        data=[
                            go.Pie(
                                labels=labels,
                                values=values,
                                hole=0.4,
                                marker=dict(colors=[color_scale[a] for a in authorities]),
                                hovertext=legend_names,
                                hoverinfo="label+percent+text",
                                textinfo="label+percent",
                                textfont_size=12,
                                pull=[0.03] * len(labels),
                                showlegend=True
                            )
                        ]
                    )

                    fig_pie.update_layout(
                        margin=dict(t=50, b=100),
                        legend_title_text="Authority Type",
                        legend_traceorder="normal",
                        legend=dict(
                            y=0.5,
                            font=dict(size=10),
                            itemsizing="constant"
                        ),
                        title="Authority Type Distribution"
                    )

                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No authority data available to display.")
else:
    st.info("Set your filters and click 'Apply Filters' to see results.")
    