import streamlit as st
import pandas as pd
import numpy as np
import xarray as xr
import plotly.express as px
import plotly.graph_objects as go
import io

# Set layout
st.set_page_config(
        page_title="Dashboard Perubahan Iklim",
        page_icon="🏠",
        layout="centered",
        initial_sidebar_state="expanded"
    )

# judul
st.header("Visualisasi Data Reanalysis dan Proyeksi")
st.empty()
# uploader untuk file netCDF
uploaded_file = st.file_uploader("Unggah file", type=["nc"])
# narasi mengenai data yang diupload
with st.expander(":blue-background[**Keterangan :**]"):
		st.caption("**Jenis data yang bisa diunggah hanya untuk parameter curah hujan, dengan kriteria yaitu :**")
		st.caption("**Kriteria 1 (Data CHIRPS):** *Pastikan nama variabel dalam file nc meliputi precip, latitude, longitude.*")
		st.caption("**Kriteria 2 (Data CMIP6) :** *Pastikan nama variabel dalam file nc meliputi pr, lat, lon.*")
		st.caption('Jika anda ingin mendownload data proyeksi (CMIP6), silahkan klik tombol di bawah ini')
		st.link_button("Unduh Data Proyeksi", "https://aims2.llnl.gov/search/cmip6/")

if uploaded_file is not None:
	# membaca file yang diupload
	file_content = uploaded_file.read()

	# fungsi load data
	@st.cache_data
	def load_data(file_content):
		with xr.open_dataset(io.BytesIO(file_content), engine='h5netcdf') as data:
			return data.load()

	# membaca data yang diupload
	data = load_data(file_content, decode_times=False)

	# mendefinisikan nama dari data
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

	# Extrak parameter yang diperlukan
	lat = data[lat_var].values
	lon = data[lon_var].values
	pr = data[pr_var]

	# konversi data bila proyeksi
	if pr_var == 'pr':
		pr *= 86400

	# akumulasi bulanan
	pr_monthly_sum = pr.resample(time='1MS').sum(dim='time')

	# membuat daftar bulan
	available_months = pr_monthly_sum['time'].dt.strftime('%B %Y').values

	# memilih bulan yang akan ditampilkan
	selected_month = st.selectbox('Pilih Bulan', available_months)

	# pilih data pr sesuai bulan tepilih
	pr_selected = pr_monthly_sum.sel(time=selected_month)

	# mendefinisikan ranges and labels curah hujan
	precip_ranges = [-np.inf, 50, 150, 300, 500, 750, np.inf]
	precip_labels = ['<50 mm', '50-150 mm', '150-300 mm', '300-500 mm', '500-750 mm', '>750 mm']

	# koordinat 2 dimensi
	lat_flat = lat.repeat(len(lon))
	lon_flat = np.tile(lon, len(lat))
	pr_flat = pr_selected.values.flatten()

	# membuang NaN dan nilai negatif
	valid_mask = ~np.isnan(pr_flat) & (pr_flat > 0)
	lat_valid = lat_flat[valid_mask]
	lon_valid = lon_flat[valid_mask]
	pr_valid = pr_flat[valid_mask]

	# menyesuaikan warna
	pr_categories = np.digitize(pr_valid, bins=precip_ranges) - 1
	colors = px.colors.sequential.RdBu[::2][:len(precip_ranges)]

	# membuat peta
	fig_map = go.Figure()

	# menambahkan marker, colorbar
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

	# titik tengah koordinat
	center_lat = -2 
	center_lon = 118 

	# Update layout with posisi dan ukuran
	fig_map.update_layout(
		mapbox=dict(
			style="open-street-map",
			center={"lat": center_lat, "lon": center_lon},
			zoom=3.5,
		),
		width=1000,
		height=600,
		title={'text': f'Peta {name_var} Curah Hujan Bulanan Periode {selected_month}',
				'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top',
					'font':{'size':20,'family':'Arial, sans-serif'}},
		autosize=True,
		margin={"r": 0, "t": 100, "l": 0, "b": 0}
	)

	# Display peta
	st.plotly_chart(fig_map)
	st.divider()

	# menghitung jumlah pr per kategori
	precip_counts = np.histogram(pr_valid, bins=precip_ranges)[0]

	# membuat pie chart
	fig_pie = go.Figure(data=[go.Pie(
			labels=precip_labels,
			values=precip_counts,
			hole=0.4,
			marker=dict(colors=colors)
		)])

	# update layout judul, legend
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
			traceorder='normal' # pilihan traceorder: 'normal', 'reversed', 'grouped', 'reversed+grouped'
		)
	)

	# menambahkan keterangan pada hole pie chart
	fig_pie.add_annotation(dict(
		text=f'Total Titik<br>{sum(precip_counts)}',
		x=0.5,
		y=0.5,
		font_size=15,
		showarrow=False
	))

	# display chart
	st.plotly_chart(fig_pie)
	st.divider()

	# membuat inputan koordinat
	col = st.columns(2)
	with col[0]:
		selected_lat = st.number_input('Input Lintang', value=-2.000, format="%.3f", step=0.025, key='lat_input')
	with col[1]:
		selected_lon = st.number_input('Input Bujur', value=120.000, format="%.3f", step=0.025, key='lon_input')

	# membuat narasi dalam keterangan
	with st.expander(":blue-background[**Keterangan :**]"):
		st.caption("*Ketik titik koordinat berdasarkan referensi koordinat dari peta reanalysis di atas (arahkan kursor di atas peta)*")
		st.caption("*Atau bisa menambahkan atau mengurangi nilai dengan klik tanda tambah atau kurang*")
		st.caption("*Apabila tidak muncul nilai pada line chart, berarti tidak ada nilai curah hujan (NaN) pada titik tersebut*")

	# mencari nilai lat dan lon terdekat
	lon_idx = np.abs(lon - selected_lon).argmin()
	lat_idx = np.abs(lat - selected_lat).argmin()

	pr_timeseries = pr[:, lat_idx, lon_idx].values

	# konversi dataframe
	df = pd.DataFrame({
			'Rentang Waktu': pr.time.values,
			'Curah Hujan (mm/hari)': pr_timeseries
		})

	# membuat line chart
	fig_line = px.line(df, x='Rentang Waktu', y='Curah Hujan (mm/hari)')
		
	# Update layout judul dan posisi
	fig_line.update_layout(
			xaxis_title='Rentang Waktu',
			yaxis_title='Curah Hujan (mm/hari)',
			title={'text': f'Grafik Curah Hujan Harian Pada Koordinat {selected_lon} dan {selected_lat}',
				'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top',
					'font':{'size':18,'family':'Arial, sans-serif'}},
			margin={"r": 0, "t": 100, "l": 0, "b": 0}
		)

	# Display line chart
	st.plotly_chart(fig_line)

else:
	st.write("Silahkan unggah file netCDF anda untuk visualisasi data.")
