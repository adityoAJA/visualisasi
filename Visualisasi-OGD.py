import streamlit as st
import pandas as pd
import xarray as xr
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import requests
import os
import tempfile

st.set_page_config(
        page_title="Dashboard Adityo W",
        page_icon="🏠",
        layout="centered",
        initial_sidebar_state="expanded"
    )

st.title('Dashboard Visualisasi Interaktif')

tabs = st.tabs(['Download Data Reanalysis','Visualisasi netCDF'])

with tabs[0]:
    # Function to download and process data
        def download_and_process_data(varname, resolution, longitude, latitude, start_year, end_year):
            if resolution == 'p05':
                template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/'
            elif resolution == 'p25':
                template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p25/'
            
            for iy in range(start_year, end_year + 1):
                fname = f'chirps-v2.0.{iy}.days_{resolution}.nc'
                link = template + fname
                st.info(f"Sedang mengunduh {fname}")
                st.warning('Pastikan tidak menutup atau berpindah halaman ketika sedang mengunduh!')
                response = requests.get(link, stream=True)
        
                if response.status_code == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    chunk_size = 1024
                    progress_bar = st.progress(0)
                    
                    try:
                        # Create a temporary file
                        temp_file_fd, temp_file_path = tempfile.mkstemp(suffix='.nc', prefix=f'{varname}_{iy}_{resolution}_', dir='/tmp')
                        
                        with os.fdopen(temp_file_fd, 'wb') as tmp_file:
                            for data in response.iter_content(chunk_size):
                                tmp_file.write(data)
                                progress_bar.progress(tmp_file.tell() / total_size)
                    
                        progress_bar.empty()
                        st.success(f"Berhasil mengunduh {fname} dari server")
                        
                        # Load and process the downloaded NetCDF file
                        with xr.open_dataset(temp_file_path, decode_times=False) as data:
                            data['time'] = pd.date_range(start=f'{iy}-01-01', end=f'{iy}-12-31', periods=len(data.time))
                            sliced_data = data.sel(longitude=slice(longitude[0], longitude[1]), latitude=slice(latitude[0], latitude[1]))
        
                            # Save sliced data to a temporary file
                            final_tmp_path = f"/tmp/{varname}_{iy}_{resolution}_sliced.nc"
                            sliced_data.to_netcdf(final_tmp_path)
                            st.success(f"Memotong dan menyimpan {fname} sesuai koordinat terpilih")
                            
                            # Save the file information to session state
                            if 'download_files' not in st.session_state:
                                st.session_state['download_files'] = []
                            st.session_state['download_files'].append((final_tmp_path, f"{varname}_{iy}_{resolution}_sliced.nc"))
                    
                    except Exception as e:
                        st.error(f"Kesalahan dalam memproses {fname}: {e}")
                    
                    finally:
                        try:
                            os.remove(temp_file_path)  # Hapus file sementara setelah digunakan
                        except Exception as e:
                            st.error(f"Kesalahan dalam menghapus temporary file: {e}")
                
                else:
                    st.error(f"Gagal mengunduh {fname} dari {link}")
        
        # Streamlit app
        def main():
            st.subheader('Download Data Curah Hujan Reanalysis Otomatis')
        
            varname = 'Curah Hujan'
            resolution = st.selectbox('Pilih Resolusi', ['p05', 'p25'])
        
            with st.expander(":blue-background[**Keterangan :**]"):
                st.caption("*Dataset yang digunakan :* **CHIRPS.**")
                st.caption("**Deskripsi :** *Data Curah Hujan Harian Global.*")
                st.caption(("**p05 :** *Resolusi Tinggi 5 x 5 km (ukuran file 1-1,2 GB).*"))
                st.caption(("**p25 :** *Resolusi Menengah 25 x 25 km (ukuran file 60-70 MB).*"))
        
            longitude = st.slider('Pilih Rentang Bujur', min_value=90.0, max_value=145.0, value=(95.0, 141.45), step=0.1)
            latitude = st.slider('Pilih Rentang Lintang', min_value=-12.0, max_value=8.0, value=(-11.08, 6.0), step=0.1)
        
            with st.expander(":blue-background[**Keterangan :**]"):
                st.caption("*Default Rentang wilayah yang digunakan adalah Lintang dan Bujur di wilayah Indonesia.*")
                st.caption("*Data yang akan tersimpan akan dipotong sesuai pilihan Lintang dan Bujur yang diinginkan.*")
        
            col1, col2 = st.columns(2)
            with col1:
                start_year = st.number_input('Tahun Awal', min_value=1981, max_value=2024, value=1981, step=1)
            with col2:
                end_year = st.number_input('Tahun Akhir', min_value=1981, max_value=2024, value=1981, step=1)
        
            with st.expander(":blue-background[**Keterangan :**]"):
                st.caption("**Deskripsi :** *Data Curah Hujan dimulai dari tahun 1981 s.d 2024.*")
                st.caption("*Data akan didownload per tahun, bila ingin mendownload 1 tahun saja maka tahun awal dan tahun akhir disamakan.*")
        
            if st.button('Download Data'):
                download_and_process_data(varname, resolution, longitude, latitude, start_year, end_year)
        
            # Display download buttons for available files
            if 'download_files' in st.session_state and st.session_state['download_files']:
                with st.expander(':green-background[**Simpan file :**]'):
                    st.caption('*File sudah siap disimpan ke direktori lokal dengan klik tombol di bawah*')
                for file_path, file_name in st.session_state['download_files']:
                    with open(file_path, "rb") as file:
                        st.download_button(
                            label=f"{file_name}",
                            data=file,
                            file_name=file_name
                        )
        
        if __name__ == '__main__':
            main()
                    
with tabs[1]:
    # File uploader for custom NetCDF files
            st.subheader("Visualisasi Data Reanalysis dan Proyeksi")
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
                def load_data(file_content):
                    try:
                        with xr.open_dataset(io.BytesIO(file_content), engine='h5netcdf') as data:
                            return data.load()
                    except Exception as e:
                        st.error(f"Error loading data: {e}")
                        return None

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
                        size=5,
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
