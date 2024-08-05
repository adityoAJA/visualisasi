import streamlit as st
import pandas as pd
import xarray as xr
import requests
import os
import tempfile
from auth import authenticate
from datetime import datetime, timedelta

# fungsi komponen download
def download_and_process_data(dataname, varname, resolution, longitude, latitude, start_year, end_year):

    # mendefinisikan URL
    if dataname == 'CHIRTS':
        template = f'https://data.chc.ucsb.edu/products/CHIRTSdaily/v1.0/global_netcdf_p05/{varname}/'
    elif dataname == 'CHIRPS':
        if resolution == 'p05':
            template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/'
        elif resolution == 'p25':
            template = 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p25/'

    # mengulangi untuk pilihan tahun > 1
    for iy in range(start_year, end_year + 1):
        # konstruksi nama file
        if dataname == 'CHIRTS':
            fname = f'{varname}.{iy}.nc'
        elif dataname == 'CHIRPS':
            fname = f'chirps-v2.0.{iy}.days_{resolution}.nc'

        # Download the file
        link = template + fname
        st.info(f"Sedang mengunduh {fname} dari server")
        response = requests.get(link, stream=True)

        # mengakses HTML / koneksi       
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 1024
            progress_bar = st.progress(0)
            temp_file_path = tempfile.NamedTemporaryFile(delete=False).name

            try:
                # membuat temporary file
                with open(temp_file_path, 'wb') as tmp_file:
                    for data in response.iter_content(chunk_size):
                        tmp_file.write(data)
                        progress_bar.progress(tmp_file.tell() / total_size)
                
                progress_bar.empty()
                st.success(f"Memotong {fname} sesuai koordinat terpilih")

                # memotong data sesuai koordinat terpilih
                with xr.open_dataarray(temp_file_path, decode_times=False) as data:
                    data['time'] = pd.date_range(start=f"{iy}-01-01", end=f"{iy}-12-31", periods=len(data.time))
                    sliced_data = data.sel(longitude=slice(longitude[0], longitude[1]), latitude=slice(latitude[0], latitude[1]))

                    # menyimpan data pada temporary file
                    with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp_file:
                        sliced_data.to_netcdf(tmp_file.name)
                        final_tmp_path = tmp_file.name

                    # menyimpan informasi pada session state
                    if 'download_files' not in st.session_state:
                        st.session_state['download_files'] = []
                    st.session_state['download_files'].append((final_tmp_path, f"{varname}_{iy}_{resolution}.nc"))

            except Exception as e:
                st.error(f"Kesalahan dalam memproses {fname}: {e}")

            finally:
                try:
                    os.remove(temp_file_path)  # membersihkan temporary file
                except Exception as e:
                    st.error(f"Kesalahan dalam menghapus temporary file: {e}")
        else:
            st.error(f"Gagal mengunduh {fname} dari {link}")

# fungsi display download
def main():
    st.header('Download Data Reanalysis Otomatis')

    # memilih parameter
    varname = st.selectbox('Pilih Parameter', ['Precipitation', 'Tmax', 'Tmin'])
    
    # penjelasan singkat mengenai parameter terpilih
    if varname == 'Precipitation':
        dataname = 'CHIRPS'
        with st.expander("**Keterangan :**"):
            st.caption(f"*Dataset yang digunakan :* **{dataname}.**")
            st.caption("**Deskripsi :** *Data Curah Hujan Harian Global.*")
            st.caption('''
                        **p05 :**
                            *Resolusi Tinggi 5 x 5 km (ukuran file 1-2 GB).*
                        ''')
            st.caption('''
                        **p25 :**
                            *Resolusi Menengah 25 x 25 km (ukuran file 60-70 MB).*
                        ''')
        # memilih resolusi
        resolution = st.selectbox('Pilih Resolusi', ['p05', 'p25'])
    else:
        dataname = 'CHIRTS'
        with st.expander("**Keterangan :**"):
            st.caption(f"*Dataset yang digunakan :* **{dataname}.**")
            st.caption("**Deskripsi :** *Data Suhu Udara Maksimum (Tmax) atau Minimum (Tmin) Harian Global.*")
            st.caption("**Resolusi :** *5 x 5 km (ukuran file 25 GB).*")
        resolution = None  # tidak ada pilihan untuk CHIRTS dataset

    # komponen slider / memilih koordinat
    longitude = st.slider('Pilih Rentang Bujur', min_value=90.0, max_value=145.0, value=(105.0, 125.0), step=0.1)
    latitude = st.slider('Pilih Rentang Lintang', min_value=-12.0, max_value=8.0, value=(-5.0, 7.0), step=0.1)
    # narasi terkait koordinat
    with st.expander("**Keterangan :**"):
        st.caption("*Default Rentang wilayah yang digunakan adalah Lintang dan Bujur di wilayah Indonesia.*")
        st.caption("*Data yang akan tersimpan akan dipotong sesuai pilihan Lintang dan Bujur yang diinginkan.*")
    
    # membuat input tahun pilihan
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input('Tahun Awal', min_value=1981, max_value=2024, value=1991, step=1)
    with col2:
        end_year = st.number_input('Tahun Akhir', min_value=1981, max_value=2024, value=2010, step=1)

    # narasi mengenai ketersediaan tahun pada dataset pilihan
    if varname == 'Precipitation':
        with st.expander("**Keterangan :**"):
            st.caption("**Parameter :** *Curah Hujan (Precipitation).*")
            st.caption("**Deskripsi :** *Dimulai dari tahun 1981 s.d 2024.*")
    else:
        with st.expander("**Keterangan :**"):
            st.caption("**Parameter :** *Tmax (suhu maksimum) dan Tmin (suhu minimum).*")
            st.caption("**Deskripsi :** *Dimulai dari tahun 1983 s.d 2016.*")
    
    if st.button('Download Data'):
        st.session_state['download_files'] = []  # daftar file download untuk beberapa pilihan / tahun
        download_and_process_data(dataname, varname, resolution, longitude, latitude, start_year, end_year)

    # Display tombol download
    if 'download_files' in st.session_state and st.session_state['download_files']:
        # narasi singkat
        with st.expander('**Simpan file :**'):
            st.caption('*File sudah siap disimpan ke direktori lokal dengan klik tombol di bawah*')
        for idx, (file_path, file_name) in enumerate(st.session_state['download_files']):
            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"{file_name}",
                    data=file,
                    file_name=file_name,
                    key=f"download_button_{idx}"  # Unique key untuk masing2 file
                )

if __name__ == '__main__':
    main()
