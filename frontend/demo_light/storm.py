import os
import streamlit as st
from pages_util import MyArticles, CreateNewArticle
import demo_util

# Determine the script directory and the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_root_dir = os.path.dirname(os.path.dirname(script_dir))

# Set page configuration at the top level
st.set_page_config(layout='wide')

def main():
    global database
    if "first_run" not in st.session_state:
        st.session_state["first_run"] = True

    if st.session_state["first_run"]:
        for key, value in st.secrets.items():
            if type(value) == str:
                os.environ[key] = value
    
     # Initialize session state variables
    if "selected_article_index" not in st.session_state:
        st.session_state["selected_article_index"] = 0
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = 0
    if st.session_state.get("rerun_requested", False):
        st.session_state["rerun_requested"] = False
        st.rerun()

    # Custom CSS to adjust sidebar, buttons, and main content
    st.markdown("""
    <style>
    /* Change sidebar background color */
    [data-testid="stSidebar"] {
        background-color: #f5f5f5;
    }

    /* Change the close button (X) to '<' */
    [data-testid="stSidebarClose"]::before {
        content: '<';
        font-size: 22px;
    }

    /* Move AURA title up by reducing top padding of main container */
    .block-container {
        padding-top: 1rem;  /* Adjust this value as needed */
    }

    /* Sidebar button styling */
    .sidebar-button {
        border: none;
        background-color: transparent;
        font-size: 18px;
        font-weight: normal;
        color: black;
        text-align: left;
        padding: 10px;
        margin: 0;
        display: block;
        width: 100%;
    }

    .sidebar-button:hover {
        background-color: #f0f0f0;
        cursor: pointer;
    }

    /* Remove the button border and shadow */
    .stButton>button {
        border: none;
        background-color: transparent;
        box-shadow: none;
        padding: 10px;
        font-size: 18px;
        color: black;
        text-align: left; /* Aligns the button text to the left */
        width: 100%;
        display: block; /* Ensures buttons take up full width */
        margin-left: 0; /* Removes any auto centering */
    }

    /* Remove background color on hover */
    .stButton>button:hover {
        background-color: #f0f0f0;
        cursor: pointer;
    }

    </style>
    """, unsafe_allow_html=True)

    # Header for the app
    st.markdown("""
    <h1 style='font-size: 24px; font-weight: bold; color: #3c6e71; padding: 10px 0; background-color: white; text-align: left; margin: 0;'>
        AURA
    </h1>
    """, unsafe_allow_html=True)

    # Sidebar layout
    with st.sidebar:
        create_article_icon = "➕"
        my_library_icon = "📄"
        
        # Update button labels
        if st.button(f"{create_article_icon} Create New Research Report", key="create_article_button", use_container_width=True):
            st.session_state.update({"selected_page": "Create New Article"})
        
        if st.button(f"{my_library_icon} My Library", key="my_articles_button", use_container_width=True):
            st.session_state.update({"selected_page": "My Articles"})

    # Main content display based on the selected page
    if st.session_state.get("selected_page") == "My Articles":
        demo_util.clear_other_page_session_state(page_index=2)
        MyArticles.my_articles_page()

    elif st.session_state.get("selected_page") == "Create New Article":
        demo_util.clear_other_page_session_state(page_index=3)
        CreateNewArticle.create_new_article_page()

if __name__ == "__main__":
    main()
