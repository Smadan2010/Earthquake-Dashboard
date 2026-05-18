import streamlit as st
import pandas as pd
import pydeck as pdk

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Earthquake Dashboard",
    layout="wide"
)

# ---------------- LOAD DATA ----------------
df = pd.read_csv("earthquake_data.csv")

# ---------------- TITLE ----------------
st.title("Global Seismic Trends: Data-Driven Earthquake Insights.")
st.subheader("🌍 Earthquake Data Analysis Dashboard")

# ---------------- SIDEBAR ----------------
st.sidebar.title("Navigation")

category = st.sidebar.radio(
    "Select Category",
    ["All Data", "Data Analysis"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

# ---------------- YEAR FILTER ----------------
years = sorted(df["year"].dropna().unique().tolist())

year_filter = st.sidebar.selectbox(
    "Select Year",
    ["All"] + years
)

# ---------------- MAGNITUDE FILTER ----------------
min_mag = float(df["mag"].min())
max_mag = float(df["mag"].max())

mag_range = st.sidebar.slider(
    "Magnitude Range",
    min_mag,
    max_mag,
    (min_mag, max_mag)
)

# ---------------- APPLY FILTERS ----------------
filtered_df = df.copy()

if year_filter != "All":
    filtered_df = filtered_df[
        filtered_df["year"] == year_filter
    ]

filtered_df = filtered_df[
    filtered_df["mag"].between(mag_range[0], mag_range[1])
]

# ---------------- KPI CARDS ----------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Earthquakes", len(filtered_df))

c2.metric(
    "Avg Magnitude",
    round(filtered_df["mag"].mean(), 2)
)

c3.metric(
    "Max Magnitude",
    round(filtered_df["mag"].max(), 2)
)

c4.metric(
    "Tsunami Events",
    int(filtered_df["tsunami"].sum())
)

st.markdown("---")

# ---------------- QUERIES ----------------
queries = {
    "1. Top 10 strongest earthquakes (mag)":
        filtered_df.sort_values(
            by="mag",
            ascending=False
        ).head(10),

    "2. Top 10 deepest earthquakes (depth)":
        filtered_df.sort_values(
            by="depth",
            ascending=False
        ).head(10),

    "3. Shallow earthquakes < 50 km and mag > 7.5":
        filtered_df[
            (filtered_df["depth"] < 50)
            & (filtered_df["mag"] > 7.5)
        ],

    "4. Average magnitude per magnitude type (magType)":
        filtered_df.groupby("magType", as_index=False)["mag"].mean(),

    "5. Year with most earthquakes":
        filtered_df.groupby("year", as_index=False).size()
        .sort_values(by="size", ascending=False)
        .head(1),

    "6. Month with highest number of earthquakes":
        filtered_df.groupby("month", as_index=False).size()
        .sort_values(by="size", ascending=False)
        .head(1),

    "7. Day of week with most earthquakes":
        filtered_df.groupby("day_of_week", as_index=False).size()
        .sort_values(by="size", ascending=False)
        .head(1),

    "8. Count of earthquakes per hour of day":
        filtered_df.assign(
            hour_of_day=pd.to_datetime(filtered_df["time"]).dt.hour
        )
        .groupby("hour_of_day", as_index=False)
        .size()
        .sort_values(by="hour_of_day"),

    "9. Most active reporting network (net)":
        filtered_df.groupby("net", as_index=False).size()
        .sort_values(by="size", ascending=False)
        .head(1),

    "10. Reviewed vs automatic earthquakes":
        filtered_df[
            filtered_df["status"].isin(
                ["reviewed", "automatic"]
            )
        ].groupby("status", as_index=False).size(),

    "11. Count by earthquake type":
        filtered_df.groupby("type", as_index=False).size(),

    "12. Number of earthquakes by datatype (types)":
        filtered_df.groupby("types", as_index=False).size(),

    "13. Events with high station coverage (nst > avg)":
        filtered_df[
            filtered_df["nst"]
            > filtered_df["nst"].mean()
        ],

    "14. Tsunami triggered earthquakes per year":
        filtered_df[
            filtered_df["tsunami"] == 1
        ].groupby("year", as_index=False).size(),

    "15. Count earthquakes by alert levels":
        filtered_df.groupby("alert", as_index=False).size(),

    "16. Top 5 countries with highest average magnitude":
        filtered_df.groupby("country", as_index=False)["mag"]
        .mean()
        .sort_values(by="mag", ascending=False)
        .head(5),

    "17. Countries with both shallow and deep earthquakes":
        filtered_df[
            filtered_df["depth"] > 70
        ],

    "18. Top 3 most seismically active regions":
        filtered_df.groupby("country", as_index=False)
        .agg(
            No_of_count=("country", "count"),
            avg_magnitude=("mag", "mean")
        )
        .sort_values(
            by="No_of_count",
            ascending=False
        )
        .head(3),

    "19. Avg depth near equator (+-5 latitude)":
        filtered_df[
            filtered_df["latitude"].abs() <= 5
        ].groupby("country", as_index=False)["depth"]
        .mean(),

    "20. Avg magnitude difference (tsunami vs non-tsunami)":
        pd.DataFrame({
            "Category": [
                "With Tsunami",
                "Without Tsunami"
            ],
            "Average Magnitude": [
                filtered_df[
                    filtered_df["tsunami"] == 1
                ]["mag"].mean(),

                filtered_df[
                    filtered_df["tsunami"] == 0
                ]["mag"].mean()
            ]
        }),

    "21. Lowest data reliability":
        filtered_df[
            (filtered_df["gap"] > 120)
            & (filtered_df["rms"] > 0.6)
        ],

    "22. Regions with highest deep focus earthquakes (>300km)":
        filtered_df[
            filtered_df["depth"] > 300
        ][
            ["latitude", "longitude", "place", "depth", "mag"]
        ]
}

# ---------------- ALL DATA ----------------
if category == "All Data":

    st.subheader("📊 All Earthquake Data")

    st.dataframe(
        filtered_df.head(1000),
        use_container_width=True
    )

# ---------------- DATA ANALYSIS ----------------
else:

    st.subheader("📈 Data Analysis")

    task = st.selectbox(
        "Choose Question",
        list(queries.keys())
    )

    result_df = queries[task]

    # ---------------- TABLE ----------------
    st.subheader("📋 Result Table")

    st.dataframe(
        result_df,
        use_container_width=True
    )

    st.markdown("---")

    # ---------------- CHART + MAP ----------------
    left_col, right_col = st.columns(2)

    # ---------------- CHART ----------------
    with left_col:

        st.subheader("📊 Chart")

        num_cols = result_df.select_dtypes(
            include="number"
        ).columns

        if len(num_cols) > 0:

            st.bar_chart(result_df[num_cols[0]])

        else:

            st.info("No numeric data available.")

    # ---------------- MAP ----------------
    with right_col:

        st.subheader("🗺️ Map")

        if {
            "latitude",
            "longitude"
        }.issubset(result_df.columns):

            st.pydeck_chart(
                pdk.Deck(
                    initial_view_state=pdk.ViewState(
                        latitude=result_df["latitude"].mean(),
                        longitude=result_df["longitude"].mean(),
                        zoom=2,
                    ),

                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=result_df,
                            get_position="[longitude, latitude]",
                            get_radius=20000,
                            get_fill_color=[255, 80, 80],
                            pickable=True,
                        )
                    ],

                    tooltip={
                        "text":
                        "Place: {place}\n"
                        "Magnitude: {mag}\n"
                        "Depth: {depth}"
                    }
                )
            )

        else:

            st.info("Map not applicable for this query.")