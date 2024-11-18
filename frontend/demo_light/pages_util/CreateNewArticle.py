import re

from time import sleep

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


def display_storylines(storylines, display_storylines_called):
    button_key = "generated"
    storylines_list = [storylines.storyline_1, storylines.storyline_2, storylines.storyline_3]
    if st.session_state.get("page3_write_article_state", "") == "requested_storyline_generated":
        button_key = "requested"
    st.markdown(
        f"""<p style='text-align: center; font-size: 16px;'>
        Please chose one for AURA to initiate the research for you.<br>
        Not seeing what you like? Scroll down and adjust them as you wish.</p>""",
        unsafe_allow_html=True
    )
    st.write("---")
    if button_key == "requested" and not display_storylines_called:
        st.session_state["requested_select_storyline_button_counter"] += len(storylines_list)
        st.session_state["display_storylines_called"] = True
    requested_select_storyline_button_counter = st.session_state.get("requested_select_storyline_button_counter", 0)
    for idx, storyline in enumerate(storylines_list, max(1, requested_select_storyline_button_counter)):
        # button_id = idx
        storyline_elaboration = (
            f"**{storyline.title}**\n\n"
            f"*{storyline.subheadline}*\n\n"  #added subheadline
            f"{storyline.elaboration}"
        )

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
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                f"Select the storyline", key=f"select_{button_key}_storyline_{idx}"
            ):
                st.session_state["page3_write_article_state"] = "storyline_selected"
                st.session_state["selected_storyline_title"] = storyline.title
                st.session_state["selected_storyline_subheadline"] = storyline.subheadline
                st.session_state["selected_storyline_elaboration"] = storyline_elaboration
                st.session_state["selected_storyline_option"] = storyline_option
        with col2:
            st.markdown(
                """
                <div style="display: block; justify-content: center; width: 100%;">
                    <a href="data:application/pdf;base64,{pdf_data}" download="{generated_file}.pdf">
                        <button style="padding: 14px 20px; font-size: 18px; color: white; background-color: #06908F; border: none; border-radius: 8px; cursor: pointer; width: 100%;">
                            Download the storyline
                        </button>
                    </a>
                </div>
                """.format(
                    pdf_data=demo_util.generate_pdf(storyline.title, "{}\n\n{}".format(storyline_elaboration, storyline_option)),
                    generated_file=re.sub(r'\W+', '_', storyline.title)
                ),
                unsafe_allow_html=True
            )
            # st.rerun()
        st.write("---")

    # if st.session_state.get("page3_write_article_state", "") != "requested_storyline_generated":
    # st.markdown(
    # "<p style='font-size: 16px;'><strong>Want to generate new storylines? Please describe what you are looking for.</strong><br>"
    # "<em>For example: Economic perspective, social context, etc.</em></p>",
    # unsafe_allow_html=True
    # )
    st.markdown(
        f"""
            <p style='text-align: center; font-size: 18px; color: #134a64;'>Want to generate new storylines? Please describe what you are looking for.</p>
            <p style='text-align: center; font-size: 18px; color: #134a64;'>For example: Economic perspective, social context, etc.</p>

        """,
        unsafe_allow_html=True
    )
    # user_feedback = st.text_input(
    #     "Please enter the changes you are looking for:", key="user_feedback"
    # )
    # user_feedback = st.text_area(
    #     label="Please enter the changes you are looking for",
    #     value=st.session_state["selected_storyline_option"],
    #     # label_visibility="collapsed", placeholder="Enter the text here",
    #     height=calculate_height(st.session_state["selected_storyline_option"]),
    # )

    storyline_requested_placeholder = st.empty()

    def action_user_feedback():
        storyline_requested_placeholder.empty()

    user_feedback = st.text_area(
        key="user_feedback_{}".format(st.session_state.get("requested_select_storyline_button_counter", 0)),
        label="Enter the changes you are looking for",
        label_visibility="collapsed",
        placeholder="Enter the changes you are looking for",
        height=100,
        on_change=action_user_feedback
    )

    # if "user_feedback" in st.session_state:
    if user_feedback.strip():
        st.session_state["page3_write_article_state"] = "storyline_requested"
        # if st.session_state.get("file_or_text_uploaded"):
        #     st.session_state["file_or_text_uploaded"] = False
    elif user_feedback:
        with storyline_requested_placeholder.container():
            st.markdown(
                "<p style='color:red;'>Please enter any text to proceed with requested storyline</p>",
                unsafe_allow_html=True
            )

    if st.button(
            "Generate Requested Storylines",
            key="generate_requested_storylines_{}".format(st.session_state.get("requested_select_storyline_button_counter", 0))
    ):
        if user_feedback.strip():
            st.session_state["page3_write_article_state"] = "storyline_requested"
        else:
            with storyline_requested_placeholder.container():
                st.markdown(
                    "<p style='color:red;'>Please enter any text to proceed with requested storyline</p>",
                    unsafe_allow_html=True
                )
        # if st.session_state.get("file_or_text_uploaded"):
        #     st.session_state["file_or_text_uploaded"] = False
        # st.rerun()


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
            background-color: #06908F;
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
            color: #5A8487;
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

    uploaded_file = None
    if "page3_write_article_state" not in st.session_state:
        st.session_state["page3_write_article_state"] = "not_started"
        st.session_state["file_or_text_uploaded"] = False
        st.session_state["requested_select_storyline_button_counter"] = 0
        st.session_state["display_storylines_called"] = False
    # elif st.session_state["page3_write_article_state"] == "not_started":
    #     st.session_state["file_or_text_uploaded"] = False

    if st.session_state.get("unique_key_for_file_uploader") or st.session_state.get("uploaded_file_page"):
        st.session_state["file_or_text_uploaded"] = True
    # st.write("---")

    file_uploaded_placeholder = st.empty()
    uploader_placeholder = st.empty()
    storylines_placeholder = st.empty()

    # with file_uploaded_placeholder.container():
    #     st.markdown(
    #         """<h2 style='text-align: center; color: #06908F;'>Create New Research Report</h2>""",
    #         unsafe_allow_html=True
    #     )

    with uploader_placeholder.container():

        # if st.session_state["page3_write_article_state"] == "not_started":
        st.markdown(
            """<h2 style='text-align: center; color: #06908F;'>Create New Research Report</h2>""",
            unsafe_allow_html=True
        )
        st.markdown(
            """<p style='text-align: center; font-size: 16px;'>
                Upload a file or paste your text (e.g., a press release or story draft).<br>
                AURA will suggest three potential newsworthy angles and provide a detailed research report.
            </p>""",
            unsafe_allow_html=True
        )
        _, search_form_column, _ = st.columns([2, 5, 2])
        with search_form_column:
            # uploader_placeholder = st.empty()
            if not st.session_state["file_or_text_uploaded"]:
                # with uploader_placeholder.container():
                st.markdown("<div class='centered'>", unsafe_allow_html=True)
                uploaded_file = st.file_uploader(
                    "Upload File",
                    type=["csv", "pdf", "doc", "docx", "txt", "rtf", "html"],
                    key="unique_key_for_file_uploader",
                    label_visibility="collapsed",
                )

                if uploaded_file is not None:
                    st.session_state["uploaded_file_page"] = uploaded_file
                    if st.session_state.get("unique_key_for_file_uploader"):
                        del st.session_state["unique_key_for_file_uploader"]
                    st.session_state["file_or_text_uploaded"] = True

                st.session_state["page3_topic"] = st.text_area(
                    label="page3_topic",
                    label_visibility="collapsed",
                    placeholder="or Enter your text here...",
                    height=100,
                )
                st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("file_or_text_uploaded"):
        uploader_placeholder.empty()

    if st.session_state["page3_write_article_state"] == "not_started" and st.session_state.get("file_or_text_uploaded"):
        # if st.session_state.get("file_or_text_uploaded"):
        uploader_placeholder.empty()
        if st.session_state.get("uploaded_file_page"):
            st.session_state["uploaded_file_page"] = st.session_state.get("uploaded_file_page")
            if st.session_state.get("unique_key_for_file_uploader"):
                del st.session_state["unique_key_for_file_uploader"]
        elif st.session_state.get("unique_key_for_file_uploader"):
            st.session_state["uploaded_file_page"] = st.session_state.get("unique_key_for_file_uploader")
            if st.session_state.get("unique_key_for_file_uploader"):
                del st.session_state["unique_key_for_file_uploader"]
        st.session_state["page3_write_article_state"] = "initiated"
        # st.rerun()

    if st.session_state["page3_write_article_state"] == "initiated":
        uploaded_file = st.session_state.get(
            "uploaded_file_page"
        )  # Retrieve the file from session state
        if st.session_state.get("uploaded_file_page"):
            del st.session_state["uploaded_file_page"]

        user_input_text = ""
        if uploaded_file:
            file_uploaded_placeholder.empty()
            with file_uploaded_placeholder.container():
                st.markdown(
                    f"""
                        <p style='text-align: center;'>
                            <span style='text-align: center; font-size: 18px; color: #06908F;'>Uploaded File: 📄</span>
                            <span style='text-align: center; font-size: 18px; color: #134a64;'>{uploaded_file.name}</span>
                        </p>
                    """,
                    unsafe_allow_html=True
                )
            # with st.spinner("Processing and uploading documents..."):
            with st.spinner("Uploading and Processing document(s)..."):
                # loading_placeholder = st.empty()
                # loading_placeholder.markdown(
                #     '<div class="custom-spinner-text">Uploading and Processing document(s)...</div>',
                #     unsafe_allow_html=True
                # )
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
            # loading_placeholder.empty()
        else:
            user_input_text = st.session_state["page3_topic"]

        # st.write("Generating Storylines...")
        # with st.spinner("Generating Storylines..."):

        st.session_state["user_input_text"] = user_input_text

        file_uploaded_placeholder.empty()
        with file_uploaded_placeholder.container():
            st.markdown(
                f"""
                    <p style='text-align: center; font-size: 18px;'>Your Agent is on it!!!<br>
                    Give it 30 seconds & it will put together a pitch and break down the newsworthiness for you.<br></p>
                """,
                unsafe_allow_html=True
            )
            # st.markdown(
            #     f"""
            #         <p style='text-align: center; font-size: 18px; color: #06908F;'>Your Agent is on it!!!</p>
            #         <p style='text-align: center; font-size: 18px; color: #06908F;'>Give it 30 seconds & it will put together a pitch and break down the newsworthiness for you.<br></p>
            #
            #     """,
            #     unsafe_allow_html=True
            # )

        with st.spinner("Generating Storylines..."):
            # loading_placeholder = st.empty()
            # loading_placeholder.markdown(
            #     '<div class="custom-spinner-text">Generating Storylines...</div>',
            #     unsafe_allow_html=True
            # )
            try:
                storylines = generate_storyline(user_input_text)
                st.session_state["storylines"] = storylines
                st.session_state["page3_write_article_state"] = "storyline_generated"
                st.session_state["display_storylines_called"] = False
            except Exception as e:
                st.error(f"An error occurred while generating storylines: {e}")
                logging.error(traceback.format_exc())
            # loading_placeholder.empty()

        file_uploaded_placeholder.empty()

    if st.session_state["page3_write_article_state"] == "storyline_requested":
        file_uploaded_placeholder.empty()
        user_feedback = st.session_state.get(
            "user_feedback_{}".format(st.session_state.get("requested_select_storyline_button_counter", 0)), ""
        )
        user_input_text = st.session_state.get("user_input_text", "")
        if not user_input_text:
            user_input_text = st.session_state.get("page3_topic", "")
        with st.spinner("Generating Requested Storylines..."):
            # loading_placeholder = st.empty()
            # loading_placeholder.markdown(
            #     '<div class="custom-spinner-text">Generating New Storylines...</div>',
            #     unsafe_allow_html=True
            # )
            try:
                storylines = generate_storyline(
                    user_input_text, user_query=user_feedback
                )
                if storylines:
                    # st.session_state["page3_write_article_state"] = "select_storyline"
                    st.session_state["storylines"] = storylines
                    st.session_state["page3_write_article_state"] = "requested_storyline_generated"
                    st.session_state["display_storylines_called"] = False
                    st.rerun()
                    # with storylines_placeholder.container():
                    #     display_storylines(storylines)
            except Exception as e:
                st.error(f"An error occurred while generating new storylines: {e}")
                logging.error(traceback.format_exc())
            # loading_placeholder.empty()

    if st.session_state["page3_write_article_state"] in ["storyline_generated", "requested_storyline_generated"]:
        storylines = st.session_state.get("storylines")
        if storylines:
            requested_generated_value = "Generated"
            if st.session_state.get("page3_write_article_state", "") == "requested_storyline_generated":
                requested_generated_value = "Requested"
            # storylines_placeholder = st.empty()
            # st.session_state["page3_write_article_state"] = "select_storyline"
            # with file_uploaded_placeholder.container():
            #     st.markdown(
            #         f"""
            #             <h5>
            #                 <span style='color: #06908F;'>Three {requested_generated_value} Storylines</span>
            #             </h5>
            #         """,
            #         unsafe_allow_html=True
            #     )
            file_uploaded_placeholder.empty()
            storylines_placeholder.empty()
            with file_uploaded_placeholder.container():
                st.markdown(
                    f"""
                        <h2 style='text-align: center; color: #06908F;'>Three {requested_generated_value} Storylines</h2>
                    """,
                    unsafe_allow_html=True
                )
            # storylines_placeholder.empty()
            with storylines_placeholder.container():
                display_storylines(storylines, st.session_state["display_storylines_called"])

    if st.session_state.get("page3_write_article_state") == "storyline_selected":
        file_uploaded_placeholder.empty()
        storylines_placeholder.empty()
        sleep(0.2)
        with file_uploaded_placeholder.container():
            st.markdown(
                f"""
                    <h2 style='text-align: center; color: #06908F;'>Storyline Elaboration</h2>
                """,
                unsafe_allow_html=True
            )
        with storylines_placeholder.container():
            st.markdown(
                f"""
                    <p style='text-align: center; font-size: 16px;'>This text is heading to your Research Agents! Need to add or cut anything?<br>
                    Make your edits, hit the button, & they'll dive in to build a research report for your chosen storyline.<br></p>
                """,
                unsafe_allow_html=True
            )
            # st.session_state["selected_storyline_option"] = st.text_area(
            #     label="Topic Option",
            #     value=st.session_state["selected_storyline_option"],
            #     # label_visibility="collapsed", placeholder="Enter the text here",
            #     height=calculate_height(st.session_state["selected_storyline_option"]),
            # )
            st.session_state["selected_storyline_elaboration"] = st.text_area(
                label="Storyline Elaboration",
                value=st.session_state["selected_storyline_elaboration"],
                label_visibility="collapsed",
                placeholder="Enter the elaboration here",
                height=calculate_height(st.session_state["selected_storyline_elaboration"])
            )


            # if st.button("Submit Storyline"):
            #     st.session_state["page3_write_article_state"] = "pre_writing"
            #     storylines_placeholder.empty()
            #     st.rerun()
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Submit Storyline"):
                    st.session_state["page3_write_article_state"] = "pre_writing"
                    storylines_placeholder.empty()
                    st.rerun()
            with col2:
                st.markdown(
                    """
                    <div style="display: block; justify-content: center; width: 100%;">
                        <a href="data:application/pdf;base64,{pdf_data}" download="{generated_file}.pdf">
                            <button style="padding: 14px 20px; font-size: 18px; color: white; background-color: #06908F; border: none; border-radius: 8px; cursor: pointer; width: 100%;">
                                Download the storyline
                            </button>
                        </a>
                    </div>
                    """.format(
                        pdf_data=demo_util.generate_pdf(
                            st.session_state["selected_storyline_title"],
                            "{}\n\n{}".format(
                                st.session_state["selected_storyline_elaboration"],
                                st.session_state["selected_storyline_option"]
                            )
                        ),
                        generated_file=re.sub(
                            r'\W+', '_', st.session_state["selected_storyline_title"]
                        )
                    ),
                    unsafe_allow_html=True
                )
        # storylines_placeholder.empty()

    if (
        st.session_state.get("selected_storyline_option", "").strip()
        and st.session_state.get("page3_write_article_state") == "pre_writing"
    ):
        file_uploaded_placeholder.empty()
        uploader_placeholder.empty()
        # storylines_placeholder.empty()
        current_working_dir = os.path.join(demo_util.get_demo_dir(), "DEMO_WORKING_DIR")
        with file_uploaded_placeholder.container():
            st.markdown(
                f"""
                    <h2 style='text-align: center; color: #06908F;'>Storyline Submitted</h2>
                """,
                unsafe_allow_html=True
            )
        with uploader_placeholder.expander("Submitted Storyline"):
            st.write(
                f"\n\n {st.session_state['selected_storyline_option']}"
            )
            st.write(
                f"Topic for research: {st.session_state['selected_storyline_elaboration']}"
            )
        if not os.path.exists(current_working_dir):
            os.makedirs(current_working_dir)

    if st.session_state["page3_write_article_state"] == "pre_writing":
        # file_uploaded_placeholder.empty()
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
        # file_uploaded_placeholder.empty()
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
        file_uploaded_placeholder.empty()
        with file_uploaded_placeholder.container():
            st.markdown(
                f"""
                    <h2 style='text-align: center; color: #06908F;'>Final Report Created</h2>
                """,
                unsafe_allow_html=True
            )
        _, show_result_col, _ = st.columns([4, 3, 4])
        with show_result_col:
            if st.button("Show Final Report", key="show_final_article"):
                st.session_state["page3_write_article_state"] = "completed"
                st.rerun()

    if st.session_state["page3_write_article_state"] == "completed":
        file_uploaded_placeholder.empty()
        with file_uploaded_placeholder.container():
            st.markdown(
                f"""
                    <h2 style='text-align: center; color: #06908F;'>Final Report</h2>
                """,
                unsafe_allow_html=True
            )
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
