import math
import os
import traceback
import streamlit as st
import demo_util
from demo_util import DemoFileIOHelper, truncate_filename
from input_processing import extract_text
from storyline import generate_storyline
import magic
import io
import logging


MIME_TYPE_EXTENSIONS = {
    "application/CDFV2": "doc",
    "application/msword": "doc",
    "application/octet-stream": "docx",
    "application/pdf": "pdf",
    "application/rtf": "rtf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/zip": "docx",
    "text/html": "html",
    "text/plain": "txt",
    "text/rtf": "rtf",
    "application/vnd.oasis.opendocument.spreadsheet": "excel",
    "application/csv": "csv",
    "text/csv": "csv",
}


def handle_uploaded_file(uploaded_file, file_extension):
    # file_extension = uploaded_file.name.split('.')[-1].lower()
    # file_path = f"/tmp/{uploaded_file.name}"

    try:
        # with open(file_path, "wb") as f:
        #     f.write(uploaded_file.getbuffer())

        docs = extract_text(uploaded_file, file_extension)
        return docs
    except Exception as e:
        st.error(f"An error occurred while handling the file: {e}")
        traceback.print_exc()
        # finally:
        #     if os.path.exists(file_path):
        #         os.remove(file_path)
        logging.error(traceback.format_exc())
    # finally:
    #     if os.path.exists(file_path):
    #         os.remove(file_path)
    return None


def display_storylines(storylines):
    st.markdown(
        "<p style='font-size: 18px; font-weight: bold; color: #06908F; margin-top: 40px;'>Here are three possible storylines. "
        "Please chose one for AURA to research thoroughly:</p>",
        unsafe_allow_html=True,
    )
    st.write("---")
    for idx, storyline in enumerate(
        [storylines.storyline_1, storylines.storyline_2, storylines.storyline_3], 1
    ):
        storyline_elaboration = f"**{storyline.title}**\n\n{storyline.elaboration}"
        storyline_option = (
            f"**Type:** {storyline.storyline_type.value}\n\n"
            f"**Angle:** {storyline.angle}\n\n"
            f"**Newsworthiness:**\n"
            + "\n".join(
                [
                    f"- **{criteria.criteria.split(':')[0]}**: {criteria.criteria.split(':', 1)[1]}"
                    for criteria in storyline.newsworthiness
                ]
            )
        )

        st.markdown(storyline_elaboration, unsafe_allow_html=True)
        st.markdown(storyline_option, unsafe_allow_html=True)

        if st.button(
            f"Select the storyline: {storyline.title}", key=f"select_storyline_{idx}"
        ):
            st.session_state["selected_storyline_title"] = storyline.title
            st.session_state["selected_storyline_elaboration"] = storyline_elaboration
            st.session_state["selected_storyline_option"] = storyline_option
            st.session_state["page3_write_article_state"] = "storyline_selected"
            st.rerun()
        st.write("---")

    st.markdown(
        "<p style='font-size: 16px;'>If none of these storylines suit you, please describe what kind of storyline you are looking for:</p>",
        unsafe_allow_html=True,
    )
    user_feedback = st.text_input(
        "Please enter the changes you are looking for:", key="user_feedback"
    )

    if st.button("Generate New Storylines", key="generate_new_storylines"):
        st.session_state["page3_write_article_state"] = "storyline_requested"
        st.rerun()


def calculate_height(text):
    # Estimate the number of lines based on character length and adjust height accordingly
    num_lines = 0
    words_per_line = 15
    lines = text.split("\n")
    for line in lines:
        num_words = line.count(" ") + 1
        num_lines += math.ceil(num_words / words_per_line)
    height_per_line = 27  # You can adjust this depending on styling
    return min(1000, num_lines * height_per_line)  # Set a max height


def create_new_article_page():
    mime = magic.Magic(mime=True)
    css = """
    <style>
        [data-testid='stFileUploader'] {
            width: 100%; /* Make the file uploader wider */
            # max-width: 400px; /* Constrain to a max width */
            # margin-top: 20px;
        }
        [data-testid='stFileUploader'] section {
            padding: 0;
            # float: right;
            background-color: white;
            display: flex; /* Use Flexbox */
            justify-content: center; /* Center the button horizontally */
            align-items: center; /* Center vertically if needed */
        }
        [data-testid='stFileUploader'] section > button {
            width: 60%;
            padding: 15px;
            background-color: #F56329;
            color: white !important; /* Force white text */
            font-size: x-large;
            border-radius: 50px; /* Rounded corners */
            border: 2px solid;
            border-image-slice: 1;
            border-width: 3px;
            # border-image-source: linear-gradient(45deg, #ff6ec4, #7873f5); /* Gradient border */
            transition: transform 0.3s ease;
            text-align: center;
            justify-content: center; /* Center the button horizontally */
            align-items: center; /* Center vertically if needed */
        }
        [data-testid='stFileUploader'] section > button:hover {
            border-color: #08AFAF !important; /* Force darker blue on hover */
            color: yellow !important; /* Force white text on hover */
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
            transform: translateY(-2px);
        }
        [data-testid='stFileUploader'] section > button:active {
            background-color: #056161 !important; /* Force darker blue on hover */
            border-color: #08C4C4 !important; /* Force darker blue on hover */
            color: yellow !important; /* Force white text on hover */
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
            transform: translateY(-2px);
        }
        [data-testid='stFileUploader'] section > button:focus {
            border-color: #056161 !important; /* Force darker blue on hover */
            color: yellow !important; /* Force white text on hover */
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
            transform: translateY(-2px);
        }
        [data-testid='stFileUploader'] section > input + div {
            display: none;
        }
        [data-testid='stFileUploader'] section + div {
            float: center;
            # padding-top: 0;
        }
        [data-testid='stUploadedFile'] {
            background-color: #b9f7f7;
            padding: 1px;
            color: #F56329;
        }
        [data-testid='stTextInput'] {
            width: 100%; /* Make the file uploader wider */
            max-width: 400px; /* Constrain to a max width */
            margin-top: 20px;
        }
        [data-testid='stTextInput'] div {
            padding: 0;
            # float: right;
            background-color: white;
            border-color: white;
        }
        [data-testid='stTextInput'] div > input {
            width: 100%;
            padding: 15px;
            background-color: white;
            border-radius: 20px; /* Rounded corners */
            border: 2px solid;
            border-image-slice: 1;
            border-width: 3px;
            # border-image-source: linear-gradient(45deg, #ff6ec4, #7873f5); /* Gradient border */
            transition: transform 0.3s ease;
            text-align: center;
        }
        [data-testid='InputInstructions'] {
            position: relative;
            top: 5px !important;
            color: red !important; /* Force white text on hover */
        }
        /* Spinner text styling */
        .custom-spinner-text {
            color: #06908F; /*F63366 Custom color */
            font-size: 18px; /* Custom font size */
            font-weight: bold;
            text-align: left;
            animation: blink 1s infinite; /* Blinking effect */
        }

        /* Blinking keyframes */
        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        /* Custom spinner styling */
        [data-testid="stSpinner"] div > i {
            border-top-color: #06908F !important; /* Change spinner color */
        }
        /* Target the label of the text area */
        [data-testid="stTextArea"] label > div > p {
            color: #06908F; /* Custom color (e.g., orange) */
            font-size: 20px; /* Custom font size */
            font-weight: bold; /* Optional: Make the font bold */
        }
        [data-testid="stTextArea"] textarea {
            background-color: #f0f8ff; /* Custom color (e.g., orange) */
            color: #333; /* Custom font size */
            border: 1px solid #08AFAF; /* Custom border color */
            border-radius: 8px; /* Custom border radius */
            padding: 10px; /* Custom padding inside the text area */
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    demo_util.clear_other_page_session_state(page_index=3)

    if "page3_write_article_state" not in st.session_state:
        st.session_state["page3_write_article_state"] = "not_started"

    st.markdown(
        """<h2 style='text-align: center; color: #06908F;'>Create a New Research Report</h2>""",
        unsafe_allow_html=True,
    )

    if st.session_state["page3_write_article_state"] == "not_started":
        st.markdown(
            """<p style='text-align: center; font-size: 16px; color: #F56329;'>
                Upload a file or paste your text (e.g., a press release or story draft).<br>
                AURA will suggest three potential newsworthy angles and provide a detailed research report.
            </p>""",
            unsafe_allow_html=True,
        )
        _, search_form_column, _ = st.columns([2, 5, 2])
        with search_form_column:
            st.markdown("<div class='centered'>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Upload File",
                type=["csv", "pdf", "doc", "docx", "txt", "rtf", "html"],
                key="unique_key_for_file_uploader",
                label_visibility="collapsed",
            )
            st.session_state["page3_topic"] = st.text_area(
                label="page3_topic",
                label_visibility="collapsed",
                placeholder="or Enter your text here...",
                height=100,
            )
            st.markdown("</div>", unsafe_allow_html=True)

            if uploaded_file or st.session_state["page3_topic"].strip():
                st.session_state["uploaded_file"] = uploaded_file
                st.session_state["page3_write_article_state"] = "initiated"

    if st.session_state["page3_write_article_state"] == "initiated":
        uploaded_file = st.session_state.get(
            "uploaded_file"
        )  # Retrieve the file from session state
        # print(
        #     "create new article",
        #     type(uploaded_file), isinstance(uploaded_file, io.BytesIO),
        #     isinstance(uploaded_file, st.runtime.uploaded_file_manager.UploadedFile)
        # )

        user_input_text = ""
        if uploaded_file:
            # with st.spinner("Processing and uploading documents..."):
            with st.spinner(""):
                loading_placeholder = st.empty()
                loading_placeholder.markdown(
                    '<div class="custom-spinner-text">Processing and uploading documents...</div>',
                    unsafe_allow_html=True,
                )
                if isinstance(uploaded_file, io.BytesIO):
                    mimeType = mime.from_buffer(uploaded_file.getvalue())
                    ext = (
                        MIME_TYPE_EXTENSIONS[mimeType]
                        if mimeType in MIME_TYPE_EXTENSIONS
                        else ""
                    )
                elif os.path.exists(uploaded_file):
                    mimeType = mime.from_file(uploaded_file)
                    ext = (
                        MIME_TYPE_EXTENSIONS[mimeType]
                        if mimeType in MIME_TYPE_EXTENSIONS
                        else ""
                    )
                else:
                    mimeType = uploaded_file.type
                    ext = (
                        MIME_TYPE_EXTENSIONS[mimeType]
                        if mimeType in MIME_TYPE_EXTENSIONS
                        else ""
                    )

                if not ext:
                    mimeType = uploaded_file.type
                    ext = (
                        MIME_TYPE_EXTENSIONS[mimeType]
                        if mimeType in MIME_TYPE_EXTENSIONS
                        else ""
                    )
                docs = []
                if ext:
                    in_memory_file = io.BytesIO()
                    file_content = uploaded_file.read()
                    in_memory_file.write(file_content)
                    in_memory_file.seek(0)
                    docs = handle_uploaded_file(in_memory_file, ext)
                if docs:
                    user_input_text = " ".join([doc.page_content for doc in docs])
                else:
                    # st.write("No text could be extracted from the document.")
                    user_input_text = st.session_state["page3_topic"]
            loading_placeholder.empty()
        else:
            user_input_text = st.session_state["page3_topic"]

        # st.write("Generating Storylines...")
        # with st.spinner("Generating Storylines..."):

        st.session_state["user_input_text"] = user_input_text

        with st.spinner(""):
            loading_placeholder = st.empty()
            loading_placeholder.markdown(
                '<div class="custom-spinner-text">Generating Storylines...</div>',
                unsafe_allow_html=True,
            )
            try:
                storylines = generate_storyline(user_input_text)
                st.session_state["storylines"] = storylines
                st.session_state["page3_write_article_state"] = "storyline_generated"
            except Exception as e:
                st.error(f"An error occurred while generating storylines: {e}")
                logging.error(traceback.format_exc())
            loading_placeholder.empty()

    if st.session_state["page3_write_article_state"] == "storyline_generated":
        storylines = st.session_state.get("storylines")
        if storylines:
            display_storylines(storylines)

    if st.session_state["page3_write_article_state"] == "storyline_requested":
        user_feedback = st.session_state.get("user_feedback", "")
        user_input_text = st.session_state.get("user_input_text", "")
        if not user_input_text:
            user_input_text = st.session_state.get("page3_topic", "")
        with st.spinner("Generating New Storylines..."):
            loading_placeholder = st.empty()
            loading_placeholder.markdown(
                '<div class="custom-spinner-text">Generating New Storylines...</div>',
                unsafe_allow_html=True,
            )
            try:
                storylines = generate_storyline(
                    user_input_text, user_query=user_feedback
                )
                st.session_state["storylines"] = storylines
                st.session_state["page3_write_article_state"] = "storyline_generated"
                st.experimental_rerun()
            except Exception as e:
                st.error(f"An error occurred while generating new storylines: {e}")
                logging.error(traceback.format_exc())
            loading_placeholder.empty()

    if st.session_state.get("page3_write_article_state") == "storyline_selected":
        st.session_state["selected_storyline_option"] = st.text_area(
            label="Topic Option",
            value=st.session_state["selected_storyline_option"],
            # label_visibility="collapsed", placeholder="Enter the text here",
            height=calculate_height(st.session_state["selected_storyline_option"]),
        )
        st.session_state["selected_storyline_elaboration"] = st.text_area(
            label="Storyline Elaboration",
            value=st.session_state["selected_storyline_elaboration"],
            # label_visibility="collapsed", placeholder="Enter the elaboration here",
            height=calculate_height(st.session_state["selected_storyline_elaboration"]),
        )

        if st.button("Proceed with this Storyline"):
            st.session_state["page3_write_article_state"] = "pre_writing"
            st.rerun()

    if (
        st.session_state.get("selected_storyline_option", "").strip()
        and st.session_state.get("page3_write_article_state") == "pre_writing"
    ):
        current_working_dir = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR")
        st.write(
            f"Selected storyline:\n\n {st.session_state['selected_storyline_option']}"
        )
        st.write(
            f"Topic for research: {st.session_state['selected_storyline_elaboration']}"
        )
        if not os.path.exists(current_working_dir):
            os.makedirs(current_working_dir)

    if st.session_state["page3_write_article_state"] == "pre_writing":
        if "runner" not in st.session_state:
            demo_util.set_storm_runner()

        st.session_state["page3_current_working_dir"] = current_working_dir
        status = st.status(
            "I am brainstorming now to research the topic. (This may take 2-3 minutes.)"
        )
        st_callback_handler = demo_util.StreamlitCallbackHandler(status)
        with status:
            try:
                st.session_state["runner"].run(
                    topic=st.session_state["selected_storyline_elaboration"],
                    do_research=True,
                    do_generate_outline=True,
                    do_generate_article=False,
                    do_polish_article=False,
                    callback_handler=st_callback_handler,
                )

                if "page3_topic_name_cleaned" not in st.session_state:
                    st.session_state["page3_topic_name_cleaned"] = (
                        st.session_state["selected_storyline_elaboration"]
                        .replace(" ", "_")
                        .replace("/", "_")
                    )
                    st.session_state["page3_topic_name_truncated"] = truncate_filename(
                        st.session_state["page3_topic_name_cleaned"]
                    )

                conversation_log_path = os.path.join(
                    st.session_state["page3_current_working_dir"],
                    st.session_state["page3_topic_name_truncated"],
                    "conversation_log.json",
                )
                demo_util._display_persona_conversations(
                    DemoFileIOHelper.read_json_file(conversation_log_path)
                )
                st.session_state["page3_write_article_state"] = "final_writing"
                status.update(label="brain**STORM**ing complete!", state="complete")
            except Exception as e:
                st.error(f"An error occurred while running the STORM process: {e}")
                logging.error(traceback.format_exc())

    if st.session_state["page3_write_article_state"] == "final_writing":
        with st.status(
            "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)"
        ) as status:
            st.info(
                "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)"
            )
            try:
                st.session_state["runner"].run(
                    topic=st.session_state["selected_storyline_elaboration"],
                    do_research=False,
                    do_generate_outline=False,
                    do_generate_article=True,
                    do_polish_article=True,
                    remove_duplicate=False,
                )
                st.session_state["runner"].post_run()
                st.session_state["page3_write_article_state"] = "prepare_to_show_result"
                status.update(label="information synthesis complete!", state="complete")
            except Exception as e:
                st.error(f"An error occurred while finalizing the article: {e}")
                logging.error(traceback.format_exc())

    if st.session_state["page3_write_article_state"] == "prepare_to_show_result":
        _, show_result_col, _ = st.columns([4, 3, 4])
        with show_result_col:
            if st.button("Show Final Article", key="show_final_article"):
                st.session_state["page3_write_article_state"] = "completed"
                st.rerun()

    if st.session_state["page3_write_article_state"] == "completed":
        article_title = st.session_state.get(
            "selected_storyline_title", "Untitled Article"
        )
        current_working_dir_paths = DemoFileIOHelper.read_structure_to_dict(
            st.session_state["page3_current_working_dir"]
        )
        if st.session_state["page3_topic_name_truncated"] in current_working_dir_paths:
            current_article_file_path_dict = current_working_dir_paths[
                st.session_state["page3_topic_name_truncated"]
            ]
            demo_util.display_article_page(
                selected_article_name=article_title,
                selected_article_file_path_dict=current_article_file_path_dict,
                show_title=True,
                show_main_article=True,
            )
        else:
            st.error("No final article found.")
