import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import os
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

# Function to get a SQLite connection
def get_connection():
    return sqlite3.connect('database_sekolah.db')

# Create tables if they do not exist
def initialize_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS pembayaran_spp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_siswa TEXT,
                kelas TEXT,
                bulan TEXT,
                jumlah_pembayaran INTEGER,
                biaya_spp INTEGER,
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

# Initialize in-memory session data
def init_session_state():
    if "pembayaran_spp" not in st.session_state:
        st.session_state.pembayaran_spp = pd.DataFrame(columns=["Nama Siswa", "Kelas", "Bulan", "Jumlah Pembayaran", "Biaya SPP/Bulan"])

# Function to save SPP payment to SQLite and CSV
def save_pembayaran_spp(nama_siswa, kelas, bulan, jumlah, biaya_spp):
    tanggal = datetime.now().strftime('%Y-%m-%d')
    new_row = pd.DataFrame({
        "Nama Siswa": [nama_siswa],
        "Kelas": [kelas],
        "Bulan": [bulan],
        "Jumlah Pembayaran": [jumlah],
        "Biaya SPP/Bulan": [biaya_spp]
    })
    st.session_state.pembayaran_spp = pd.concat([st.session_state.pembayaran_spp, new_row], ignore_index=True)
    st.session_state.pembayaran_spp.to_csv('pembayaran_spp.csv', index=False)
    
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO pembayaran_spp (nama_siswa, kelas, bulan, jumlah_pembayaran, biaya_spp, tanggal) VALUES (?, ?, ?, ?, ?, ?)", 
                  (nama_siswa, kelas, bulan, jumlah, biaya_spp, tanggal))
        conn.commit()

# Function to save teacher salary to SQLite and CSV
def save_gaji_guru(nama_guru, bulan, gaji, tunjangan):
    tanggal = datetime.now().strftime('%Y-%m-%d')
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO gaji_guru (nama_guru, bulan, gaji, tunjangan, tanggal) VALUES (?, ?, ?, ?, ?)',
                  (nama_guru, bulan, gaji, tunjangan, tanggal))
        conn.commit()
    
    df_gaji = pd.DataFrame([{
        'Nama Guru': nama_guru,
        'Bulan': bulan,
        'Gaji Pokok': gaji,
        'Tunjangan': tunjangan,
        'Tanggal': tanggal
    }])
    df_gaji.to_csv('gaji_guru.csv', index=False)

# Function to generate payment receipt as a PDF
def generate_receipt(nama_siswa, kelas, bulan, jumlah, biaya_spp, filename):
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
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    st.download_button(
        label="Download Kwitansi",
        data=pdf_output,
        file_name=f"{filename}.pdf",
        mime="application/pdf"
    )

# Setup for sidebar menu
def setup_sidebar():
    with st.sidebar:
        return option_menu(
            menu_title="Main Menu",
            options=["Pembayaran SPP", "Laporan Keuangan", "Pengelolaan Gaji Guru"],
            icons=["cash-stack", "bar-chart", "person-badge"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": "#f0f2f6"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#4CAF50"},
            }
        )

def main():
    initialize_db()
    init_session_state()
    
    selected = setup_sidebar()

    if selected == "Pembayaran SPP":
        st.title("Pembayaran SPP")
        st.write("Halaman untuk pembayaran SPP siswa.")

        with st.form("pembayaran_form"):
            nama_siswa = st.text_input("Nama Siswa")
            kelas = st.selectbox("Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])
            bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            biaya_spp = st.number_input("Biaya SPP per Bulan (Rp)", min_value=0)
            jumlah = st.number_input("Jumlah Pembayaran (Rp)", min_value=0)

            submitted = st.form_submit_button("Bayar")

            if submitted:
                if not nama_siswa or not kelas or not jumlah:
                    st.warning("Semua field harus diisi!")
                else:
                    save_pembayaran_spp(nama_siswa, kelas, bulan, jumlah, biaya_spp)
                    st.success(f"Pembayaran SPP untuk {nama_siswa} berhasil ditambahkan!")
                    generate_receipt(nama_siswa, kelas, bulan, jumlah, biaya_spp, f"Kwitansi_SPP_{nama_siswa}_{bulan}")

        st.subheader("Pencarian")
        search_nama = st.text_input("Cari Nama Siswa")
        search_kelas = st.selectbox("Cari Kelas", ["Semua"] + ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])

        filtered_data = st.session_state.pembayaran_spp
        if search_nama:
            filtered_data = filtered_data[filtered_data["Nama Siswa"].str.contains(search_nama, case=False)]
        if search_kelas != "Semua":
            filtered_data = filtered_data[filtered_data["Kelas"] == search_kelas]

        filtered_data['Total Tagihan SPP 1 Tahun (Rp)'] = filtered_data['Biaya SPP/Bulan'] * 12
        filtered_data['SPP yang Sudah Terbayar (Rp)'] = filtered_data.groupby(['Nama Siswa', 'Kelas'])['Jumlah Pembayaran'].transform('sum')
        filtered_data['Sisa Tagihan SPP (Rp)'] = filtered_data['Total Tagihan SPP 1 Tahun (Rp)'] - filtered_data['SPP yang Sudah Terbayar (Rp)']

        st.subheader("Data Pembayaran SPP")
        st.table(filtered_data)

        selected_siswa = st.selectbox("Pilih Siswa untuk Kwitansi", options=filtered_data["Nama Siswa"].unique())
        selected_kelas = st.selectbox("Pilih Kelas", options=filtered_data["Kelas"].unique())

        siswa_data = filtered_data[(filtered_data["Nama Siswa"] == selected_siswa) & (filtered_data["Kelas"] == selected_kelas)]

        if not siswa_data.empty:
            siswa_row = siswa_data.iloc[0]
            generate_receipt(siswa_row["Nama Siswa"], siswa_row["Kelas"], siswa_row["Bulan"], siswa_row["Jumlah Pembayaran"], siswa_row["Biaya SPP/Bulan"], f"Kwitansi_SPP_{siswa_row['Nama Siswa']}_{siswa_row['Bulan']}")
        else:
            st.warning("Tidak ada data yang sesuai untuk kwitansi.")

    elif selected == "Laporan Keuangan":
        st.title("Laporan Keuangan")
        st.write("Halaman untuk melihat laporan keuangan sekolah.")

        data = {
            "Keterangan": ["SPP Kelas 1", "SPP Kelas 2", "Pembelian Buku"],
            "Debet (Rp)": [1000000, 1200000, 500000],
            "Kredit (Rp)": [0, 0, 0]
        }
        df = pd.DataFrame(data)
        st.table(df)

        st.subheader("Grafik Laporan Keuangan")
        plt.figure(figsize=(10, 6))
        plt.bar(df["Keterangan"], df["Debet (Rp)"], color='blue', label='Debet')
        plt.bar(df["Keterangan"], df["Kredit (Rp)"], color='red', label='Kredit', bottom=df["Debet (Rp)"])
        plt.xlabel('Keterangan')
        plt.ylabel('Jumlah (Rp)')
        plt.title('Laporan Keuangan')
        plt.legend()
        st.pyplot(plt)

    elif selected == "Pengelolaan Gaji Guru":
        st.title("Pengelolaan Gaji Guru")
        st.write("Halaman untuk mengelola gaji guru.")

        with st.form("gaji_form"):
            nama_guru = st.text_input("Nama Guru")
            bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            gaji = st.number_input("Gaji Pokok (Rp)", min_value=0)
            tunjangan = st.number_input("Tunjangan (Rp)", min_value=0)

            submitted = st.form_submit_button("Simpan Gaji")

            if submitted:
                if not nama_guru or not bulan or not gaji:
                    st.warning("Semua field harus diisi!")
                else:
                    save_gaji_guru(nama_guru, bulan, gaji, tunjangan)
                    st.success(f"Gaji untuk {nama_guru} berhasil disimpan!")

        st.subheader("Data Gaji Guru")
        df_gaji = pd.read_csv('gaji_guru.csv')
        st.table(df_gaji)

if __name__ == "__main__":
    main()
