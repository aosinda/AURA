import os
import demo_util
import streamlit as st
from demo_util import DemoFileIOHelper, DemoUIHelper
from streamlit_card import card
import re

def sanitize_text(text):
    """
    Remove Markdown formatting like #, **, and other special characters from the text.
    """
    # Remove Markdown headers (e.g., #, ##)
    text = re.sub(r'#', '', text)
    # Remove bold or italic (e.g., **text** or *text*)
    text = re.sub(r'\*\*|\*', '', text)
    return text.strip()

# set page config and display title
def my_articles_page():
    # Centered title with added spacing below
    st.markdown(
        "<h3 style='text-align: center; margin-bottom: 40px;'>My Library</h3>",
        unsafe_allow_html=True
    )

    with st.sidebar:
        _, return_button_col = st.columns([2, 5])
        with return_button_col:
            if st.button("Select another article", disabled="page2_selected_my_article" not in st.session_state):
                if "page2_selected_my_article" in st.session_state:
                    del st.session_state["page2_selected_my_article"]
                st.rerun()

    # sync my articles
    if "page2_user_articles_file_path_dict" not in st.session_state:
        local_dir = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR")
        os.makedirs(local_dir, exist_ok=True)
        st.session_state["page2_user_articles_file_path_dict"] = DemoFileIOHelper.read_structure_to_dict(local_dir)

    # if no feature demo selected, display all featured articles as info cards
    def article_card_setup(article_name):
        # Capitalize only the first letter of the article title
        cleaned_article_title = article_name.replace("_", " ").capitalize()

        # Define the path to the polished article
        article_path = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR", article_name, "storm_gen_article_polished.txt")
        
        # Read the content of the polished article
        if os.path.exists(article_path):
            with open(article_path, 'r') as file:
                article_content = file.read()

            # Extract a snippet (first 200 characters or adjust as needed)
            sanitized_snippet = sanitize_text(article_content[:200]) + "..."
        else:
            sanitized_snippet = "No content available."

        # Combine title and snippet without bold
        card_text = f"{cleaned_article_title}\n\n{sanitized_snippet}"

        # Create the card with the title and sanitized snippet text
        hasClicked = card(
            title="",  # Title is part of the text
            text=card_text,
            image=DemoFileIOHelper.read_image_as_base64(
                os.path.join(demo_util.get_demo_dir(), "assets", "void.jpg")),
            styles=DemoUIHelper.get_article_card_UI_style(boarder_color="#9AD8E1")
        )
        
        if hasClicked:
            st.session_state["page2_selected_my_article"] = article_name
            st.rerun()

    if "page2_selected_my_article" not in st.session_state:
        # display article cards
        if len(st.session_state["page2_user_articles_file_path_dict"]) > 0:
            # get article names
            article_names = sorted(list(st.session_state["page2_user_articles_file_path_dict"].keys()))
            
            # Show all articles without pagination
            for article_name in article_names:
                article_card_setup(article_name=article_name)
        else:
            hasClicked = card(title="Get started",
                              text="Start your first research!",
                              image=DemoFileIOHelper.read_image_as_base64(
                                  os.path.join(demo_util.get_demo_dir(), "assets", "void.jpg")),
                              styles=DemoUIHelper.get_article_card_UI_style())
            if hasClicked:
                st.session_state.selected_page = 1
                st.session_state["manual_selection_override"] = True
                st.session_state["rerun_requested"] = True
                st.rerun()
    else:
        selected_article_name = st.session_state["page2_selected_my_article"]
        selected_article_file_path_dict = st.session_state["page2_user_articles_file_path_dict"][selected_article_name]

        demo_util.display_article_page(selected_article_name=selected_article_name,
                                       selected_article_file_path_dict=selected_article_file_path_dict,
                                       show_title=True, show_main_article=True)
