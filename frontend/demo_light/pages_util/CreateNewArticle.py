import os
import time
import streamlit as st
import demo_util
from demo_util import DemoFileIOHelper, DemoTextProcessingHelper, DemoUIHelper


def create_new_article_page():
    demo_util.clear_other_page_session_state(page_index=3)

    if "page3_write_article_state" not in st.session_state:
        st.session_state["page3_write_article_state"] = "not started"

    # Add the instructional text right below the title
    st.markdown("""
    <h2 style='text-align: center;'>Create a New Research Report</h2>
    <p style='text-align: center; font-size: 16px; color: #555;'>
        Upload a file or paste your text (e.g., a press release or story draft).<br>
        AURA will suggest three potential newsworthy angles and provide a detailed research report.
    </p>
    """, unsafe_allow_html=True)

    if st.session_state["page3_write_article_state"] == "not started":
        _, search_form_column, _ = st.columns([2, 5, 2])
        with search_form_column:
            # File uploader and text input
            uploaded_file = st.file_uploader("Upload File", type=["txt", "pdf", "docx"], label_visibility="collapsed")
            st.session_state["page3_topic"] = st.text_input(label='page3_topic', label_visibility="collapsed", placeholder="Enter the topic here")

            if uploaded_file or st.session_state["page3_topic"].strip():
                st.session_state["page3_write_article_state"] = "initiated"
                
    if st.session_state["page3_write_article_state"] == "initiated":
        current_working_dir = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR")
        if not os.path.exists(current_working_dir):
            os.makedirs(current_working_dir)

        if "runner" not in st.session_state:
            demo_util.set_storm_runner()

        st.session_state["page3_current_working_dir"] = current_working_dir
        st.session_state["page3_write_article_state"] = "pre_writing"

    if st.session_state["page3_write_article_state"] == "pre_writing":
        status = st.status("I am brain**STORM**ing now to research the topic. (This may take 2-3 minutes.)")
        st_callback_handler = demo_util.StreamlitCallbackHandler(status)
        
        with status:
            # STORM main gen outline
            st.session_state["runner"].run(
                topic=st.session_state["page3_topic"],
                do_research=True,
                do_generate_outline=True,
                do_generate_article=False,
                do_polish_article=False,
                callback_handler=st_callback_handler
            )
            
            # Ensure topic name is cleaned and truncated properly
            if "page3_topic_name_cleaned" not in st.session_state or not st.session_state["page3_topic_name_cleaned"]:
                st.session_state["page3_topic_name_cleaned"] = st.session_state["page3_topic"].replace(' ', '_').replace('/', '_')

            conversation_log_path = os.path.join(st.session_state["page3_current_working_dir"],
                                                 st.session_state["page3_topic_name_cleaned"], "conversation_log.json")

            # Check if the file exists before reading it
            if os.path.exists(conversation_log_path):
                demo_util._display_persona_conversations(DemoFileIOHelper.read_json_file(conversation_log_path))
            else:
                st.error("Conversation log not found. Please check the topic and try again.")

            st.session_state["page3_write_article_state"] = "final_writing"
            status.update(label="brain**STORM**ing complete!", state="complete")

    if st.session_state["page3_write_article_state"] == "final_writing":
        # Polish final article
        with st.status("Now I will connect the information I found for your reference. (This may take 4-5 minutes.)") as status:
            st.session_state["runner"].run(topic=st.session_state["page3_topic"], do_research=False,
                                           do_generate_outline=False,
                                           do_generate_article=True, do_polish_article=True, remove_duplicate=False)
            # Finish the session
            st.session_state["runner"].post_run()

            # Update status bar
            st.session_state["page3_write_article_state"] = "prepare_to_show_result"
            status.update(label="Information synthesis complete!", state="complete")

    if st.session_state["page3_write_article_state"] == "prepare_to_show_result":
        _, show_result_col, _ = st.columns([4, 3, 4])
        with show_result_col:
            if st.button("Show Final Article"):
                st.session_state["page3_write_article_state"] = "completed"
                st.rerun()

    if st.session_state["page3_write_article_state"] == "completed":
        # Display polished article
        current_working_dir_paths = DemoFileIOHelper.read_structure_to_dict(st.session_state["page3_current_working_dir"])
        if st.session_state["page3_topic_name_cleaned"] in current_working_dir_paths:
            current_article_file_path_dict = current_working_dir_paths[st.session_state["page3_topic_name_cleaned"]]
            demo_util.display_article_page(selected_article_name=st.session_state["page3_topic_name_cleaned"],
                                           selected_article_file_path_dict=current_article_file_path_dict,
                                           show_title=True, show_main_article=True)
        else:
            st.error("Could not find the article. Please try again.")
