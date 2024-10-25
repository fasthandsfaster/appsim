import json
from IPython.display import display
import pandas as pd
import plotly.graph_objects as go

# Sample JSON data with multiple time series
with open('exer_result.json', 'r') as file:
    json_data = json.load(file)

# Convert JSON data to DataFrame
df = pd.json_normalize(json_data['result']['taskResultList'])

# Ensure the 'date' column is in datetime format
df['setTime'] = pd.to_datetime(df['setTime'])
df['replyTime'] = pd.to_datetime(df['replyTime'])

# Create a plotly figure
fig = go.Figure()

display(df)

def get_marker_symbol(category):
    symbol_map = {
        'Rebounder': 'circle',
        'Port': 'square',
        'Triangle': 'diamond',
        'LongPort': 'cross'
    }
    return symbol_map.get(category, 'circle')  # De


# Add each time series to the figure
# Hypothetical correction
#for index, row in df.iterrows():
#    elemType = row['task']['type']  # Assuming 'type' is a direct column in df
#    fig.add_trace(go.Scatter(x=[row['setTime']], y=[row['replyTime'] - row['setTime']], mode='lines+markers', name=elemType, marker=dict(symbol=get_marker_symbol(elemType),size=10)))

#for column in df.columns[1:]:
#elemType = df['type'].first  # Assuming 'type' is a direct column in df
fig.add_trace(go.Scatter(x=df['setTime'], y=df['replyTime'] - df['setTime'],name='gygag',mode='lines+markers'))

# Update layout for a better look
fig.update_layout(
    title='Results of the exercise',
    xaxis_title='Time',
    yaxis_title='Reaction Time',
    legend_title='Time Series'
)

# Show the interactive plot
fig.show()