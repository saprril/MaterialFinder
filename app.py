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

st.title("🔍 SAP Smart Material Search (MM/SD)")
st.caption("Cari kode material SAP (MATNR) dari file CSV Master Data menggunakan AI.")

# Upload File CSV Master Data
uploaded_file = st.file_uploader("Upload File Master Data SAP (.csv)", type=["csv"])

if uploaded_file is not None:
    df_master = pd.read_csv(uploaded_file)
    st.success(f"Berhasil memuat {len(df_master)} data material!")
    
    with st.expander("Preview Data Master SAP"):
        st.dataframe(df_master.head(5))

    query_user = st.text_input("Ketik deskripsi barang yang dicari:", placeholder="misal: baut besi ukuran 8mm")

    if query_user:
        with st.spinner("AI sedang menganalisis & mencocokkan data..."):
            catalog_text = df_master.head(100).to_string(index=False)

            prompt = f"""
            Kamu adalah sistem pencarian cerdas untuk SAP Master Data (Module MM/SD).
            Berikut adalah Katalog Master Data SAP yang di-upload:
            {catalog_text}

            User mencari barang dengan bahasa awam: "{query_user}"

            Tugasmu:
            1. Analisis intent pencarian user.
            2. Cari maksimal 3 barang dari katalog yang paling cocok/relevan.
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
                    model='gemini-2.5-flash',
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
else:
    st.info("Silakan upload file CSV Master Data SAP kamu terlebih dahulu untuk mulai mencari.")
