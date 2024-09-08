import os
import traceback
import streamlit as st
import demo_util
from demo_util import DemoFileIOHelper
from input_processing import extract_text
from storyline import generate_storyline

def handle_uploaded_file(uploaded_file):
    file_extension = uploaded_file.name.split('.')[-1].lower()
    file_path = f"/tmp/{uploaded_file.name}"
    
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        docs = extract_text(file_path, file_extension)
        return docs
    except Exception as e:
        st.error(f"An error occurred while handling the file: {e}")
        traceback.print_exc()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return None

def display_storylines(storylines):
    st.markdown("<p style='font-size: 18px; font-weight: bold;'>Here are three possible storylines. Please chose one, so AURA can make a thorough research</p>", unsafe_allow_html=True)
    for idx, storyline in enumerate([storylines.storyline_1, storylines.storyline_2, storylines.storyline_3], 1):
        st.write(f"**Storyline {idx}:**")
        st.write(f"- **Option:** {storyline.storyline_option}")
        st.write(f"- **Elaboration:** {storyline.elaboration}")

        if st.button(f"Select Storyline {idx}", key=f"select_storyline_{idx}"):
            st.session_state["selected_storyline_option"] = storyline.storyline_option
            st.session_state["selected_storyline_elaboration"] = storyline.elaboration
            st.session_state["page3_write_article_state"] = "storyline_selected"
            st.experimental_rerun()

def create_new_article_page():
    css = '''
    <style>
        [data-testid='stFileUploader'] {
            width: max-content;
        }
        [data-testid='stFileUploader'] section {
            padding: 0;
            float: right;
        }
        [data-testid='stFileUploader'] section > input + div {
            display: none;
        }
        [data-testid='stFileUploader'] section + div {
            float: right;
            padding-top: 0;
        }
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)

    demo_util.clear_other_page_session_state(page_index=3)

    if "page3_write_article_state" not in st.session_state:
        st.session_state["page3_write_article_state"] = "not started"

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
            uploaded_file = st.file_uploader("Upload File", type=["txt", "pdf", "docx"], key="unique_key_for_file_uploader", label_visibility="collapsed")
            st.session_state["page3_topic"] = st.text_input(label='page3_topic', label_visibility="collapsed", placeholder="Enter the topic here")

            if uploaded_file or st.session_state["page3_topic"].strip():
                st.session_state["uploaded_file"] = uploaded_file  # Store the file in session state
                st.session_state["page3_write_article_state"] = "initiated"

    if st.session_state["page3_write_article_state"] == "initiated":
        uploaded_file = st.session_state.get("uploaded_file")  # Retrieve the file from session state

        if uploaded_file is not None:
            docs = handle_uploaded_file(uploaded_file)
            if docs:
                user_input_text = " ".join([doc.page_content for doc in docs])

                st.write("Generating Storylines...")
                try:
                    storylines = generate_storyline(user_input_text)
                    display_storylines(storylines)
                except Exception as e:
                    st.error(f"An error occurred while generating storylines: {e}")
                    traceback.print_exc()
            else:
                st.write("No text could be extracted from the document.")

    if st.session_state.get("page3_write_article_state") == "storyline_selected":
        st.text_input(label='Topic Option', value=st.session_state["selected_storyline_option"], label_visibility="collapsed", placeholder="Enter the topic here")
        st.text_input(label='Storyline Elaboration', value=st.session_state["selected_storyline_elaboration"], label_visibility="collapsed", placeholder="Enter the elaboration here")

        if st.button("Proceed with this Storyline"):
            st.session_state["page3_write_article_state"] = "pre_writing"
            st.experimental_rerun()

    if st.session_state.get("selected_storyline_option", "").strip() and st.session_state.get("page3_write_article_state") == "pre_writing":
        current_working_dir = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR")
        if not os.path.exists(current_working_dir):
            os.makedirs(current_working_dir)

        if "runner" not in st.session_state:
            demo_util.set_storm_runner()

        st.session_state["page3_current_working_dir"] = current_working_dir
        status = st.status("Brainstorming topic... (This may take 2-3 minutes.)")
        st_callback_handler = demo_util.StreamlitCallbackHandler(status)

        with status:
            try:
                st.session_state["runner"].run(
                    topic=st.session_state["page3_topic"],
                    do_research=True,
                    do_generate_outline=True,
                    do_generate_article=False,
                    do_polish_article=False,
                    callback_handler=st_callback_handler
                )

                if "page3_topic_name_cleaned" not in st.session_state:
                    st.session_state["page3_topic_name_cleaned"] = st.session_state["page3_topic"].replace(' ', '_').replace('/', '_')

                conversation_log_path = os.path.join(st.session_state["page3_current_working_dir"], st.session_state["page3_topic_name_cleaned"], "conversation_log.json")

                if os.path.exists(conversation_log_path):
                    demo_util._display_persona_conversations(DemoFileIOHelper.read_json_file(conversation_log_path))
                else:
                    st.error("Conversation log not found.")

                st.session_state["page3_write_article_state"] = "final_writing"
                status.update(label="Brainstorming complete!", state="complete")
            except Exception as e:
                st.error(f"An error occurred during pre-writing: {e}")
                traceback.print_exc()

    if st.session_state["page3_write_article_state"] == "final_writing":
        with st.status("Compiling the final article... (This may take 4-5 minutes.)") as status:
            try:
                st.session_state["runner"].run(
                    topic=st.session_state["page3_topic"],
                    do_research=False,
                    do_generate_outline=False,
                    do_generate_article=True,
                    do_polish_article=True
                )
                st.session_state["runner"].post_run()
                st.session_state["page3_write_article_state"] = "prepare_to_show_result"
                status.update(label="Final article ready!", state="complete")
            except Exception as e:
                st.error(f"An error occurred during final writing: {e}")
                traceback.print_exc()

    if st.session_state["page3_write_article_state"] == "prepare_to_show_result":
        _, show_result_col, _ = st.columns([4, 3, 4])
        with show_result_col:
            if st.button("Show Final Article"):
                st.session_state["page3_write_article_state"] = "completed"
                st.experimental_rerun()

    if st.session_state["page3_write_article_state"] == "completed":
        current_working_dir_paths = DemoFileIOHelper.read_structure_to_dict(st.session_state["page3_current_working_dir"])
        if st.session_state["page3_topic_name_cleaned"] in current_working_dir_paths:
            current_article_file_path_dict = current_working_dir_paths[st.session_state["page3_topic_name_cleaned"]]
            demo_util.display_article_page(selected_article_name=st.session_state["page3_topic_name_cleaned"],
                                           selected_article_file_path_dict=current_article_file_path_dict,
                                           show_title=True, show_main_article=True, show_chatlog=False, show_steps=True)
        else:
            st.error("No final article found.")
