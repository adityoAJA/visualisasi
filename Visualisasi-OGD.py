import streamlit as st
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

tabs = st.tabs(['Download Data Reanalysis', 'Visualisasi netCDF'])

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

                    # Open the downloaded NetCDF file using xarray directly
                    try:
                        data = xr.open_dataset(temp_file_path, decode_times=False)
                        data['time'] = pd.date_range(start=f'{iy}-01-01', end=f'{iy}-12-31', periods=len(data.time))
                        sliced_data = data.sel(longitude=slice(longitude[0], longitude[1]), latitude=slice(latitude[0], latitude[1]))

                        # Save sliced data to a temporary file
                        final_tmp_path = f"/tmp/{varname}_{iy}_{resolution}.nc"
                        sliced_data.to_netcdf(final_tmp_path)
                        st.success(f"Memotong dan menyimpan {fname} sesuai koordinat terpilih")

                        # Save the file information to session state
                        if 'download_files' not in st.session_state:
                            st.session_state['download_files'] = []
                        st.session_state['download_files'].append((final_tmp_path, f"{varname}_{iy}_{resolution}.nc"))

                    except Exception as e:
                        st.error(f"Kesalahan dalam memproses {fname}: {e}")

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
            st.session_state['download_files'] = []  # Reset the session state for new downloads
            download_and_process_data(varname, resolution, longitude, latitude, start_year, end_year)

        # Display download buttons for available files
        if 'download_files' in st.session_state and st.session_state['download_files']:
            with st.expander(':green-background[**Simpan file :**]'):
                st.caption('*File sudah siap disimpan ke direktori lokal dengan klik tombol di bawah*')
            for idx, (file_path, file_name) in enumerate(st.session_state['download_files']):
                with open(file_path, "rb") as file:
                    st.download_button(
                        label=f"Unduh {file_name}",
                        data=file,
                        file_name=file_name,
                        key=f"download_button_{idx}"  # Unique key for each file
                    )

    if __name__ == '__main__':
        main()

with tabs[1]:
    st.subheader("Visualisasi Data Reanalysis dan Proyeksi")
    uploaded_file = st.file_uploader("Unggah file", type=["nc"])
    
    with st.expander(":blue-background[**Keterangan :**]"):
        st.caption("**Jenis data yang dapat divisualisasikan :**")
        st.caption("*Data CHIRPS :* *data curah hujan dengan variabel : precip, latitude, longitude*")
        st.caption("*Data CMIP6 :* *data curah hujan dengan variabel : pr, lat, lon*")
        
    if uploaded_file is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file.flush()

            data = xr.open_dataset(temp_file.name, decode_times=False)
            variable_options = data.data_vars.keys()
            coordinate_options = data.coords.keys()

            if 'precip' in variable_options and {'latitude', 'longitude'}.issubset(coordinate_options):
                dataset_type = 'CHIRPS'
                varname = 'precip'
                lat = 'latitude'
                lon = 'longitude'
            elif 'pr' in variable_options and {'lat', 'lon'}.issubset(coordinate_options):
                dataset_type = 'CMIP6'
                varname = 'pr'
                lat = 'lat'
                lon = 'lon'
            else:
                st.error('File tidak memiliki struktur data yang sesuai. Pastikan file memiliki variabel dan koordinat yang sesuai.')
                st.stop()

            st.success(f'File netCDF diunggah dan dikenali sebagai data {dataset_type} dengan variabel "{varname}".')
            
            # Create a monthly summed dataset
            monthly_data = data[varname].resample(time='1M').sum(dim='time')

            # Dropdown to select month
            selected_month = st.selectbox('Pilih Bulan', options=range(1, 13), format_func=lambda x: f'Bulan {x}')

            # Select data for the chosen month
            selected_data = monthly_data.sel(time=monthly_data['time.month'] == selected_month)

            # Display the map and pie chart
            st.write(f'Menampilkan peta untuk bulan {selected_month}')

            fig = px.imshow(selected_data, x=lon, y=lat, origin='upper', aspect='auto')
            st.plotly_chart(fig)

            # Allow user to input coordinates
            st.write('Masukkan koordinat untuk melihat data series.')
            longitude_input = st.number_input('Bujur', min_value=float(data[lon].min()), max_value=float(data[lon].max()), step=0.01)
            latitude_input = st.number_input('Lintang', min_value=float(data[lat].min()), max_value=float(data[lat].max()), step=0.01)

            if st.button('Tampilkan Data Series'):
                series_data = data[varname].sel({lon: longitude_input, lat: latitude_input}, method='nearest')
                st.write(f'Data series untuk koordinat ({latitude_input}, {longitude_input}):')
                st.line_chart(series_data)

        except Exception as e:
            st.error(f'Terjadi kesalahan saat membaca atau memproses file: {e}')
