import streamlit as st
import os
import shutil
import time
from dotenv import load_dotenv
from extractor import extract_from_pdf, get_thermal_images_only
from report_generator import generate_ddr
from docx_builder import build_docx

load_dotenv(override=True)

st.set_page_config(
    page_title="DDR Report Generator",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0a0a0a;
        background-image: 
            linear-gradient(rgba(232,122,30,0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(232,122,30,0.05) 1px, transparent 1px),
            linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        background-size: 40px 40px, 40px 40px, 100% 100%;
        background-attachment: fixed;
    }
    .stButton>button {
        background-color: #E87A1E !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        transition: 0.3s;
        font-weight: bold;
    }
    .stButton>button:hover {
        opacity: 0.85;
        box-shadow: 0 4px 8px rgba(232,122,30,0.3) !important;
    }
    div[data-testid="stFileUploader"] {
        padding: 1rem;
        border-radius: 10px;
        transition: 0.3s;
    }
    div[data-testid="stFileUploader"]:hover {
        border: 2px dashed #E87A1E !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
  background: linear-gradient(135deg, #1a1a1a, #2d1a00);
  border: 2px solid #E87A1E;
  border-radius: 16px;
  padding: 40px;
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
">
  <div style="font-size:48px">🏗️</div>
  <h1 style="color:white; font-size:2.5rem; margin:0">DDR Report Generator</h1>
  <p style="color:#E87A1E; font-size:1.1rem; margin-top:8px">
    UrbanRoof — AI Powered Inspection Analysis
  </p>
  <div style="
    position:absolute; right:40px; top:50%; transform:translateY(-50%);
    font-size:80px; opacity:0.15;
  ">🏢🔍🌡️</div>
</div>
""", unsafe_allow_html=True)

stat1, stat2 = st.columns(2)
card_style = "background-color: #1a1a1a; border-left: 4px solid #E87A1E; padding: 16px; border-radius: 8px; color: white; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"

with stat1:
    st.markdown(f'<div style="{card_style}">🏠 Any Property Type</div>', unsafe_allow_html=True)
with stat2:
    st.markdown(f'<div style="{card_style}">📄 2 PDFs → 1 Report</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; color:#E87A1E; font-size:32px; letter-spacing:8px; margin:20px 0; opacity:0.6">
🏢🏗️🏠🏢🏗️🏠🏢🏗️🏠
</div>
""", unsafe_allow_html=True)

st.markdown("""
<h3 style="color:white; text-align:center; text-shadow: 0 0 20px rgba(232,122,30,0.5);">
  Upload Your Reports
</h3>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    inspection_file = st.file_uploader(
        "📋 Inspection Report PDF",
        type=["pdf"]
    )
with col2:
    thermal_file = st.file_uploader(
        "🌡️ Thermal Report PDF", 
        type=["pdf"]
    )

if inspection_file:
    st.success(f"✅ Inspection Report: {inspection_file.name}")
if thermal_file:
    st.success(f"✅ Thermal Report: {thermal_file.name}")

generate_btn = st.button(
    "🚀 Generate DDR Report",
    disabled=not (inspection_file and thermal_file),
    use_container_width=True
)

if generate_btn:
    
    if not os.environ.get("GROQ_API_KEY"):
        st.warning("Please ensure GROQ_API_KEY is set in your .env file.")
        st.stop()
    if not inspection_file or not thermal_file:
        st.warning("Please upload both PDF files")
        st.stop()
        
    progress_bar = st.progress(0)
    
    # Setup temp directories
    os.makedirs("temp_imgs", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Save uploaded files
    with open("temp_inspection.pdf", "wb") as f:
        f.write(inspection_file.read())
    with open("temp_thermal.pdf", "wb") as f:
        f.write(thermal_file.read())
    
    # STEP 1: Extract
    with st.spinner("📄 Step 1/3 — Extracting text and images from PDFs..."):
        try:
            insp_text, insp_images = extract_from_pdf(
                "temp_inspection.pdf", "temp_imgs", "inspection")
            therm_text, therm_images = extract_from_pdf(
                "temp_thermal.pdf", "temp_imgs", "thermal")
            
            all_images = insp_images + therm_images
            thermal_maps, thermal_real_photos = get_thermal_images_only(therm_images)
            
            st.info(f"""
            📊 Extraction complete:
            - Inspection: {len(insp_images)} images, {len(insp_text)} characters
            - Thermal: {len(therm_images)} images ({len(thermal_maps)} thermal maps, 
              {len(thermal_real_photos)} reference photos)
            """)
            
            if len(insp_text) < 100:
                st.error("Could not extract text from Inspection PDF. Please check the file.")
                st.stop()
                
        except Exception as e:
            st.error(f"PDF extraction failed: {e}")
            st.stop()
            
        progress_bar.progress(33)
    
    # STEP 2: AI Analysis
    with st.spinner("🤖 Step 2/3 — AI is analyzing inspection data..."):
        try:
            ddr_data = generate_ddr(insp_text, therm_text)
            
            if ddr_data is None:
                st.error("AI analysis failed. Check your Groq API key and try again.")
                st.stop()
            
            areas_found = len(ddr_data.get("area_wise_observations", []))
            st.info(f"🤖 AI found {areas_found} impacted areas")
            
        except Exception as e:
            st.error(f"AI analysis failed: {e}")
            st.stop()
            
        progress_bar.progress(66)
    
    # STEP 3: Build Report
    with st.spinner("📝 Step 3/3 — Building professional Word report..."):
        try:
            output_path = "output/DDR_Report.docx"
            build_docx(ddr_data, all_images, thermal_maps, 
                      thermal_real_photos, output_path)
            progress_bar.progress(100)
            st.success("✅ DDR Report generated successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()
    
    # Download Button
    st.markdown("---")
    with open(output_path, "rb") as f:
        st.download_button(
            label="📥 Download DDR Report (.docx)",
            data=f,
            file_name="DDR_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    
    # JSON Preview
    with st.expander("👁️ Preview AI Analysis (JSON)"):
        st.json(ddr_data)
    
    # Image Preview
    with st.expander(f"🖼️ Preview Extracted Images ({len(all_images)} total)"):
        cols = st.columns(4)
        for idx, img in enumerate(all_images[:12]):
            with cols[idx % 4]:
                if os.path.exists(img["path"]):
                    st.image(img["path"], 
                            caption=f"{img['source']} p{img['page']}", 
                            use_column_width=True)

# Footer
st.markdown("""
<div style="text-align:center; padding:20px; color:#666; border-top:1px solid #333; margin-top:40px">
  <span style="color:#E87A1E">⬛ UrbanRoof</span> · 
  Powered by Groq AI · Built for smarter inspections
</div>
""", unsafe_allow_html=True)
