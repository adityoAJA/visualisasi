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

st.title('Dashboard Visualisasi Interaktif')

# tabs = st.tabs(['Download Data Reanalysis', 'Visualisasi netCDF'])

# with tabs[0]:
#     st.header('Download Data Curah Hujan Reanalysis Otomatis')
#     # Function to download and process data
#     def download_and_process_data(varname, resolution, longitude, latitude, start_year, end_year):
#         # Create a temporary directory for saving files
#         temp_dir = tempfile.TemporaryDirectory()

#         # Define the template URL based on the dataset and resolution
#         if resolution == 'p05':
#             template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/'
#         elif resolution == 'p25':
#             template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p25/'

#         # Loop through the years
#         for iy in range(start_year, end_year + 1):
#             fname = f'chirps-v2.0.{iy}.days_{resolution}.nc'

#             # Download the file
#             link = template + fname
#             st.info(f"Sedang mengunduh {fname}")
#             st.warning('Pastikan tidak menutup/berpindah halaman ketika sedang mengunduh!')
#             response = requests.get(link, stream=True)

#             if response.status_code == 200:
#                 total_size = int(response.headers.get('content-length', 0))
#                 chunk_size = 1024
#                 progress_bar = st.progress(0)
#                 temp_file_path = tempfile.NamedTemporaryFile(delete=False).name

#                 try:
#                     # Write to the temporary file
#                     with open(temp_file_path, 'wb') as tmp_file:
#                         for data in response.iter_content(chunk_size):
#                             tmp_file.write(data)
#                             progress_bar.progress(tmp_file.tell() / total_size)

#                     progress_bar.empty()
#                     st.success(f"Memotong {fname} sesuai koordinat terpilih")

#                     # Process the file (slice to region of interest and save)
#                     with xr.open_dataarray(temp_file_path, decode_times=False) as data:
#                         data['time'] = pd.date_range(start=str(iy)+'-01-01', end=str(iy)+'-12-31', periods=len(data.time))
#                         sliced_data = data.sel(longitude=slice(longitude[0], longitude[1]), latitude=slice(latitude[0], latitude[1]))
#                         final_path = os.path.join(temp_dir.name, fname)
#                         sliced_data.to_netcdf(final_path)  # Save sliced data to temporary directory
#                         st.success(f"Berhasil mengunduh dan menyimpan {fname}")

#                         # Provide a download link for the user
#                         with open(final_path, 'rb') as f:
#                             st.download_button(label=f"Unduh {fname}", data=f, file_name=fname)

#                 except Exception as e:
#                     st.error(f"Kesalahan dalam memproses {fname}: {e}")

#                 finally:
#                     try:
#                         os.remove(temp_file_path)  # Clean up temporary file
#                     except Exception as e:
#                         st.error(f"Kesalahan dalam menghapus temporary file: {e}")
#             else:
#                 st.error(f"Gagal mengunduh {fname} dari {link}")

#     # Streamlit app
#     def main():
#         # Set the dataset and variable
#         varname = 'Curah Hujan'

#         # Resolution selection for CHIRPS dataset
#         resolution = st.selectbox('Pilih Resolusi', ['p05', 'p25'])

#         with st.expander(":blue-background[**Keterangan :**]"):
#             st.caption("*Dataset yang digunakan :* **CHIRPS.**")
#             st.caption("**Deskripsi :** *Data Curah Hujan Harian Global.*")
#             st.caption(("**p05 :** *Resolusi Tinggi 5 x 5 km (ukuran file 1-1,2 GB).*"))
#             st.caption(("**p25 :** *Resolusi Menengah 25 x 25 km (ukuran file 60-70 MB).*"))

#         longitude = st.slider('Pilih Rentang Bujur', min_value=90.0, max_value=145.0, value=(95.0, 141.45), step=0.1)
#         latitude = st.slider('Pilih Rentang Lintang', min_value=-12.0, max_value=8.0, value=(-11.08, 6.0), step=0.1)

#         with st.expander(":blue-background[**Keterangan :**]"):
#             st.caption("*Defalut Rentang wilayah yang digunakan adalah Lintang dan Bujur di wilayah Indonesia.*")
#             st.caption("*Data yang akan tersimpan akan dipotong sesuai pilihan Lintang dan Bujur yang diinginkan.*")

#         col1, col2 = st.columns(2)
#         with col1:
#             start_year = st.number_input('Tahun Awal', min_value=1981, max_value=2024, value=1981, step=1)
#         with col2:
#             end_year = st.number_input('Tahun Akhir', min_value=1981, max_value=2024, value=1981, step=1)

#         with st.expander(":blue-background[**Keterangan :**]"):
#             st.caption("**Deskripsi :** *Data Curah Hujan dimulai dari tahun 1981 s.d 2024.*")
#             st.caption("*Data akan didownload per tahun, bila ingin mendownload 1 tahun saja maka tahun awal dan tahun akhir disamakan.*")

#         # Download button
#         if st.button('Download Data'):
#             download_and_process_data(varname, resolution, longitude, latitude, start_year, end_year)

#     if __name__ == '__main__':
#         main()
    
# with tabs[1]:
# Fungsi untuk memuat data dari file yang diunggah
@st.cache(show_spinner=False)
def load_data(file_content):
    with xr.open_dataset(io.BytesIO(file_content), engine='h5netcdf') as data:
        return data.load()

# Menampilkan peta curah hujan
def show_precipitation_map(data):
    # Menentukan variabel curah hujan
    if 'precip' in data:
        precip_var = 'precip'
    elif 'pr' in data:
        precip_var = 'pr'
    else:
        st.error("Tidak dapat menemukan variabel curah hujan yang sesuai dalam dataset.")
        return

    # Mengambil data latitude, longitude, dan curah hujan
    lat = data['latitude'].values
    lon = data['longitude'].values
    precip = data[precip_var]

    # Menghitung jumlah bulanan curah hujan
    precip_monthly_sum = precip.resample(time='1MS').sum(dim='time')

    # Membuat list bulan yang tersedia
    available_months = precip_monthly_sum['time'].dt.strftime('%B %Y').values

    # Memilih bulan yang akan ditampilkan
    selected_month = st.selectbox('Pilih Bulan', available_months)

    # Memilih data curah hujan untuk bulan yang dipilih
    precip_selected = precip_monthly_sum.sel(time=selected_month)

    # Menghitung kategori curah hujan dan mempersiapkan warna untuk plot
    precip_ranges = [-np.inf, 50, 150, 300, 500, 750, np.inf]
    precip_labels = ['<50 mm', '50-150 mm', '150-300 mm', '300-500 mm', '500-750 mm', '>750 mm']
    precip_categories = np.digitize(precip_selected.values.flatten(), bins=precip_ranges) - 1
    colors = px.colors.sequential.RdBu[::2][:len(precip_ranges)]

    # Membuat plot peta menggunakan Plotly
    fig = go.Figure(go.Scattermapbox(
        lat=lat.flatten(),
        lon=lon.flatten(),
        mode='markers',
        marker=dict(
            size=8,
            color=precip_categories,
            colorscale=colors,
            colorbar=dict(
                title='Curah Hujan (mm)',
                tickvals=np.arange(len(precip_ranges) - 1),
                ticktext=precip_labels
            )
        ),
        text=f'Curah Hujan: {precip_selected.values.flatten()} mm',
        hoverinfo='text'
    ))

    # Mengatur layout peta menggunakan Mapbox
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": np.mean(lat), "lon": np.mean(lon)},
        mapbox_zoom=3.5,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        width=1000,
        height=600,
        title=f'Peta Curah Hujan Bulanan Periode {selected_month}'
    )

    # Menampilkan plot peta menggunakan Streamlit
    st.plotly_chart(fig)

    # Calculate precipitation category counts for the pie chart
    precip_counts = np.histogram(precip_selected.values.flatten(), bins=precip_ranges)[0]

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

    pr_timeseries = precip[:, lat_idx, lon_idx].values

    # Convert time series to pandas DataFrame for easier plotting with Plotly Express
    df = pd.DataFrame({
        'Rentang Waktu': precip.time.values,
        'Curah Hujan (mm/hari)': pr_timeseries
    })

    # Create a Plotly line chart for the time series
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=df['Rentang Waktu'], y=df['Curah Hujan (mm/hari)'],
                                  mode='lines+markers', name='Curah Hujan (mm/hari)'))

    # Update layout of the line chart
    fig_line.update_layout(
        xaxis_title='Rentang Waktu',
        yaxis_title='Curah Hujan (mm/hari)',
        title={'text': f'Grafik Curah Hujan Harian Pada Koordinat {selected_lon} dan {selected_lat}',
               'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top',
               'font': {'size': 18, 'family': 'Arial, sans-serif'}},
        margin={"r": 0, "t": 100, "l": 0, "b": 0}
    )

    # Display the Plotly line chart in Streamlit
    st.plotly_chart(fig_line)

# Streamlit app
def main():
    st.title('Visualisasi Data Curah Hujan')

    # File uploader untuk data NetCDF
    uploaded_file = st.file_uploader("Unggah file NetCDF", type=["nc"])

    if uploaded_file is not None:
        # Membaca isi file ke dalam buffer
        file_content = uploaded_file.read()

        # Memuat data dari file menggunakan cache
        data = load_data(file_content)

        # Menampilkan peta curah hujan
        show_precipitation_map(data)

    else:
        st.write("Silakan unggah file NetCDF Anda untuk memulai visualisasi.")

if __name__ == '__main__':
    main()
