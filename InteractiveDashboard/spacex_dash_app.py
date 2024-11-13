
# Previously tested in local notebook
# Import required libraries
import pandas as pd
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Read the airline data into pandas dataframe
spacex_df = pd.read_csv("spacex_launch_dash.csv")
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# Previously tested on local, so got some data will need later, could also do with the Payload Mass
unique_launch_sites = spacex_df['Launch Site'].unique()
site_labels = [f"Site{i+1}" for i in range(len(unique_launch_sites))]
launch_sites_df = pd.DataFrame({
    'Launch Site': unique_launch_sites,
    'Site Label': site_labels
})
# Agrega la opción 'All Sites' como la primera opción
site_options = [{'label': 'All Sites', 'value': 'ALL'}]
# Completa con valores únicos de 'Launch Site' en launch_sites_df
site_options.extend([{'label': site, 'value': site} for site in launch_sites_df['Launch Site'].unique()])

# Añadimos la cuenta de Success y Fail para el pie chart
success_fail_counts = spacex_df.groupby('Launch Site')['class'].value_counts().unstack(fill_value=0)
# Renombrar las columnas para reflejar 'Success' y 'Fail'
success_fail_counts.columns = ['Fail', 'Success']
# Asegurarse de que las columnas estén en el orden correcto
success_fail_counts = success_fail_counts[['Success', 'Fail']]
# Unir el resultado a launch_sites_df
launch_sites_df = launch_sites_df.join(success_fail_counts, on='Launch Site')


# Create a dash application
app = dash.Dash(__name__)

# Create an app layout
app.layout = html.Div(children=[html.H1('SpaceX Launch Records Dashboard',
                                        style={'textAlign': 'center', 'color': '#503D36',
                                               'font-size': 40}),
                                # TASK 1: Add a dropdown list to enable Launch Site selection
                                # The default select value is for ALL sites
                                # dcc.Dropdown(id='site-dropdown',...)
                                html.Br(),
                                dcc.Dropdown(id='site-dropdown',
                                                options = site_options,
                                                value='ALL',
                                                placeholder="Select a Launch Site here",
                                                searchable=True
                                            ),
                                # TASK 2: Add a pie chart to show the total successful launches count for all sites
                                # If a specific launch site was selected, show the Success vs. Failed counts for the site
                                html.Div(dcc.Graph(id='success-pie-chart')),
                                html.Br(),

                                html.P("Payload range (Kg):"),
                                # TASK 3: Add a slider to select payload range
                                #dcc.RangeSlider(id='payload-slider',...)
                                dcc.RangeSlider(
                                    id='payload-slider',
                                    step=1000,
                                    marks={},  # Las marcas se actualizarán dinámicamente desde el callback
                                    value=[0, 10000],  # El valor inicial puede ser un rango arbitrario que luego se actualizará
                                ),
                                # TASK 4: Add a scatter chart to show the correlation between payload and launch success
                                html.Div(dcc.Graph(id='success-payload-scatter-chart')),
                                ])

# TASK 2:
# Add a callback function for `site-dropdown` as input, `success-pie-chart` as output
@app.callback( Output(component_id='success-pie-chart', component_property='figure'),
               Input(component_id='site-dropdown', component_property='value'))
# Add computation to callback function and return graph

def get_graph(lauch_sites_selection):
    # ALL means pie chart showing all the sites, individually
    if lauch_sites_selection == "ALL":
    # Si se selecciona "ALL", mostrar datos para cada sitio en el gráfico (a ver como funciona el melt)
        # pie_data = launch_sites_df.melt(id_vars=['Launch Site'], value_vars=['Success', 'Fail'], 
        #                                 var_name='Outcome', value_name='Count')
        pie_data = launch_sites_df.melt(id_vars=['Launch Site'], value_vars=['Success'], 
                                        var_name='Outcome', value_name='Count')
        pie_title = 'Total Success Launche By Site'
    else:
        # Filtrar solo para el sitio específico y preparar los datos para cada caso
        site_data = launch_sites_df[launch_sites_df['Launch Site'] == lauch_sites_selection]
        pie_data = site_data.melt(id_vars=['Launch Site'], value_vars=['Success', 'Fail'], 
                                var_name='Outcome', value_name='Count')
        pie_title=f'Success and Fail Counts for {lauch_sites_selection}'
                # Para el slider luego, estamos usando unas variables globales

    fig = px.pie(pie_data, names='Launch Site' if lauch_sites_selection == "ALL" else 'Outcome', 
                values='Count', 
                #title=f'Success and Fail Counts for {"All Sites" if lauch_sites_selection == "ALL" else lauch_sites_selection}',
                title = pie_title,
                color='Outcome' if lauch_sites_selection != "ALL" else 'Launch Site')
    return fig

# TASK 3.5
# Update the slider range based on the selected site
@app.callback(
    Output(component_id='payload-slider', component_property='marks'),
    Output(component_id='payload-slider', component_property='min'),
    Output(component_id='payload-slider', component_property='max'),
    Input(component_id='site-dropdown', component_property='value')
)
def update_slider_range(selected_site):
    if selected_site == 'ALL':
        # Si seleccionamos "ALL", usamos los valores min y max globales
        min_payload = int(spacex_df['Payload Mass (kg)'].min())  # Convertir a int
        # max_payload = int(spacex_df['Payload Mass (kg)'].max())  # Convertir a int
        max_payload = 10000
        # Definimos marcas cada 1000 kg
        marks = {i: f'{i} kg' for i in range(min_payload, max_payload + 1, 1000)}
    else:
        # Si se selecciona un sitio específico, filtramos por ese sitio
        site_df = spacex_df[spacex_df['Launch Site'] == selected_site]
        min_payload = int(site_df['Payload Mass (kg)'].min())  # Convertir a int
        max_payload = int(site_df['Payload Mass (kg)'].max())  # Convertir a int
        # Definimos marcas cada 1000 kg
        marks = {i: f'{i} kg' for i in range(min_payload, max_payload + 1, 1000)}

    return marks, min_payload, max_payload

# TASK 4:
# Add a callback function for `site-dropdown` and `payload-slider` as inputs, `success-payload-scatter-chart` as output
@app.callback(
    Output(component_id='success-payload-scatter-chart', component_property='figure'),
    [Input(component_id='site-dropdown', component_property='value'),
     Input(component_id='payload-slider', component_property='value')]
)
def update_scatter_chart(selected_site, payload_range):
    min_payload, max_payload = payload_range
    
    # Filtrar según el rango de la carga útil (Payload Mass)
    filtered_df = spacex_df[(spacex_df['Payload Mass (kg)'] >= min_payload) & 
                            (spacex_df['Payload Mass (kg)'] <= max_payload)]

    if selected_site == 'ALL':
        # filtered_df = spacex_df[(spacex_df['Payload Mass (kg)'] >= min_payload) & 
        #                         (spacex_df['Payload Mass (kg)'] <= max_payload)]
        title = "Payload vs Success (All Sites)"
        color_column = 'Launch Site'
    else:
        # filtered_df = spacex_df[(spacex_df['Launch Site'] == selected_site) &
        #                         (spacex_df['Payload Mass (kg)'] >= min_payload) &
        #                         (spacex_df['Payload Mass (kg)'] <= max_payload)]
        filtered_df = filtered_df[filtered_df['Launch Site'] == selected_site]
        title = f"Payload vs Success for {selected_site}"
        color_column = 'Booster Version Category'

    fig = px.scatter(
        filtered_df,
        x='Payload Mass (kg)',
        y='class',
        color=color_column, # De esta forma es como podemos diferenciar entre los boosters o los sites
        title=title,
        labels={'class': 'Launch Outcome (1=Success, 0=Failure)', 'Payload Mass (kg)': 'Payload Mass (kg)'},
        hover_data=['Launch Site', 'Booster Version Category']
    )
    
    # Asegurarse de que los ejes sean siempre positivos y con márgenes desde los bordes
    fig.update_layout(
        xaxis=dict(
            range=[0, filtered_df['Payload Mass (kg)'].max() + 500],  # Ajustar el rango de x
            showgrid=True
        ),
        yaxis=dict(
            range=[-0.1, 1.1],  # Añadir margen por encima de 1 y debajo de 0 en el eje y
            tickvals=[0, 1],  # Solo mostrar los valores 0 y 1
            showgrid=True
        ),
        margin=dict(l=50, r=50, t=50, b=50)  # Añadir márgenes al gráfico
    )
    
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server()
