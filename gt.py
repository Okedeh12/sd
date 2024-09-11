import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import os
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

# Koneksi ke SQLite
conn = sqlite3.connect('database_sekolah.db')
c = conn.cursor()

# Buat tabel jika belum ada
c.execute('''
CREATE TABLE IF NOT EXISTS pembayaran_spp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_siswa TEXT,
    kelas TEXT,
    bulan TEXT,
    jumlah INTEGER,
    tanggal TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS gaji_guru (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_guru TEXT,
    bulan TEXT,
    gaji INTEGER,
    tunjangan INTEGER,
    tanggal TEXT
)
''')
conn.commit()

# Koneksi ke SQLite
conn = sqlite3.connect('database_sekolah.db')
c = conn.cursor()

# Update table schema if the column is missing
c.execute('''
ALTER TABLE pembayaran_spp 
ADD COLUMN IF NOT EXISTS jumlah_pembayaran INTEGER
''')
conn.commit()

# Initialize in-memory session data
if "pembayaran_spp" not in st.session_state:
    st.session_state.pembayaran_spp = pd.DataFrame(columns=["Nama Siswa", "Kelas", "Bulan", "Jumlah Pembayaran", "Biaya SPP/Bulan"])

# Function to save SPP payment to CSV and SQL
def save_pembayaran_spp(nama_siswa, kelas, bulan, jumlah, biaya_spp):
    # Save to session state
    new_row = pd.DataFrame({
        "Nama Siswa": [nama_siswa],
        "Kelas": [kelas],
        "Bulan": [bulan],
        "Jumlah Pembayaran": [jumlah],
        "Biaya SPP/Bulan": [biaya_spp]
    })
    st.session_state.pembayaran_spp = pd.concat([st.session_state.pembayaran_spp, new_row], ignore_index=True)
    
    # Save to CSV
    st.session_state.pembayaran_spp.to_csv('pembayaran_spp.csv', index=False)
    
    # Save to SQLite
    c.execute("INSERT INTO pembayaran_spp (nama_siswa, kelas, bulan, jumlah_pembayaran, biaya_spp) VALUES (?, ?, ?, ?, ?)", 
              (nama_siswa, kelas, bulan, jumlah, biaya_spp))
    conn.commit()

# Fungsi untuk menyimpan data gaji guru ke SQLite dan CSV
def save_gaji_guru(nama_guru, bulan, gaji, tunjangan):
    tanggal = datetime.now().strftime('%Y-%m-%d')
    c.execute('INSERT INTO gaji_guru (nama_guru, bulan, gaji, tunjangan, tanggal) VALUES (?, ?, ?, ?, ?)',
              (nama_guru, bulan, gaji, tunjangan, tanggal))
    conn.commit()
    
    # Simpan juga ke CSV
    df_gaji = pd.DataFrame([{
        'Nama Guru': nama_guru,
        'Bulan': bulan,
        'Gaji Pokok': gaji,
        'Tunjangan': tunjangan,
        'Tanggal': tanggal
    }])

# Setup untuk judul dan desain sidebar menggunakan option_menu
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",  # Judul menu sidebar
        options=["Pembayaran SPP", "Laporan Keuangan", "Pengelolaan Gaji Guru"],  # Opsi di sidebar
        icons=["cash-stack", "bar-chart", "person-badge"],  # Ikon untuk setiap opsi
        menu_icon="cast",  # Ikon untuk menu utama
        default_index=0,  # Indeks default yang dipilih
        styles={
            "container": {"padding": "5!important", "background-color": "#f0f2f6"},  # Desain container
            "icon": {"color": "orange", "font-size": "25px"},  # Desain ikon
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},  # Desain link
            "nav-link-selected": {"background-color": "#4CAF50"},  # Desain link yang dipilih
        }
    )

# Konten halaman berdasarkan menu yang dipilih
if selected == "Pembayaran SPP":
    st.title("Pembayaran SPP")
    st.write("Halaman untuk pembayaran SPP siswa.")
    
    # Set up SQLite database connection
    conn = sqlite3.connect('spp_payments.db')
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS pembayaran_spp (
                nama_siswa TEXT, kelas TEXT, bulan TEXT, jumlah_pembayaran INTEGER, biaya_spp INTEGER)''')
    conn.commit()

    # Initialize in-memory session data
    if "pembayaran_spp" not in st.session_state:
        st.session_state.pembayaran_spp = pd.DataFrame(columns=["Nama Siswa", "Kelas", "Bulan", "Jumlah Pembayaran", "Biaya SPP/Bulan"])

# Function to save SPP payment to CSV and SQL
def save_pembayaran_spp(nama_siswa, kelas, bulan, jumlah, biaya_spp):
    # Save to session state
    new_row = pd.DataFrame({
        "Nama Siswa": [nama_siswa],
        "Kelas": [kelas],
        "Bulan": [bulan],
        "Jumlah Pembayaran": [jumlah],
        "Biaya SPP/Bulan": [biaya_spp]
    })
    st.session_state.pembayaran_spp = pd.concat([st.session_state.pembayaran_spp, new_row], ignore_index=True)
    
    # Save to CSV
    st.session_state.pembayaran_spp.to_csv('pembayaran_spp.csv', index=False)
    
    # Save to SQLite
    c.execute("INSERT INTO pembayaran_spp (nama_siswa, kelas, bulan, jumlah_pembayaran, biaya_spp) VALUES (?, ?, ?, ?, ?)", 
              (nama_siswa, kelas, bulan, jumlah, biaya_spp))
    conn.commit()

# Function to generate payment receipt as a PDF
def generate_receipt(nama_siswa, kelas, bulan, jumlah, biaya_spp):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Kwitansi Pembayaran SPP", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Nama Siswa: {nama_siswa}", ln=True)
    pdf.cell(200, 10, txt=f"Kelas: {kelas}", ln=True)
    pdf.cell(200, 10, txt=f"Bulan: {bulan}", ln=True)
    pdf.cell(200, 10, txt=f"Jumlah Pembayaran: Rp {jumlah}", ln=True)
    pdf.cell(200, 10, txt=f"Biaya SPP per Bulan: Rp {biaya_spp}", ln=True)
    pdf.cell(200, 10, txt=f"Tanggal: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    
    return pdf

# Setup untuk judul dan desain sidebar menggunakan option_menu
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",  # Judul menu sidebar
        options=["Pembayaran SPP", "Laporan Keuangan", "Pengelolaan Gaji Guru"],  # Opsi di sidebar
        icons=["cash-stack", "bar-chart", "person-badge"],  # Ikon untuk setiap opsi
        menu_icon="cast",  # Ikon untuk menu utama
        default_index=0,  # Indeks default yang dipilih
        styles={
            "container": {"padding": "5!important", "background-color": "#f0f2f6"},  # Desain container
            "icon": {"color": "orange", "font-size": "25px"},  # Desain ikon
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},  # Desain link
            "nav-link-selected": {"background-color": "#4CAF50"},  # Desain link yang dipilih
        }
    )

# Konten halaman berdasarkan menu yang dipilih
if selected == "Pembayaran SPP":
    st.title("Pembayaran SPP")
    st.write("Halaman untuk pembayaran SPP siswa.")
    
    # Simulasi input data pembayaran SPP menggunakan form
    with st.form("pembayaran_form"):
        nama_siswa = st.text_input("Nama Siswa")
        kelas = st.selectbox("Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])
        bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        biaya_spp = st.number_input("Biaya SPP per Bulan (Rp)", min_value=0)
        jumlah = st.number_input("Jumlah Pembayaran (Rp)", min_value=0)
        
        # Tombol submit
        submitted = st.form_submit_button("Bayar")
        
        if submitted:
            save_pembayaran_spp(nama_siswa, kelas, bulan, jumlah, biaya_spp)
            st.success(f"Pembayaran SPP untuk {nama_siswa} berhasil ditambahkan!")
            
            # Generate PDF receipt
            pdf = generate_receipt(nama_siswa, kelas, bulan, jumlah, biaya_spp)
            
            # Button to download PDF receipt
            pdf_output = BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)
            st.download_button(
                label="Download Kwitansi",
                data=pdf_output,
                file_name=f"Kwitansi_SPP_{nama_siswa}_{bulan}.pdf",
                mime="application/pdf"
            )

    # Pencarian Nama Siswa dan Kelas
    st.subheader("Pencarian")
    search_nama = st.text_input("Cari Nama Siswa")
    search_kelas = st.selectbox("Cari Kelas", ["Semua"] + ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])

    # Filter data berdasarkan pencarian
    filtered_data = st.session_state.pembayaran_spp
    if search_nama:
        filtered_data = filtered_data[filtered_data["Nama Siswa"].str.contains(search_nama, case=False)]
    if search_kelas != "Semua":
        filtered_data = filtered_data[filtered_data["Kelas"] == search_kelas]

    # Adding columns for Total Tagihan, SPP Terbayar, and Sisa Tagihan
    filtered_data['Total Tagihan SPP 1 Tahun (Rp)'] = filtered_data['Biaya SPP/Bulan'] * 12
    filtered_data['SPP yang Sudah Terbayar (Rp)'] = filtered_data.groupby(['Nama Siswa', 'Kelas'])['Jumlah Pembayaran'].transform('sum')
    filtered_data['Sisa Tagihan SPP (Rp)'] = filtered_data['Total Tagihan SPP 1 Tahun (Rp)'] - filtered_data['SPP yang Sudah Terbayar (Rp)']

    # Tampilkan data pembayaran SPP
    st.subheader("Data Pembayaran SPP")
    st.table(filtered_data)

    # Pilihan untuk memilih siswa dari daftar
    selected_siswa = st.selectbox("Pilih Siswa untuk Kwitansi", options=filtered_data["Nama Siswa"].unique())
    selected_kelas = st.selectbox("Pilih Kelas", options=filtered_data["Kelas"].unique())

    # Filter data untuk siswa dan kelas yang dipilih
    siswa_data = filtered_data[(filtered_data["Nama Siswa"] == selected_siswa) & (filtered_data["Kelas"] == selected_kelas)]

    # Tombol untuk download kwitansi siswa yang dipilih
    if not siswa_data.empty:
        siswa_row = siswa_data.iloc[0]  # Ambil baris pertama
        pdf = generate_receipt(siswa_row["Nama Siswa"], siswa_row["Kelas"], siswa_row["Bulan"], siswa_row["Jumlah Pembayaran"], siswa_row["Biaya SPP/Bulan"])
        
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        st.download_button(
            label="Download Kwitansi Siswa",
            data=pdf_output,
            file_name=f"Kwitansi_SPP_{siswa_row['Nama Siswa']}_{siswa_row['Bulan']}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Tidak ada data yang sesuai untuk kwitansi.")

elif selected == "Laporan Keuangan":
    st.title("Laporan Keuangan")
    st.write("Halaman untuk melihat laporan keuangan sekolah.")
    
    # Simulasi laporan keuangan dalam bentuk tabel
    data = {
        "Keterangan": ["SPP Kelas 1", "SPP Kelas 2", "Pembelian Buku"],
        "Debet (Rp)": [500000, 600000, 200000],
        "Kredit (Rp)": [0, 0, 100000],
        "Tanggal": [datetime(2024, 1, 10), datetime(2024, 1, 12), datetime(2024, 1, 15)],
    }
    laporan_keuangan = pd.DataFrame(data)
    st.table(laporan_keuangan)
    
    # Simulasi laporan keuangan dalam bentuk tabel
    data = {
        "Keterangan": ["SPP Kelas 1", "SPP Kelas 2", "Pembelian Buku"],
        "Debet (Rp)": [500000, 600000, 200000],
        "Kredit (Rp)": [0, 0, 100000],
        "Tanggal": [datetime(2024, 1, 10), datetime(2024, 2, 5), datetime(2024, 3, 20)]
    }
    df = pd.DataFrame(data)
    st.write(df)
    
    # Plot grafik debet dan kredit
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    df.set_index("Tanggal", inplace=True)
    df[["Debet (Rp)", "Kredit (Rp)"]].plot(kind="bar", stacked=True)
    st.pyplot(plt)

elif selected == "Pengelolaan Gaji Guru":
    st.title("Pengelolaan Gaji Guru")
    st.write("Halaman untuk mengelola pembayaran gaji guru.")
    
    # Simulasi input data gaji guru
    with st.form("gaji_form"):
        nama_guru = st.text_input("Nama Guru")
        bulan = st.selectbox("Bulan Gaji", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        gaji = st.number_input("Gaji Pokok (Rp)", min_value=0)
        tunjangan = st.number_input("Tunjangan (Rp)", min_value=0)
        
        # Tombol submit
        submitted_gaji = st.form_submit_button("Bayar Gaji")
        
        if submitted_gaji:
            save_gaji_guru(nama_guru, bulan, gaji, tunjangan)
            st.success(f"Gaji untuk {nama_guru} bulan {bulan} berhasil ditambahkan!")
