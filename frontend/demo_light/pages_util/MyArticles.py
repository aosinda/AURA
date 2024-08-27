import os
import demo_util
import streamlit as st
from demo_util import DemoFileIOHelper, DemoUIHelper
from streamlit_card import card

def my_articles_page():
    # Sync articles if not already in session state
    if "page2_user_articles_file_path_dict" not in st.session_state:
        local_dir = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR")
        os.makedirs(local_dir, exist_ok=True)
        st.session_state["page2_user_articles_file_path_dict"] = DemoFileIOHelper.read_structure_to_dict(local_dir)

    # Function to display article cards
    def article_card_setup(column_to_add, card_title, article_name):
        with column_to_add:
            cleaned_article_title = article_name.replace("_", " ")
            hasClicked = card(title=" / ".join(card_title),
                              text=cleaned_article_title,
                              image=DemoFileIOHelper.read_image_as_base64(
                                  os.path.join(demo_util.get_demo_dir(), "assets", "void.jpg")),
                              styles=DemoUIHelper.get_article_card_UI_style(boarder_color="#9AD8E1"))
            if hasClicked:
                st.session_state["page2_selected_my_article"] = article_name
                st.rerun()

    # Display article cards if no article is selected
    if "page2_selected_my_article" not in st.session_state:
        # Display article cards without pagination
        my_article_columns = st.columns(3)
        if len(st.session_state["page2_user_articles_file_path_dict"]) > 0:
            article_names = sorted(list(st.session_state["page2_user_articles_file_path_dict"].keys()))
            # Display all article cards
            my_article_count = 0
            for article_name in article_names:
                column_to_add = my_article_columns[my_article_count % 3]
                my_article_count += 1
                article_card_setup(column_to_add=column_to_add,
                                   card_title=["My Article"],
                                   article_name=article_name)
        else:
            # Show a card prompting to create the first article
            with my_article_columns[0]:
                hasClicked = card(title="Get started",
                                  text="Start your first research!",
                                  image=DemoFileIOHelper.read_image_as_base64(
                                      os.path.join(demo_util.get_demo_dir(), "assets", "void.jpg")),
                                  styles=DemoUIHelper.get_article_card_UI_style())
                if hasClicked:
                    st.session_state.selected_page = "Create New Article"
                    st.session_state["manual_selection_override"] = True
                    st.session_state["rerun_requested"] = True
                    st.rerun()

    # If an article is selected, display the article content
    else:
        selected_article_name = st.session_state["page2_selected_my_article"]
        selected_article_file_path_dict = st.session_state["page2_user_articles_file_path_dict"][selected_article_name]

        demo_util.display_article_page(selected_article_name=selected_article_name,
                                       selected_article_file_path_dict=selected_article_file_path_dict,
                                       show_title=True, show_main_article=True)


