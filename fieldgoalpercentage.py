from dash import Dash, dash_table, dcc, html, Input, Output
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Function to scrape NCAA team stats
def fetch_ncaa_team_stats():
    url = "https://www.ncaa.com/stats/basketball-men/d1/current/team/148"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        if not table:
            raise ValueError("No stats table found on the page.")

        headers = [header.text.strip() for header in table.find_all("th")]
        rows = table.find_all("tr")[1:]

        data = []
        for row in rows:
            cells = row.find_all("td")
            if cells:
                # Extract team name from <a> with class="school"
                team_cell = cells[1].find("a", class_="school")
                team_name = team_cell.text.strip() if team_cell else "Unknown Team"

                # Extract the remaining columns
                columns = [cell.text.strip() for cell in cells]
                columns[1] = team_name  # Replace the second column with the team name
                data.append(columns)

        df = pd.DataFrame(data, columns=headers)

        # Ensure numeric columns are properly converted
        numeric_cols = headers[2:]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Add placeholder for Conference column if missing
        if "Conference" not in df.columns:
            df["Conference"] = ["Unknown Conference"] * len(df)

        return df
    except Exception as e:
        print(f"Error while fetching data: {e}")
        return pd.DataFrame()


# Function to fetch NCAA NET rankings
def fetch_ncaa_net_rankings():
    url = "https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        if not table:
            raise ValueError("No rankings table found on the page.")

        headers = [header.text.strip() for header in table.find_all("th")]
        rows = table.find_all("tr")[1:]

        data = []
        for row in rows:
            cells = row.find_all("td")
            if cells:
                columns = [cell.text.strip() for cell in cells]
                data.append(columns)

        df = pd.DataFrame(data, columns=headers)

        # Ensure column names match for merging
        df.rename(columns={"Team": "Team", "RANK": "Rank"}, inplace=True)
        df["Team"] = df["Team"].str.strip()
        df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
        return df
    except Exception as e:
        print(f"Error while fetching NET rankings: {e}")
        return pd.DataFrame()


# Merge stats and rankings
def merge_stats_and_rankings(stats_df, rankings_df):
    if not stats_df.empty and not rankings_df.empty:
        merged_df = pd.merge(
            stats_df,
            rankings_df[["Team", "Rank"]],
            on="Team",
            how="left"
        )
        # Ensure Conference column exists in merged data
        if "Conference" not in merged_df.columns:
            merged_df["Conference"] = ["Unknown Conference"] * len(merged_df)
        return merged_df
    return stats_df


# Initialize the Dash app
app = Dash(__name__)

# Fetch the data
team_stats_df = fetch_ncaa_team_stats()
net_rankings_df = fetch_ncaa_net_rankings()

# Merge data
team_stats_df = merge_stats_and_rankings(team_stats_df, net_rankings_df)

# If data is empty, create a placeholder DataFrame
if team_stats_df.empty:
    print("No data was retrieved. Please check the NCAA stats page.")
    team_stats_df = pd.DataFrame({"Team": [], "Conference": [], "Rank": []})  # Adjusted placeholder

# Layout for the Dash app
app.layout = html.Div(
    children=[
        html.H1("NCAA Division I Basketball Team Stats", style={"textAlign": "center"}),

        # Filters
        html.Div(
            [
                dcc.Dropdown(
                    id="conference-filter",
                    options=[
                        {"label": conf, "value": conf} for conf in sorted(team_stats_df["Conference"].unique())
                    ] + [{"label": "All Conferences", "value": "All"}],
                    placeholder="Select a Conference",
                    value="All",
                    style={"width": "45%", "display": "inline-block", "margin-right": "10px"},
                ),
                dcc.Dropdown(
                    id="stat-filter",
                    options=[
                        {"label": col, "value": col} for col in team_stats_df.columns if col not in ["Team", "Conference"]
                    ],
                    multi=True,
                    placeholder="Select Stats to Compare",
                    style={"width": "45%", "display": "inline-block"},
                )
            ],
            style={"padding": "10px"},
        ),

        # Graph
        dcc.Graph(id="team-stats-graph"),

        # Table
        dash_table.DataTable(
            id="stats-table",
            columns=[{"name": col, "id": col} for col in team_stats_df.columns],
            data=team_stats_df.to_dict("records"),
            page_size=50,
            sort_action="native",
            filter_action="native",
            style_table={"margin": "20px auto", "width": "90%"},
            style_header={"backgroundColor": "#333", "color": "white", "fontWeight": "bold"},
            style_cell={"textAlign": "center", "padding": "10px"},
        ),
    ],
    style={"fontFamily": "Arial, sans-serif", "backgroundColor": "#f9f9f9", "padding": "20px"},
)


# Callbacks for updating the graph and table
@app.callback(
    [Output("team-stats-graph", "figure"), Output("stats-table", "data")],
    [Input("conference-filter", "value"), Input("stat-filter", "value")]
)
def update_dashboard(selected_conference, selected_stats):
    filtered_df = team_stats_df

    # Filter by conference
    if selected_conference and selected_conference != "All":
        filtered_df = filtered_df[filtered_df["Conference"] == selected_conference]

    # Update the graph
    if selected_stats:
        figure = {
            "data": [
                {
                    "x": filtered_df["Team"],
                    "y": filtered_df[stat],
                    "type": "bar",
                    "name": stat,
                }
                for stat in selected_stats
            ],
            "layout": {
                "title": f"Comparison of Selected Stats in {selected_conference or 'All Conferences'}",
                "xaxis": {"title": "Team"},
                "yaxis": {"title": "Value"},
                "barmode": "group",
            },
        }
    else:
        figure = {
            "data": [],
            "layout": {
                "title": "Select Stats to Display",
                "xaxis": {"title": "Team"},
                "yaxis": {"title": "Value"},
            },
        }

    return figure, filtered_df.to_dict("records")


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
