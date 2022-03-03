from dash.dependencies import Input, Output, ALL, State, MATCH, ALLSMALLER
from app import app
from dash import html
import numpy as np
import pandas as pd
import figures
import Summary
import page1FarmView
import Decarbonization

@app.callback(
    Output('Visible-content', 'children'),
    Input("tabs", "active_tab")
)
def switch_tab(tab):
    if tab == 'summary-tab':
        return Summary.content
    elif tab == 'flows-tab':
        return page1FarmView.content
    elif tab == 'decrb-tab':
        return Decarbonization.content

@app.callback(
    [Output('transit_figure1', 'figure'),
     Output('transit_figure2', 'figure'),
     Output('transit_figure3', 'figure'),
     Output('transit_figure4', 'figure')],
    [Input("select-year", "value")]
)
def update_options(year):
    # figures.Update_UNstats_database(year)

    return figures.UNstats_plots(year)[0],figures.UNstats_plots(year)[1],figures.UNstats_plots(year)[2],figures.land_use_plot()



@app.callback(
    Output('figure1', 'figure'),
    [Input("select-year", "value"),
     Input("select-country", "value"),
     Input("product_drpdwn", "value")]
)
def sensor_checklist(year,country,selected_products):

    Interest_list = ['Crude Petroleum', 'Refined Petroleum', 'Petroleum', 'Petroleum Gas', 'Coal Briquettes',
                     'Petroleum Coke', 'Fuel Wood', 'Coconut Oil', 'Ferroalloys', 'Nickel Mattes', 'Nickel Ore',
                     'Aluminium Ore', 'Non-Petroleum Gas', 'Hydrogen', 'Tug Boats', 'Fishing Ships',
                     'Non-fillet Frozen Fish',
                     'Cars', 'Busses', 'Delivery Trucks', 'Motorcycles', 'Bicycles',
                     'Combustion Engines', 'Engine Parts', 'Gas Turbines', 'Spark-Ignition Engines',
                     'Planes, Helicopters, and/or Spacecraft', 'Aircraft Parts',
                     'Passenger and Cargo Ships']


    df_exp= pd.read_csv("Data/{}/Exports-{}---Click-to-Select-a-Product.csv".format(country,year))
    df_imp = pd.read_csv("Data/{}/Imports-{}---Click-to-Select-a-Product.csv".format(country,year))
    df_imp['Trade Value'] = -df_imp['Trade Value']/1000000
    df_exp['Trade Value'] = df_exp['Trade Value']/1000000


    return figures.import_export_figure(df_imp,df_exp,selected_products,year)



@app.callback(
    Output('product_drpdwn', 'options'),
    [Input("select-year", "value"),
     Input("select-country", "value")]
)
def update_options(year,country):
    items = []
    df_exp= pd.read_csv("Data/{}/Exports-{}---Click-to-Select-a-Product.csv".format(country,year))
    df_imp = pd.read_csv("Data/{}/Imports-{}---Click-to-Select-a-Product.csv".format(country,year))

    for i in df_exp['HS4']:
        items.append(i)
    for i in df_imp['HS4']:
        items.append(i)
    product_list = set(items)
    return [{"label": i, "value": i} for i in product_list]



@app.callback(
    [Output('Sankey_figure', 'figure'),
     Output('Sankey_elec_figure', 'figure')],
     [Input("select-year", "value"),
     Input("select-country", "value"),
]
)
def sensor_checklist(year,country):
    return figures.Generate_Sankey(year,country)[0],figures.Generate_Sankey(year,country)[1]


@app.callback(
    [Output('generation-cost', 'children'),
     Output('power-generated', 'children'),
     Output('lost-cost', 'children'),
     Output('generation-efficiency', 'children'),
     Output('required_RE', 'figure'),
     Output('oil_to_RE', 'figure'),
     Output('annual_demand', 'figure'),
     Output('rooftop_PV_plot', 'figure'),
     Output('scenarios-plot', 'figure'),
     Output('scenarios-plot-cum', 'figure'),
     Output('scenarios-annaul-RE', 'figure'),
     Output('scenarios-annual-carbon', 'figure'),
     Output('emission-quantity', 'children'),
     Output('emission-cost', 'children')],
    Input('update-button','n_clicks'),
    [State("select-year", "value"),
     State("select-country", "value"),
    State("diesel_price_slider", "value"),
     State("PV-cost", "value"),
     State("PV-battery-cost", "value"),
    State("wind-battery-cost", "value"),
     State("wind-large-cost", "value"),
     State("demand-growth", "value"),
    State('decarb-year', "value"),
     State('rooftop-size', "value"),
    State('emissions-rate', "value"),
     State('carbon-price', "value"),
     State('Wind_PV_share', "value"),
     State('small-PV-share', "value"),
     State('small-wind-share', "value"),

     ])
def sensor_checklist(n_clicks,year,country,diesel_price,PV_cost,PVBatt_cost,WindBatt_cost,Wind_cost,demand_growth,decarb_year,rooftop_size,emission_kgperlitre,
                     emission_dollarpertonne,wind_share, small_PV_share,small_wind_share):
    if n_clicks:
        diesel_HHV = 3.74/1000000
        df = pd.read_csv("Data/Sankey/csv/{}/{}.csv".format(year,country))

        oil_supplied_TJ = df[(df[' (from)'] == 'Oil: Supplied') & (df[' (to)'] == 'PowerStations')][' (weight)'] # Tj- Modifty the units
        Natural_gas_supplied = df[(df[' (from)'] == 'Natural Gas: Supplied') & (df[' (to)'] == 'PowerStations')][' (weight)'] # Tj- Modifty the units
        oil_supplied_litre = oil_supplied_TJ/diesel_HHV
        oil_supplied_cost = int(oil_supplied_litre * diesel_price/1000000)#$MM

        power_generated_TJ = df[(df[' (from)'] == 'PowerStations') & (df[' (to)'] == 'Electricity & Heat: Supplied')][' (weight)'] #TJ
        power_generated_GWh = int(power_generated_TJ * 0.2777)
        power_stations_input_TJ = df[df[' (to)'] == 'PowerStations'][' (weight)'].sum()
        Efficiency = int(100*(power_generated_TJ/power_stations_input_TJ))

        transformation_losses_cost = int(oil_supplied_cost * (1-Efficiency/100))
        #44 MJ/kg
        # 0.85 kg/l
        #37.4e-6 TJ/l

        df_p = pd.read_excel('Data/Potentials.xlsx')
        # print(df_p.loc[2, country],power_generated_GWh)
        Wind_pot = df_p.loc[2, country] #GWh/MW/year
        PV_pot = df_p.loc[0, country] #GWh/MW/year

        PV_decarb_MW = int(1.2 * power_generated_GWh/ PV_pot)
        wind_decarb_MW = int(1.2 * power_generated_GWh / Wind_pot)

        PV_install_with_oil = int((oil_supplied_cost * 1000000/PV_cost)/1000000)
        PV_bat_install_with_oil = int((oil_supplied_cost * 1000000/PVBatt_cost)/1000000)
        Wind_bat_install_with_oil = int((oil_supplied_cost * 1000000/WindBatt_cost)/1000000)
        Wind_install_with_oil = int((oil_supplied_cost * 1000000/Wind_cost)/1000000)

        x = max(PV_decarb_MW,wind_decarb_MW,PV_install_with_oil,PV_bat_install_with_oil)

        #Emissions
        emissions_mtonne = float(oil_supplied_litre * emission_kgperlitre/1000000000)
        emission_cost_mdollar = float(emission_dollarpertonne * emissions_mtonne)
        emissions_mtonne = round(emissions_mtonne, 2)
        emission_cost_mdollar = round(emission_cost_mdollar, 2)

        return [oil_supplied_cost, power_generated_GWh, transformation_losses_cost,Efficiency,figures.potentials_bar(wind_decarb_MW,PV_decarb_MW,x,year),
                figures.oil_to_RE(PV_install_with_oil,PV_bat_install_with_oil,Wind_install_with_oil,Wind_bat_install_with_oil,x,year),
                figures.annual_demand(power_generated_GWh, demand_growth, decarb_year),
                figures.rooftop_PV_plot(country, rooftop_size,x),
                figures.decarbonization_scenarios(power_generated_GWh, demand_growth, PV_cost,PVBatt_cost,
                                                  WindBatt_cost,Wind_cost,decarb_year,wind_share,small_PV_share,
                                                  small_wind_share,PV_pot,Wind_pot,diesel_HHV,diesel_price)[0],
                figures.decarbonization_scenarios(power_generated_GWh, demand_growth, PV_cost, PVBatt_cost,
                                                  WindBatt_cost, Wind_cost, decarb_year, wind_share, small_PV_share,
                                                  small_wind_share, PV_pot, Wind_pot, diesel_HHV, diesel_price)[1],
                figures.decarbonization_scenarios(power_generated_GWh, demand_growth, PV_cost, PVBatt_cost,
                                                  WindBatt_cost, Wind_cost, decarb_year, wind_share, small_PV_share,
                                                  small_wind_share, PV_pot, Wind_pot, diesel_HHV, diesel_price)[2],
                figures.decarbonization_scenarios(power_generated_GWh, demand_growth, PV_cost, PVBatt_cost,
                                                  WindBatt_cost, Wind_cost, decarb_year, wind_share, small_PV_share,
                                                  small_wind_share, PV_pot, Wind_pot, diesel_HHV, diesel_price)[3],
                emissions_mtonne, emission_cost_mdollar
                ]
    else:
        pass

