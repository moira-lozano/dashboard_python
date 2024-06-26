import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output

from data_fetcher import  (get_sales_by_year, get_sales_by_month, get_sales_by_date_range, get_products_by_sizes, get_products_by_model, 
                            get_products_by_color, get_products_by_brand, get_products_by_promotion, get_sales_recurring_customers, 
                            get_customer_name, get_conversion_rate)
import os
from dotenv import load_dotenv


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# URL del backend
BACKEND_URL = os.getenv('BACKEND_URL', 'https://microservicioproductos-production.up.railway.app/api')
OTHER_SERVICE_URL = os.getenv('OTHER_SERVICE_URL', 'http://4.203.105.3')
#OTHER_SERVICE_URL = os.getenv('OTHER_SERVICE_URL', 'http://127.0.0.1:8000')
GRAPHQL_ENDPOINT = os.getenv('GRAPHQL_ENDPOINT', 'http://18.218.15.90:8080/graphql')

# Obtener el puerto de la variable de entorno PORT (Railway lo asigna automáticamente)
port = int(os.getenv('PORT', 8050))

# Initialize the app with suppress_callback_exceptions
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Exponer el servidor Flask subyacente

# Obtener datos iniciales
sales_by_year = get_sales_by_year()

# Layout de la aplicación Dash
app.layout = html.Div(children=[
    html.Div([
        html.H1(children='DASHBOARD DE VENTAS', style={'textAlign': 'center', 'margin-bottom': '20px'})
    ]),

    dcc.Tabs(id='tabs', value='tab-ventas-totales', children=[
        dcc.Tab(label='Ventas Totales', value='tab-ventas-totales'),
        dcc.Tab(label='Productos Más Demandados', value='tab-productos-mas-comprados'),
        dcc.Tab(label='Tasa de Conversión de Clientes', value='tab-conversion-rate')
    ]),
    
    html.Div(id='tabs-content')
])

# Callback para actualizar el contenido basado en la pestaña seleccionada
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    if (tab == 'tab-ventas-totales'):
        return html.Div([
            dcc.RadioItems(
                id='ventas-radioitems',
                labelStyle={'display': 'inline-block'},
                options=[
                    {'label': 'Ventas totales por año', 'value': 'ventas_totales_año'},
                    {'label': 'Ventas totales por mes', 'value': 'ventas_totales_mes'},
                    {'label': 'Ventas totales por rango de fechas', 'value': 'ventas_totales_fecha'},
                    {'label': 'Ventas totales por clientes recurrentes', 'value': 'ventas_totales_cliente'}
                ],
                value='ventas_totales_año',
                style={'text-align': 'center', 'color': 'black'},
                className='dcc_compon'
            ),
            html.Div(id='controls-container', style={'textAlign': 'center', 'margin-bottom': '20px'}, children=[
                html.Div([
                    dcc.Dropdown(
                        id='year-dropdown',
                        options=[{'label': str(year['year']), 'value': year['year']} for year in sales_by_year],
                        value=sales_by_year[0]['year'] if sales_by_year else None
                    ),
                ], id='year-dropdown-container', style={'display': 'none', 'margin': '0 auto', 'width': '50%'}),
                
                html.Div([
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=pd.to_datetime('2023-01-01'),
                        end_date=pd.to_datetime('2023-12-31'),
                        display_format='YYYY-MM-DD',
                        style={'margin-bottom': '20px', 'margin': '0 auto'}
                    ),
                ], id='date-picker-container', style={'display': 'none', 'textAlign': 'center'}),
            ]),
            dcc.Graph(
                id='sales-graph'
            )
        ])
    elif (tab == 'tab-productos-mas-comprados'):
        return html.Div([
            dcc.RadioItems(
                id='productos-radioitems',
                labelStyle={'display': 'inline-block'},
                options=[
                    {'label': 'Por Talla', 'value': 'productos_por_talla'},
                    {'label': 'Por Modelo', 'value': 'productos_por_modelo'},
                    {'label': 'Por Color', 'value': 'productos_por_color'},
                    {'label': 'Por Marca', 'value': 'productos_por_marca'},
                    {'label': 'Por Promocion', 'value': 'productos_por_promocion'}
                ],
                value='productos_por_talla',
                style={'text-align': 'center', 'color': 'black'},
                className='dcc_compon'
            ),
            dcc.Graph(
                id='products-graph'
            )
        ])
    elif (tab == 'tab-conversion-rate'):
        # Obtener datos de tasa de conversión
        conversion_data = get_conversion_rate()
        df_conversion = pd.DataFrame(conversion_data)

        # Crear gráfico de línea de tasa de conversión
        fig = px.line(df_conversion, x='year', y='conversion_rate', title='Tasa de Conversión por Año',
                    labels={'year': 'Año', 'conversion_rate': 'Tasa de Conversión'})

        return html.Div([
            dcc.Graph(id='conversion-graph', figure=fig)
        ])

# Callback para actualizar el gráfico basado en la selección del usuario
@app.callback(
    [Output('sales-graph', 'figure'),
        Output('year-dropdown-container', 'style'),
        Output('date-picker-container', 'style')],
    [Input('ventas-radioitems', 'value'),
        Input('year-dropdown', 'value'),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date')]
)
def update_sales_graph(selected_option, selected_year, start_date, end_date):
    if selected_option == 'ventas_totales_año':
        sales_by_year = get_sales_by_year()
        df_year = pd.DataFrame(sales_by_year)
        fig = px.bar(df_year, x='year', y='total_sales', title='Total de Ventas por Año',
                labels={'year': 'Año', 'total_sales': 'Total de Ventas'},
                text_auto=True)
        return fig, {'display': 'none'}, {'display': 'none'}

    elif selected_option == 'ventas_totales_mes':
        if selected_year is None:
            return {}, {'display': 'block', 'textAlign': 'center'}, {'display': 'none'}
        sales_by_month = get_sales_by_month(selected_year)
        df_month = pd.DataFrame(sales_by_month)
        fig = px.bar(df_month, x='month', y='total_sales', title=f'Total de Ventas por Mes del {selected_year}',
                        labels={'month': 'Mes', 'total_sales': 'Total de Ventas'},
                        text_auto=True)
        return fig, {'display': 'block', 'textAlign': 'center'}, {'display': 'none'}
    
    elif selected_option == 'ventas_totales_fecha':
        if start_date is None or end_date is None:
            return {}, {'display': 'none'}, {'display': 'block', 'textAlign': 'center'}
        sales_by_date_range = get_sales_by_date_range(start_date, end_date)
        
        # Debug print to check the data format
        print(f'Sales by date range data: {sales_by_date_range}')
        
        if isinstance(sales_by_date_range, dict) and isinstance(sales_by_date_range.get('total_sales_by_month'), list):
            df_date_range = pd.DataFrame(sales_by_date_range['total_sales_by_month'])
            df_date_range['month'] = df_date_range['month'].apply(lambda x: f'{x:02}')
            df_date_range['date'] = df_date_range['year'].astype(str) + '-' + df_date_range['month']
            
            fig = px.bar(df_date_range, x='date', y='total_sales', title=f'Total de Ventas desde {start_date} hasta {end_date}',
                        labels={'date': 'Fecha', 'total_sales': 'Total de Ventas'},
                        text_auto=True)
            return fig, {'display': 'none'}, {'display': 'block', 'textAlign': 'center'}
        else:
            print('Error: Unexpected data format')
            return {}, {'display': 'none'}, {'display': 'block', 'textAlign': 'center'}
        
        
    elif selected_option == 'ventas_totales_cliente':
        sales_by_customers = get_sales_recurring_customers()
        
        # Filtrar y limitar los datos a los primeros 50 elementos donde total_spent >= 8000
        filtered_sales_by_customers = [customer for customer in sales_by_customers if customer['total_spent'] >= 8000][:50]
        
        customer_names = []
        for customer in filtered_sales_by_customers:
            customer_id = customer['customer_id']
            customer_name = get_customer_name(customer_id)
            customer_names.append(customer_name if customer_name else 'Desconocido')

        df_customers = pd.DataFrame(filtered_sales_by_customers)
        df_customers['customer_name'] = customer_names

        fig = px.bar(df_customers, x='customer_name', y='total_spent', title='Total de Ventas por Clientes Recurrentes',
                    labels={'customer_name': 'Nombre de Cliente', 'total_spent': 'Total Gastado'},
                    text=df_customers['total_spent'], height=500)
        min_total_spent = df_customers['total_spent'].min()
        fig.update_layout(yaxis=dict(range=[min_total_spent, df_customers['total_spent'].max()]))
    return fig, {'display': 'none'}, {'display': 'none'}

# Callback para actualizar el gráfico de productos más comprados
@app.callback(
    Output('products-graph', 'figure'),
    Input('productos-radioitems', 'value')
)
def update_products_graph(selected_option):
    if selected_option == 'productos_por_talla':
        products_by_sizes = get_products_by_sizes()
        df_products = pd.DataFrame(products_by_sizes)
        
        if df_products.empty:
            return {}
        
        # Crear gráfico de sectores
        fig = px.pie(df_products, names='talla', values='cantidad_vendida', color='producto', title='Productos más Comprados por Talla',
                    labels={'talla': 'Talla', 'cantidad_vendida': 'Cantidad', 'producto': 'Producto'})
        
        return fig
    
    elif selected_option == 'productos_por_modelo':
        products_by_model = get_products_by_model()
        df_products = pd.DataFrame(products_by_model)
        
        if df_products.empty:
            return {}
        
        # Crear gráfico de sectores
        fig = px.pie(df_products, names='modelo', values='cantidad_vendida', color='producto', title='Productos más Comprados por Modelo',
                    labels={'modelo': 'Modelo', 'cantidad_vendida': 'Cantidad', 'producto': 'Producto'})
        
        return fig
    
    elif selected_option == 'productos_por_color':
        products_by_color = get_products_by_color()
        df_products = pd.DataFrame(products_by_color)
        
        if df_products.empty:
            return {}
        
        # Crear gráfico de sectores
        fig = px.pie(df_products, names='color', values='cantidad_vendida', color='producto', title='Productos más Comprados por Color',
                    labels={'color': 'Color', 'cantidad_vendida': 'Cantidad', 'producto': 'Producto'})
        
        return fig
    
    elif selected_option == 'productos_por_marca':
        products_by_brand = get_products_by_brand()
        df_products = pd.DataFrame(products_by_brand)
        
        if df_products.empty:
            return {}
        
        # Crear gráfico de barras
        fig = px.bar(df_products, x='marca', y='cantidad_vendida', color='producto', title='Productos más Comprados por Marca',
                    labels={'marca': 'Marca', 'cantidad_vendida': 'Cantidad', 'producto': 'Producto'})
        
        return fig
    
    elif selected_option == 'productos_por_promocion':
        products_by_promotion = get_products_by_promotion()
        print("Datos recibidos de get_products_by_promotion:", products_by_promotion)  # Debugging print
        
        # Limitar los datos a los primeros 50 registros si hay más de 50
        if len(products_by_promotion) > 50:
            products_by_promotion = products_by_promotion[:50]
        
        df_products = pd.DataFrame(products_by_promotion)
        
        if df_products.empty:
            return {}
        
        print("DataFrame de productos por promocion:", df_products)  # Debugging print
        
        # Verificar si 'promocion' está en las columnas del DataFrame, si no, añadir una columna ficticia
        if 'promocion' not in df_products.columns:
            df_products['promocion'] = 'Promocion Activa'  # Añadir una columna ficticia si 'promocion' no está presente
        
        # Transformar los datos para que sean adecuados para un gráfico de barras agrupadas
        df_products_melted = df_products.melt(id_vars=['producto', 'promocion'], value_vars=['precio', 'descuento'],
                                            var_name='tipo', value_name='valor')
        
        print("DataFrame transformado:", df_products_melted)  # Debugging print
        
        # Crear gráfico de barras agrupadas
        fig = px.bar(df_products_melted, x='producto', y='valor', color='tipo', barmode='group',
                    title='Precio y Descuento de Productos en Promoción',
                    labels={'producto': 'Producto', 'valor': 'Valor', 'tipo': 'Tipo'})
    
    return fig

    
if __name__ == "__main__":
    # Ejecutar la aplicación en el puerto especificado
    app.run_server(host="0.0.0.0", port=port)
