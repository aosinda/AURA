import os
import streamlit as st
from pages_util import MyArticles, CreateNewArticle
import demo_util

# Determine the script directory and the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_root_dir = os.path.dirname(os.path.dirname(script_dir))


favicon_path = os.path.join(wiki_root_dir, "assets", "icon.png")

# Set page configuration at the top level
st.set_page_config(layout="wide", page_title="AURA", page_icon=favicon_path)


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
    st.markdown(
        """
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
        border: 2px solid #06908F !important; /* Force blue border */
        background-color: #06908F !important; /* Force blue background */
        color: white !important; /* Force white text */
        padding: 12px 20px;
        font-size: 18px;
        text-align: center;
        width: 100%;
        display: block;
        margin-left: 0;
        border-radius: 8px;
        transition: background-color 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        cursor: pointer;
        outline: none !important; /* Remove focus outline */
    }
    
    /* Hover effect */
    .stButton>button:hover {
        background-color: #08AFAF !important; /* Force darker blue on hover */
        color: yellow !important; /* Force white text on hover */
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }
    
    /* Active (clicked) state */
    .stButton>button:active {
        background-color: #056161 !important; /* Force even darker blue on click */
        color: yellow !important; /* Force white text on active */
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        transform: translateY(0);
        border: 2px solid #1f6aa6 !important; /* Force border to stay blue */
    }
    
    /* Focus state (after clicking) */
    .stButton>button:focus {
        background-color: #056161 !important; /* Force even darker blue on click */
        outline: none !important; /* Force no outline on focus */
        color: yellow !important; /* Force white text on active */
        border: 2px solid #1f6aa6 !important; /* Force border to stay blue */
    }


    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header for the app
    st.markdown(
        """
    <h1 style='
        font-size: 48px; 
        font-weight: bold; 
        color: #056161; 
        padding: 10px 0; 
        background-color: white; 
        text-align: center; 
        margin: 0;
    '>
        AURA
    </h1>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar layout
    with st.sidebar:
        create_article_icon = "➕"
        my_library_icon = "📄"
        demo_util.clear_other_page_session_state(page_index=3)
        st.session_state.update({"selected_page": "Create New Article"})

        # Update button labels
        if st.button(
            f"{create_article_icon} Create New Research Report",
            key="create_article_button",
            use_container_width=True,
        ):
            st.session_state.update({"selected_page": "Create New Article"})

        if st.button(
            f"{my_library_icon} My Library",
            key="my_articles_button",
            use_container_width=True,
        ):
            st.session_state.update({"selected_page": "My Articles"})

    # Main content display based on the selected page
    if st.session_state.get("selected_page") == "My Articles":
        # print("selected_page: My Articles")
        demo_util.clear_other_page_session_state(page_index=1)
        MyArticles.my_articles_page()
    elif st.session_state.get("selected_page") == "Show Article":
        # print("selected_page: Show Article")
        demo_util.clear_other_page_session_state(page_index=2)
        MyArticles.my_articles_page()
    elif st.session_state.get("selected_page") == "Create New Article":
        # print("selected_page: Create New Article")
        demo_util.clear_other_page_session_state(page_index=3)
        CreateNewArticle.create_new_article_page()


if __name__ == "__main__":
    main()
