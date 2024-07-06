import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import xarray as xr
import numpy as np
import io
import requests
import os
import tempfile

st.set_page_config(
    page_title="Dashboard Visualisasi Interaktif",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Function to download and process data
def download_and_process_data(resolution, longitude, latitude, start_year, end_year):
    st.header('Download Data Curah Hujan Reanalysis Otomatis')
    
    # Create a temporary directory for saving files
    temp_dir = tempfile.TemporaryDirectory()

    # Define the template URL based on the dataset and resolution
    if resolution == 'p05':
        template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/'
    elif resolution == 'p25':
        template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p25/'

    # Loop through the years
    for iy in range(start_year, end_year + 1):
        fname = f'chirps-v2.0.{iy}.days_{resolution}.nc'

        # Download the file
        link = template + fname
        st.info(f"Sedang mengunduh {fname}")
        st.warning('Pastikan tidak menutup/berpindah halaman ketika sedang mengunduh!')
        response = requests.get(link, stream=True)

        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 1024
            progress_bar = st.progress(0)
            temp_file_path = tempfile.NamedTemporaryFile(delete=False).name

            try:
                # Write to the temporary file
                with open(temp_file_path, 'wb') as tmp_file:
                    for data in response.iter_content(chunk_size):
                        tmp_file.write(data)
                        progress_bar.progress(tmp_file.tell() / total_size)

                progress_bar.empty()
                st.success(f"Memotong {fname} sesuai koordinat terpilih")

                # Process the file (slice to region of interest and save)
                with xr.open_dataarray(temp_file_path, decode_times=False) as data:
                    data['time'] = pd.date_range(start=f'{iy}-01-01', end=f'{iy}-12-31', periods=len(data.time))
                    sliced_data = data.sel(longitude=slice(longitude[0], longitude[1]), latitude=slice(latitude[0], latitude[1]))
                    final_path = os.path.join(temp_dir.name, fname)
                    sliced_data.to_netcdf(final_path)  # Save sliced data to temporary directory
                    st.success(f"Berhasil mengunduh dan menyimpan {fname}")

                    # Provide a download link for the user
                    with open(final_path, 'rb') as f:
                        st.download_button(label=f"Unduh {fname}", data=f, file_name=fname)

            except Exception as e:
                st.error(f"Kesalahan dalam memproses {fname}: {e}")

            finally:
                try:
                    os.remove(temp_file_path)  # Clean up temporary file
                except Exception as e:
                    st.error(f"Kesalahan dalam menghapus temporary file: {e}")
        else:
            st.error(f"Gagal mengunduh {fname} dari {link}")

# Function to load and visualize NetCDF data
def visualize_netCDF_data(file_content):
    st.title('Visualisasi Data Curah Hujan')
    st.caption("*Berhasil mengunduh dan menyimpan pada file NetCDF.*")
    
    # Load data from uploaded file
    with xr.open_dataset(io.BytesIO(file_content), engine='h5netcdf') as data:
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

        # Compute monthly sums along the time dimension
        pr_monthly_sum = data[pr_var].resample(time='1MS').sum(dim='time')

        # Select the precipitation data for visualization
        available_months = pr_monthly_sum['time'].dt.strftime('%B %Y').values
        selected_month = st.selectbox('Pilih Bulan', available_months)

        pr_selected = pr_monthly_sum.sel(time=selected_month)

        # Define precipitation ranges and labels
        precip_ranges = [-np.inf, 50, 150, 300, 500, 750, np.inf]
        precip_labels = ['<50 mm', '50-150 mm', '150-300 mm', '300-500 mm', '500-750 mm', '>750 mm']

        # Flatten the data for plotting
        lat_flat = data[lat_var].values.repeat(len(data[lon_var].values))
        lon_flat = np.tile(data[lon_var].values, len(data[lat_var].values))
        pr_flat = pr_selected.values.flatten()

        # Filter out NaN and non-positive values
        valid_mask = ~np.isnan(pr_flat) & (pr_flat > 0)
        lat_valid = lat_flat[valid_mask]
        lon_valid = lon_flat[valid_mask]
        pr_valid = pr_flat[valid_mask]

        # Digitize the precipitation data to categorize them
        pr_categories = np.digitize(pr_valid, bins=precip_ranges) - 1
        colors = px.colors.sequential.RdBu[::2][:len(precip_ranges)]

        # Create a Plotly figure for the map
        fig_map = go.Figure()

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
                    y=-0.15,
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
                center={"lat": float(np.mean(data[lat_var].values)), "lon": float(np.mean(data[lon_var].values))},
                zoom=3.5,
            ),
            width=1000,
            height=600,
            title={'text': f'Peta {name_var} Curah Hujan Bulanan Periode {selected_month}',
                   'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top',
                   'font': {'size': 20, 'family': 'Arial, sans-serif'}},
            autosize=True,
            margin={"r": 0, "t": 100, "l": 0, "b": 0}
        )

        # Display the Plotly map in Streamlit
        st.plotly_chart(fig_map)
        st.divider()

        # Calculate precipitation category counts for the pie chart
        precip_counts = np.histogram(pr_selected.values.flatten(), bins=precip_ranges)[0]

        fig_pie = go.Figure(data=[go.Pie(
            labels=precip_labels,
            values=precip_counts,
            hole=0.4,
            marker=dict(colors=colors)
        )])

        # Update layout of the pie chart
        fig_pie.update_layout(
            title=dict(
                text=f'Distribusi Curah Hujan periode {selected_month}',
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
        longitude = col[0].slider('Longitude', min_value=-180.0, max_value=180.0, value=[0.0, 120.0], step=0.1)
        latitude = col[1].slider('Latitude', min_value=-90.0, max_value=90.0, value=[-50.0, 50.0], step=0.1)

        # Display a download button for processed data
        if st.button('Proses dan Unduh'):
            download_and_process_data(resolution, longitude, latitude, start_year, end_year)

# Main section of the Streamlit app
def main():
    st.sidebar.title('Pilih Tab')
    tab_selection = st.sidebar.radio('Navigasi tab di atas', ('Data Unduh', 'Visualisasi netCDF'))
    
    if tab_selection == 'Data Unduh':
        st.header('Data Unduh CHIRPS Reanalysis')
        st.caption("*Silakan pilih resolusi dan tahun data yang akan diunduh.*")
        
        resolution = st.radio('Pilih Resolusi', ('p05', 'p25'))
        start_year = st.number_input('Pilih tahun awal', 1981, 2021, 2021 - 40)
        end_year = st.number_input('Pilih tahun akhir', 1981, 2021, 2021)
        
        if st.button('Unduh'):
            link = f"https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/{resolution}/chirps-v2.0.2021.days_{resolution}.nc"
            response = requests.get(link, stream=True)
            if response.status_code == 200:
                with open('data.nc', 'wb') as f:
                    f.write(response.content)
                st.success("Berhasil mengunduh file CHIRPS Reanalysis.")

    elif tab_selection == 'Visualisasi netCDF':
        st.header('Visualisasi Data netCDF')
        st.caption("*Silakan unggah file netCDF untuk visualisasi.*")

        uploaded_file = st.file_uploader("Unggah file netCDF", type=['nc'])

        if uploaded_file is not None:
            file_content = uploaded_file.read()

            try:
                visualize_netCDF_data(file_content)
            except Exception as e:
                st.error(f"Kesalahan dalam memproses file netCDF: {e}")

# Entry point of the Streamlit app
if __name__ == '__main__':
    main()
