import dash
from dash import dcc, html, Input, Output, State
from dash import dash_table  # Updated import for dash_table
from flask import Flask, render_template_string
import plotly.express as px
import subprocess
import pandas as pd
import os
from datetime import datetime

# Define chart width and height as variables
chart_width = 500
chart_height = 300
update_time = 8000
refresh_interval = 2000

# Initialize Dash app
app = dash.Dash(__name__)

# Define a global variable for previous file modification timestamp
previous_modified = None

# Initialize dataframes for Value1 to Value6, with a max size of 100 rows
value_dataframes = {f"Value{i}": pd.DataFrame(columns=["timestamp"]) for i in range(1, 7)}

# Function to read the updated CSV file
def read_updated_csv(file_path):
    return pd.read_csv(file_path)

# Function to get the last modification time of the CSV file
def get_file_timestamp(file_path):
    modification_time = os.path.getmtime(file_path)
    return datetime.fromtimestamp(modification_time).strftime("%Y-%m-%d %H:%M:%S")

def append_to_dataframes(new_data, timestamp):
    symbols = new_data["Symbol"].unique()
    for col in new_data.columns[1:]:
        value_df = new_data[["Symbol", col]].copy()
        value_df["timestamp"] = timestamp
        pivot_df = value_df.pivot(index="timestamp", columns="Symbol", values=col)
        pivot_df = pivot_df.rename(columns={symbol: symbol.lower() for symbol in symbols})
        pivot_df.reset_index(inplace=True)
        
        # Remove rows with duplicate timestamps and keep the most recent one
        value_dataframes[col] = pd.concat([value_dataframes[col], pivot_df], ignore_index=True)
        value_dataframes[col] = value_dataframes[col].drop_duplicates(subset=["timestamp"], keep="last").reset_index(drop=True)
        
        if len(value_dataframes[col]) > 50:
            value_dataframes[col] = value_dataframes[col].iloc[1:].reset_index(drop=True)

# Function to prepare scenario data
def prepare_scenario_data():
    scenarios = {}
    for i in range(1, 7):
        scenario_data = value_dataframes[f"Value{i}"].tail(20)
        scenario_data["timestamp"] = pd.to_datetime(scenario_data["timestamp"])
        for col in scenario_data.columns:
            if col != "timestamp":
                scenario_data[col] = scenario_data[col].str.replace('%', '').astype(float) / 100
        scenarios[f"Scenario {i}"] = scenario_data
    return scenarios

# Define paths to your Python scripts
script_1_path = "script1.py"
script_2_path = "script2.py"
script_3_path = "script3.py"

# Layout
app.layout = html.Div([ 
    html.H1("Real-Time Scenario Dashboard", style={"text-align": "center"}),

html.Div([
    html.Button("Run Script 1", id="button-1", n_clicks=0, style={"margin": "10px"}),
    html.Button("Run Script 2", id="button-2", n_clicks=0, style={"margin": "10px"}),
    html.Button("Run Script 3", id="button-3", n_clicks=0, style={"margin": "10px"}),
    html.A("View Tables", href="/get_table", target="_blank", style={"margin": "10px", "display": "inline-block"}),
], style={"margin-top": "20px", "text-align": "center"}),


    # Hidden output div to capture button click
    html.Div(id="dummy_output", style={"display": "none"}),

    # Interval for updating charts every 5 seconds
    dcc.Interval(id="interval", interval=update_time, n_intervals=0),

    # Div to contain the charts
    html.Div(
        id="charts",
        style={
            "display": "grid",
            "grid-template-columns": f"repeat(3, {chart_width}px)",
            "grid-template-rows": f"repeat(2, {chart_height}px)",
            "gap": 5,
            "justify-items": "center",
            "padding": 5
        }
    ),

   
])

# Callback to update the charts
@app.callback(
    Output("charts", "children"),
    Input("interval", "n_intervals")
)
def update_charts(n_intervals):
    global previous_modified
    csv_file_path = "scenario2.csv"

    try:
        last_modified = os.path.getmtime(csv_file_path)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
        return html.Div("CSV file not found.")

    if n_intervals == 0 or (last_modified is not None and last_modified != previous_modified):
        try:
            new_data = read_updated_csv(csv_file_path)
            timestamp = get_file_timestamp(csv_file_path)
            append_to_dataframes(new_data, timestamp)
            scenarios = prepare_scenario_data()

            charts = []
            for i in range(0, 6, 3):
                row_charts = []
                for j in range(i, i + 3):
                    if j < 6:
                        scenario_name, data = list(scenarios.items())[j]
                        fig = px.line(data, x=data.index, y=[col for col in data.columns if col != "timestamp"], title=scenario_name)

                        fig.update_layout(
                            xaxis=dict(
                                tickmode="array",
                                tickvals=data.index,
                                ticktext=data["timestamp"].dt.strftime("%H:%M:%S"),
                                title="Time",
                                range=[data.index.min() - 1, data.index.max() + 1],
                            ),
                            yaxis=dict(tickformat=".0%", title="Percentage"),
                            height=chart_height,
                            width=chart_width,
                            margin=dict(l=10, r=10, t=30, b=10),
                            title=dict(font=dict(size=16), x=0.5)
                        )
                        row_charts.append(dcc.Graph(figure=fig))
                charts.extend(row_charts)

            previous_modified = last_modified
            return charts

        except pd.errors.EmptyDataError:
            print("Error: CSV file is empty.")
            return html.Div("CSV file is empty.")
        except Exception as e:
            print(f"An error occurred: {e}")
            return html.Div(f"An error occurred: {e}")
    else:
        return dash.no_update
# Callback for button clicks to trigger script execution or open table in a new tab
@app.callback(
    Output("dummy_output", "children"),
    [Input("button-1", "n_clicks"),
     Input("button-2", "n_clicks"),
     Input("button-3", "n_clicks")]
)
def run_scripts_or_open_table(n_clicks_1, n_clicks_2, n_clicks_3):
    ctx = dash.callback_context
    if not ctx.triggered:
        return None
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "button-1" and n_clicks_1 > 0:
        subprocess.run(["python", "script1.py"])
    elif button_id == "button-2" and n_clicks_2 > 0:
        subprocess.run(["python", "script2.py"])
    elif button_id == "button-3" and n_clicks_3 > 0:
        subprocess.run(["python", "script3.py"])




# Helper function to generate the tables in a 3x2 grid format
def generate_tables():
    scenarios = prepare_scenario_data()  # Get the processed data
    tables = []

    for i in range(1, 7):
        scenario_data = scenarios[f"Scenario {i}"]
        table = dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in scenario_data.columns],
            data=scenario_data.to_dict("records"),
            style_table={"width": "100%", "overflowX": "auto"},
            style_cell={
                "textAlign": "center",
                "padding": "10px",
                "minWidth": "150px",
                "maxWidth": "200px",
                "whiteSpace": "normal",
            },
            style_header={"backgroundColor": "lightgrey", "fontWeight": "bold"},
            page_size=10,
        )
        tables.append(html.Div([html.H3(f"Table for Scenario {i}"), table]))

    # Arrange tables into a 3x2 grid
    table_grid = html.Div(
        style={
            "display": "grid",
            "grid-template-columns": "repeat(3, 1fr)",
            "grid-gap": "20px",
            "padding": "10px",
        },
        children=tables,
    )
    return table_grid


@app.server.route("/get_table")
def serve_table():
    # Prepare table data
    scenarios = prepare_scenario_data()

    # HTML template to display the tables
    table_html = "<h1>Tables for Scenarios</h1><div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;'>"
    for i in range(1, 7):
        scenario_data = scenarios[f"Scenario {i}"]

        # Convert numerical columns to percentages
        for col in scenario_data.columns:
            if col != "timestamp":
                scenario_data[col] = (scenario_data[col] * 100).round(2).astype(str) + "%"

        # Add table for each scenario
        table_html += f"""
        <div>
            <h2>Table for Scenario {i}</h2>
            {scenario_data.to_html(index=False, escape=False)}
        </div>
        """
    table_html += "</div>"

    # Use the predefined `refresh_interval` variable
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scenario Tables</title>
        <script>
            // Auto-refresh the page every {refresh_interval / 1000} seconds
            setTimeout(function() {{
                window.location.reload();
            }}, {refresh_interval});
        </script>
    </head>
    <body>
        {table_html}
    </body>
    </html>
    """)

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)

