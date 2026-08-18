import streamlit as st

from utils.helpers import apply_custom_css, render_sidebar

st.set_page_config(
    page_title="MORQEVA | Dark Vault",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()
st.logo("assets/morqeva_mark.svg", size="large", icon_image="assets/morqeva_mark.svg")
render_sidebar()

pages = {
    "Control Center": [
        st.Page("pages/1_Dashboard.py", title="Executive Dashboard", icon="📊", default=True),
        st.Page("pages/2_Create_Story.py", title="Create Story", icon="✨"),
        st.Page("pages/3_Story_Library.py", title="Story Library", icon="📚"),
    ],
    "Production": [
        st.Page("pages/4_Production.py", title="Production", icon="🎬"),
        st.Page("pages/5_Quality_Control.py", title="Quality Control", icon="✅"),
        st.Page("pages/6_Distribution.py", title="Distribution", icon="🚀"),
    ],
    "Intelligence": [
        st.Page("pages/7_Analytics.py", title="Analytics", icon="📈"),
        st.Page("pages/8_Blueprints.py", title="Blueprints", icon="🧩"),
        st.Page("pages/9_Settings.py", title="Settings", icon="⚙️"),
    ],
}

st.navigation(pages).run()
