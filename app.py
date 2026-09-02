import streamlit as st
import pandas as pd
from google import genai
import json

# Mengambil API Key dari Streamlit Secrets / Environment
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Gemini belum diatur di Streamlit Secrets!")
    st.stop()

client = genai.Client(api_key=api_key)

st.set_page_config(page_title="SAP Smart Material Search", page_icon="🔍")

st.title("🔍 SAP Smart Material Search (MM60 Excel)")
st.caption("Cari kode material SAP (MATNR) dari file Excel hasil export T-Code MM60.")

# Upload File Excel Master Data MM60
uploaded_file = st.file_uploader(
    "Upload File Excel Export MM60 (.xlsx / .xls)", 
    type=["xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        # Membaca file Excel
        # converters={'Material': str} memastikan leading zero (misal 00000010002) tidak hilang
        df_master = pd.read_excel(uploaded_file, dtype=str)
        
        # Bersihkan spasi berlebih di nama kolom
        df_master.columns = df_master.columns.str.strip()

        st.success(f"Berhasil memuat {len(df_master)} data material dari Excel!")
        
        with st.expander("Preview Data"):
            st.dataframe(df_master.head(5))

        query_user = st.text_input("Ketik deskripsi barang yang dicari:", placeholder="misal: asam klorida")

        if query_user:
            with st.spinner("AI sedang menganalisis & mencocokkan data..."):
                # Mengambil 100 baris pertama untuk efisiensi context window
                catalog_data = df_master.head(100).to_dict(orient='records')
                catalog_text = json.dumps(catalog_data, ensure_ascii=False)

                prompt = f"""
                Kamu adalah sistem pencarian cerdas untuk SAP Master Data (Module MM/SD).
                Berikut adalah Katalog Master Data SAP hasil export MM60:
                {catalog_text}

                User mencari barang dengan bahasa awam: "{query_user}"

                Tugasmu:
                1. Analisis intent pencarian user.
                2. Cari maksimal 3 barang dari katalog yang paling cocok/relevan (perhatikan kolom Material dan Material Description).
                3. Kembalikan hasilnya HANYA dalam format JSON array berisi object dengan key:
                   - "matnr": Kode Material SAP
                   - "maktx": Deskripsi Material di SAP
                   - "confidence": Persentase relevansi (contoh: "95%")
                   - "reason": Alasan singkat kenapa barang ini cocok

                Contoh format JSON:
                [
                  {{"matnr": "10002931", "maktx": "BT-BJ-M8-100", "confidence": "90%", "reason": "M8 sesuai dengan ukuran 8mm"}}
                ]
                """

                try:
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                    )

                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    results = json.loads(clean_json)

                    st.subheader("Rekomendasi Kode Material SAP:")
                    for item in results:
                        with st.container(border=True):
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.header(f"`{item['matnr']}`")
                                st.caption(f"Relevansi: {item['confidence']}")
                            with col2:
                                st.subheader(item['maktx'])
                                st.write(f"💡 *{item['reason']}*")
                except Exception as e:
                    st.error(f"Gagal memproses AI: {e}")

    except Exception as e:
        st.error(f"Gagal membaca file Excel: {e}")
else:
    st.info("Silakan upload file Excel (.xlsx / .xls) hasil export MM60 kamu terlebih dahulu.")