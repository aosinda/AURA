import os
import demo_util
import streamlit as st
from demo_util import DemoFileIOHelper


def my_articles_page():
    # Add custom CSS for centering content
    st.markdown("""
    <style>
    .centered-container {
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sync articles if not already in session state
    if "page2_user_articles_file_path_dict" not in st.session_state:
        # Define the base directory for articles
        local_dir = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR")
        os.makedirs(local_dir, exist_ok=True)
        # Read the directory structure into session state
        st.session_state["page2_user_articles_file_path_dict"] = DemoFileIOHelper.read_structure_to_dict(local_dir)

    # Center the main content container
    with st.container():
        # st.markdown("<div class='centered-container'>", unsafe_allow_html=True)

        # Display article previews if no article is selected
        if "page2_selected_my_article" not in st.session_state:
            # st.markdown("### My Articles")  # Header for the list of articles
            st.markdown(
                """<h2 style='text-align: center; color: #06908F;'>My Research Reports</h2>""",
                unsafe_allow_html=True,
            )
            st.write("---")

            if len(st.session_state["page2_user_articles_file_path_dict"]) > 0:
                article_names = sorted(list(st.session_state["page2_user_articles_file_path_dict"].keys()))

                # Loop through each article (i.e., folder)
                for article_name in article_names:
                    # Clean up the article name for display
                    cleaned_article_title = article_name.replace("_", " ").title()
                    # print("cleaned_article_title", cleaned_article_title)
                    cleaned_article_title = cleaned_article_title.split("\n")[0]

                    # Get the path to the article folder
                    article_folder_path = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR", article_name)

                    # Define the potential paths for the polished and raw article text files
                    polished_article_path = os.path.join(article_folder_path, "storm_gen_article_polished.txt")
                    raw_article_path = os.path.join(article_folder_path, "storm_gen_article.txt")

                    # Attempt to load the content of the polished article or fall back to the raw article
                    if os.path.exists(polished_article_path):
                        with open(polished_article_path, "r") as file:
                            article_content = file.read()
                    elif os.path.exists(raw_article_path):
                        with open(raw_article_path, "r") as file:
                            article_content = file.read()
                    else:
                        article_content = "No preview available..."

                    # Remove the `# summary` line if present
                    article_content_lines = article_content.splitlines()
                    article_content = "\n".join([line for line in article_content_lines if line.strip() != "# summary"])

                    # Generate a preview of the first 100 characters
                    preview_text = article_content[:300] + "..." if article_content != "No preview available..." else article_content

                    # Display the article as a clickable header
                    if st.button(cleaned_article_title):
                        st.session_state.update({"selected_page": "Show Article"})
                        st.session_state["page2_selected_my_article"] = article_name
                        st.rerun()

                    # Show a short preview of the article content as regular text
                    st.write(preview_text)

                    # Add a horizontal line separator between articles
                    st.write("---")
            else:
                # No articles available, prompt to create one
                st.info("No articles found. Start your first research!")

        # If an article is selected, display the full article content
        else:
            selected_article_name = st.session_state["page2_selected_my_article"]
            selected_article_file_path_dict = st.session_state["page2_user_articles_file_path_dict"][selected_article_name]
            selected_article_name = selected_article_name.split("\n")[0]

            # Display the full content of the selected article
            demo_util.display_article_page(
                selected_article_name=selected_article_name,
                selected_article_file_path_dict=selected_article_file_path_dict,
                show_title=True, show_main_article=True
            )

        # st.markdown("</div>", unsafe_allow_html=True)
