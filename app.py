import streamlit as st
import requests
import os

# Backend API URL
BASE_URL = "http://127.0.0.1:8000"  # Change this if using Render or another server

st.title("📰 TOI Newspaper Downloader & Extractor")

# User inputs city name
city = st.text_input("Enter City Name", "")

# Section to Download PDF
st.subheader("📥 Download Newspaper PDF")

if st.button("Download PDF"):
    if city:
        response = requests.get(f"{BASE_URL}/download-pdf", params={"city": city})
        if response.status_code == 200:
            pdf_path = response.json().get("pdf_path")
            st.success("✅ PDF downloaded successfully!")

            # Display PDF in Streamlit
            if pdf_path and os.path.exists(pdf_path):
                st.subheader("📄 Preview PDF")
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(label="⬇️ Download PDF", 
                                       data=pdf_file, 
                                       file_name=os.path.basename(pdf_path), 
                                       mime="application/pdf")
                st.markdown(f'<iframe src="{pdf_path}" width="700" height="500"></iframe>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ PDF file not found on the server.")

        else:
            st.error(f"❌ {response.json()['detail']}")
    else:
        st.warning("⚠️ Please enter a city name.")

# Section to Extract Text & Download Excel
st.subheader("🔍 Extract Text & Download Excel")

if st.button("Extract Text & Download Excel"):
    if city:
        response = requests.get(f"{BASE_URL}/extract-text-excel", params={"city": city})
        if response.status_code == 200:
            excel_url = response.url
            st.success("✅ Extraction complete! Download the Excel file below:")
            st.markdown(f"[📥 Download Extracted Excel]({excel_url})")
        else:
            st.error(f"❌ {response.json()['detail']}")
    else:
        st.warning("⚠️ Please enter a city name.")
