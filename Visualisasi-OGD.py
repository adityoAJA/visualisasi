import streamlit as st
import pandas as pd
import xarray as xr
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io

st.set_page_config(
        page_title="Visualisasi Adit",
        page_icon="🏠",
        layout="centered",
        initial_sidebar_state="expanded"
    )

st.title('Demo Visualisasi Interaktif')

tabs = st.tabs(['Peta Anomali Bulanan','Warming Stripes','Visualisasi netCDF'])

@st.cache_data
def load_excel_data(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    return df

# Path to your Excel file
file_path = "Anomali.xlsx"

with tabs[1]:
     # Load the data
                st.header("Warming Stripes Per Provinsi")

                df6 = load_excel_data(file_path, sheet_name='Stripes')

                # Sort the data by Year
                data = df6.sort_values(by='Tahun')

                # menjadikan kolom sebagai data list
                options = data.columns[1:].tolist()

                # kolom yang dipilih untuk visualisasi
                selected_column = st.selectbox("Pilih Wilayah", options)

                # Create a temperature stripe plot using Plotly based on the selected column
                def create_temperature_stripe(data, column):
                    fig = px.imshow(
                        [data[column]],
                        labels={'x': 'Tahun', 'color': 'Anomali (°C)'},
                        x=data['Tahun'].astype(str),
                        color_continuous_scale='RdBu_r',
                        aspect="auto"
                    )
                    fig.update_yaxes(showticklabels=False)  # Hide y-axis ticks
                    
                    fig.update_layout(
                        coloraxis_colorbar=dict(tickformat='.2f', title="°C"),
                        xaxis={'side': 'bottom'},
                        title={'text': f"Anomali Suhu Udara Tahunan di {selected_column}", 'x':0.45, 'y':0.95,
                        'xanchor':'center', 'yanchor':'top',
                        'font':{'size':18,'family':'Arial, sans-serif'}},
                    width=1000,  # Set the width to 1000 pixels
                    height=400,
                    )
                    fig.update_xaxes(tickangle=360)
                    fig.update_traces(hovertemplate='Tahun: %{x}<br>Anomali: %{z:.2f}°C<extra></extra>')
                    return fig

                # Plot the temperature stripe based on the selected column
                fig = create_temperature_stripe(data, selected_column)
                st.plotly_chart(fig)

with tabs[0]:
      # peta anomali, mondif, suhu bulanan
            st.header("Peta Anomali Suhu Udara Per Bulan")

            df4 = load_excel_data(file_path, sheet_name='GIS')

            # Extract unique months from the 'Bulan' column
            bulan_options = df4['Bulan'].unique()

            # Selectbox for choosing month
            selected_bulan = st.select_slider("Pilih Bulan", bulan_options)

            # Filter the DataFrame based on the selected month
            filtered_df2 = df4[df4['Bulan'] == selected_bulan]

            # kolom parameter dijadikan list pilihan
            param = df4.columns[4:].tolist()

            # visualisasi berdasarkan pilihan parameter
            selected_param = st.selectbox("Pilih Kondisi Suhu Udara", param)

            # Determine the color based on the selected parameter
            if selected_param in ["Anomali Suhu Udara Rata-Rata", "Selisih Suhu Udara Rata-Rata"]:
                # Set color to blue where selected_param is positive, and red otherwise
                color_values = filtered_df2[selected_param].apply(lambda x: 'red' if x > 0 else 'blue')
            elif selected_param == "Suhu Udara Rata-Rata":
                # Set color to black for all values
                color_values = 'black'

            # membuat peta
            fig = go.Figure()

            # Add scatter trace
            fig.add_trace(go.Scattermapbox(
                lat=filtered_df2['Lat'],
                lon=filtered_df2['Lon'],
                mode='markers+text',
                marker=go.scattermapbox.Marker(
                    size=16,
                    color=color_values,
                    opacity=1
                ),
                text=filtered_df2[selected_param].apply(lambda x: f'{x:.1f}'),
                textposition="top center",
                textfont=dict(color='black', size=11),
                hoverinfo='text',
                hovertext=filtered_df2['Stasiun'] + '<br>' + selected_param + ': ' + filtered_df2[selected_param].apply(lambda x: f'{x:.1f}') + ' °C'
            ))

            # Manually set the center of the map
            center_lat = -2  # Replace with your desired latitude
            center_lon = 118  # Replace with your desired longitude

            # Update layout
            fig.update_layout(title=f"Peta Sebaran {selected_param} Bulan {selected_bulan} 2024",
                            title_font=dict(size=18),  # Set the font size of the title
                            title_x=0.15,  # Set the x-position of the title
                            title_y=0.9,
                            mapbox_style="open-street-map",
                            mapbox_zoom=3.4,
                            mapbox_center={"lat": center_lat, "lon": center_lon},
                            # margin={"r":0,"t":0,"l":0,"b":0},  # margins peta dengan konten atas,bawah,kiri,kanan
                            margin={"b":0},
                            height=400,
                            width=900,
                            showlegend=False)

            # Display the Plotly map in Streamlit
            st.plotly_chart(fig)

            st.caption(":blue-background[Keterangan :]")
            st.caption(('''
                        **Anomali Suhu Udara Rata-Rata :**
                        *Selisih Suhu Udara Rata-Rata Bulan Terpilih dengan Normal 1991-2020.*'''))
            st.caption(('''
                        **Selisih Suhu Udara Rata-Rata :**
                        *Selisih Suhu Udara Rata-Rata Bulan Terpilih dengan Bulan Sebelumnya.*'''))

with tabs[2]:
    # File uploader for custom NetCDF files
            st.header("Visualisasi Data Reanalysis dan Proyeksi")
            # uploader untuk file netCDF
            uploaded_file = st.file_uploader("Unggah file", type=["nc"])
            with st.expander(":blue-background[**Keterangan :**]"):
                    st.caption("**Jenis data yang bisa diunggah hanya untuk parameter curah hujan, dengan kriteria yaitu :**")
                    st.caption("**Kriteria 1 (Data CHIRPS):** *Pastikan nama variabel dalam file nc meliputi precip, latitude, longitude.*")
                    st.caption("**Kriteria 2 (Data CMIP6) :** *Pastikan nama variabel dalam file nc meliputi pr, lat, lon.*")

            if uploaded_file is not None:
                # Read the file content into a buffer
                file_content = uploaded_file.read()

                # Load the data from the buffer with caching to avoid reloading on every interaction
                @st.cache_data
                def load_data(file_content):
                    with xr.open_dataset(io.BytesIO(file_content), engine='h5netcdf') as data:
                        return data.load()

                # Load the data
                data = load_data(file_content)

                # Determine the precipitation variable name ('precip' or 'pr')
                if 'precip' in data:
                    pr_var = 'precip'
                    lat_var = 'latitude'
                    lon_var = 'longitude'
                    name_var = 'Reanalysis'
                elif 'pr' in data:
                    pr_var = 'pr'
                    lat_var = 'lat'
                    lon_var = 'lon'
                    name_var = 'Proyeksi'
                else:
                    st.error("Tidak ada variabel yang sesuai kriteria dalam file netCDF anda.")
                    st.stop()

                # Extract necessary variables
                lat = data[lat_var].values
                lon = data[lon_var].values
                pr = data[pr_var]

                # If pr_var is 'pr', convert precipitation values to millimeters per day
                if pr_var == 'pr':
                    pr *= 86400

                # Compute monthly sums along the time dimension
                pr_monthly_sum = pr.resample(time='1MS').sum(dim='time')

                # membuat list bulan
                available_months = pr_monthly_sum['time'].dt.strftime('%B %Y').values

                # memilih bulan yang akan ditampilkan
                selected_month = st.selectbox('Pilih Bulan', available_months)

                # Select the precipitation data for the chosen month
                pr_selected = pr_monthly_sum.sel(time=selected_month)

                # Define precipitation ranges and labels
                precip_ranges = [-np.inf, 50, 150, 300, 500, 750, np.inf]
                precip_labels = ['<50 mm', '50-150 mm', '150-300 mm', '300-500 mm', '500-750 mm', '>750 mm']

                # Flatten the data for plotting
                lat_flat = lat.repeat(len(lon))
                lon_flat = np.tile(lon, len(lat))
                pr_flat = pr_selected.values.flatten()

                # Filter out NaN and non-positive values
                valid_mask = ~np.isnan(pr_flat) & (pr_flat > 0)
                lat_valid = lat_flat[valid_mask]
                lon_valid = lon_flat[valid_mask]
                pr_valid = pr_flat[valid_mask]

                # Digitize the precipitation data to categorize them
                pr_categories = np.digitize(pr_valid, bins=precip_ranges) - 1
                colors = px.colors.sequential.RdBu[::2][:len(precip_ranges)]

                # Create a Plotly figure
                fig_map = go.Figure()

                # Add scatter plot trace
                fig_map.add_trace(go.Scattermapbox(
                    lat=lat_valid,
                    lon=lon_valid,
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=6,
                        color=pr_categories,
                        colorscale=colors,
                        cmin=0,
                        cmax=len(precip_ranges) - 1,
                        colorbar=dict(
                            title='Curah Hujan (mm)',
                            orientation='h',
                            x=0.5,
                            y=-0.25,
                            len=0.9,
                            thickness=15,
                            tickvals=np.arange(1, len(precip_ranges) - 1),
                            ticktext=precip_ranges[1:]
                        )
                    ),
                    text=[f'Lintang: {lat}<br>Bujur: {lon}<br>Curah Hujan: {pr:.3f}' 
                        for pr, lat, lon in zip(pr_valid, lat_valid, lon_valid)],
                    hoverinfo='text'
                ))

                # Update layout with Mapbox for basemap
                fig_map.update_layout(
                    mapbox=dict(
                        style="open-street-map",
                        center={"lat": float(np.mean(lat)), "lon": float(np.mean(lon))},
                        zoom=3,
                    ),
                    width=900,
                    height=500,
                    title={'text': f'Peta {name_var} Curah Hujan Bulanan Periode {selected_month}',
                               'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top',
                                'font':{'size':20,'family':'Arial, sans-serif'}},
                    autosize=True,
                    margin={"r": 0, "t": 100, "l": 0, "b": 0}
                )

                # Display the Plotly map in Streamlit
                st.plotly_chart(fig_map)
                st.divider()

                # Calculate precipitation category counts for the pie chart
                precip_counts = np.histogram(pr_valid, bins=precip_ranges)[0]

                fig_pie = go.Figure(data=[go.Pie(
                        labels=precip_labels,
                        values=precip_counts,
                        hole=0.4,
                        marker=dict(colors=colors)
                    )])

                # Options for traceorder: 'normal', 'reversed', 'grouped', 'reversed+grouped'
                fig_pie.update_layout(
                    title=dict(
                        text=f'Distribusi Curah Hujan<br>periode {selected_month}',
                        font=dict(size=20),
                        x=0.5,
                        xanchor='center'
                    ),
                    legend=dict(
                        title=dict(
                            text='milimeter (mm) :',
                            font=dict(size=14, family='Calibri, sans-serif')
                        ),
                        x=0.5,
                        y=-0.1,
                        orientation='h',
                        yanchor='top',
                        xanchor='center',
                        traceorder='normal'
                    )
                )

                # Add annotation in the center of the hole
                fig_pie.add_annotation(dict(
                    text=f'Total Titik<br>{sum(precip_counts)}',
                    x=0.5,
                    y=0.5,
                    font_size=15,
                    showarrow=False
                ))

                st.plotly_chart(fig_pie)
                st.divider()

                # User input for selecting longitude and latitude
                col = st.columns(2)
                with col[0]:
                    selected_lat = st.number_input('Input Lintang', value=-2.000, format="%.3f", step=0.025, key='lat_input')
                with col[1]:
                    selected_lon = st.number_input('Input Bujur', value=120.000, format="%.3f", step=0.025, key='lon_input')

                # Display the list of coordinates in an expander
                with st.expander(":blue-background[**Keterangan :**]"):
                    st.caption("*Ketik titik koordinat berdasarkan referensi koordinat dari peta reanalysis di atas (arahkan kursor di atas peta)*")
                    st.caption("*Atau bisa menambahkan atau mengurangi nilai dengan klik tanda tambah atau kurang*")
                    st.caption("*Apabila tidak muncul nilai pada line chart, berarti tidak ada nilai curah hujan (NaN) pada titik tersebut*")

                # Find closest indices to selected lon and lat
                lon_idx = np.abs(lon - selected_lon).argmin()
                lat_idx = np.abs(lat - selected_lat).argmin()

                pr_timeseries = pr[:, lat_idx, lon_idx].values

                # Convert time series to pandas DataFrame for easier plotting with Plotly Express
                df = pd.DataFrame({
                        'Rentang Waktu': pr.time.values,
                        'Curah Hujan (mm/hari)': pr_timeseries
                    })

                # Create a Plotly line chart for the time series
                fig_line = px.line(df, x='Rentang Waktu', y='Curah Hujan (mm/hari)')
                    
                # Update layout of the line chart
                fig_line.update_layout(
                        xaxis_title='Rentang Waktu',
                        yaxis_title='Curah Hujan (mm/hari)',
                        title={'text': f'Grafik Curah Hujan Harian Pada Koordinat {selected_lon} dan {selected_lat}',
                               'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top',
                                'font':{'size':18,'family':'Arial, sans-serif'}},
                        margin={"r": 0, "t": 100, "l": 0, "b": 0}
                    )

                # Display the Plotly line chart in Streamlit
                st.plotly_chart(fig_line)

            else:
                st.write("Silahkan unggah file netCDF anda untuk visualisasi data yaa.")
