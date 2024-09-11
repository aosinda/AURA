import re
import sys

import pandas as pd
import numpy as np
from langchain_community.document_loaders import DataFrameLoader, PyPDFLoader
from langchain.docstore.document import Document

import io
import traceback

import os
import subprocess
from subprocess import Popen, PIPE
from datetime import datetime, date
from io import BytesIO
from time import sleep

import mammoth
import pypandoc
from fold_to_ascii import fold
from lxml import html as htmlParser
from pdfminer.converter import TextConverter, XMLConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from striprtf.striprtf import rtf_to_text
from tidylib import tidy_document
import streamlit as st


def process_csv(file):
    # Read CSV file inputted by user, also bespoke
    df = pd.read_csv(file)
    df.dropna(axis=1, inplace=True)
    # Integer overflow as pandas is interpreting these as unsigned ints
    df["CONTENT_KEY"] = df["CONTENT_KEY"].astype(np.float64)
    loader = DataFrameLoader(df, page_content_column="CONTENT_BODY_TEXT")
    documents = loader.load()
    return documents


def process_pdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return documents


def save_uploaded_file(uploaded_file, save_path):
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    f.close()
    return save_path


def extract_data_from_pdf(pdf_path, format='text', codec='utf-8', password=''):
    print(type(pdf_path))
    text = ""
    try:
        max_pages = 0
        caching = True
        page_nos = set()
        print(type(pdf_path), isinstance(pdf_path, io.BytesIO), isinstance(pdf_path, st.runtime.uploaded_file_manager.UploadedFile))
        if isinstance(pdf_path, io.BytesIO):
            for page in PDFPage.get_pages(
                    pdf_path, page_nos, maxpages=max_pages, password=password, caching=caching, check_extractable=True
            ):
                r_src_mgr = PDFResourceManager()
                ret_str = io.StringIO()
                la_params = LAParams()
                if format == 'text':
                    device = TextConverter(r_src_mgr, ret_str, laparams=la_params)
                elif format == 'html':
                    device = HTMLConverter(r_src_mgr, ret_str, laparams=la_params)
                elif format == 'xml':
                    device = XMLConverter(r_src_mgr, ret_str, laparams=la_params)
                else:
                    raise ValueError('provide format, either text, html or xml!')
                interpreter = PDFPageInterpreter(r_src_mgr, device)
                interpreter.process_page(page)

                text = ret_str.getvalue()
                yield text
                device.close()
                ret_str.close()
        else:
            fp = open(pdf_path, 'rb')
            for page in PDFPage.get_pages(
                    fp, page_nos, maxpages=max_pages, password=password, caching=caching, check_extractable=True
            ):
                r_src_mgr = PDFResourceManager()
                ret_str = io.StringIO()
                la_params = LAParams()
                if format == 'text':
                    device = TextConverter(r_src_mgr, ret_str, laparams=la_params)
                elif format == 'html':
                    device = HTMLConverter(r_src_mgr, ret_str, laparams=la_params)
                elif format == 'xml':
                    device = XMLConverter(r_src_mgr, ret_str, laparams=la_params)
                else:
                    raise ValueError('provide format, either text, html or xml!')
                interpreter = PDFPageInterpreter(r_src_mgr, device)
                interpreter.process_page(page)

                text = ret_str.getvalue()
                yield text
                device.close()
                ret_str.close()
            fp.close()
    except:
        traceback.print_exc()
    return text


def extract_text_by_page(pdf_path):
    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            resource_manager = PDFResourceManager()
            fake_file_handle = io.StringIO()

            converter = TextConverter(resource_manager,
                                      fake_file_handle)

            page_interpreter = PDFPageInterpreter(resource_manager,
                                                  converter)

            page_interpreter.process_page(page)
            text = fake_file_handle.getvalue()

            yield text

            # close open handles
            converter.close()
            fake_file_handle.close()


def extract_html_from_docx(doc_path):
    '''
    Helper function to extract plain text from .docx files

    :param doc_path: path to .docx file to be extracted
    :return: string of extracted text
    '''
    file_path = ""
    try:
        if isinstance(doc_path, io.BytesIO):
            result = mammoth.convert_to_html(doc_path)
            text = result.value
        else:
            with open(doc_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                text = result.value
        return text
    except:
        traceback.print_exc()
        try:
            if isinstance(doc_path, io.BytesIO):
                file_path = "/tmp/" + datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f") + ".docx"
                with open(file_path, "wb") as outfile:
                    # Copy the BytesIO stream to the output file
                    outfile.write(doc_path.getvalue())
                outfile.close()
                retry = 1
                while not os.path.exists(file_path) and retry <= 200:
                    sleep(0.01)
                    retry += 1
            else:
                file_path = doc_path
            output = pypandoc.convert(file_path, 'html')
            try:
                output, errors = tidy_document(output, options={
                    'numeric-entities': 1,
                    'wrap': 80,
                })
            except:
                traceback.print_exc()
                pass
            output = output.replace(u"\u2018", '&lsquo;').replace(u"\u2019", '&rsquo;')
            output = output.replace(u"\u201c", "&ldquo;").replace(u"\u201d", "&rdquo;")
            if type(output) is not str:
                output = output.encode('utf-8')
            text = output
        except:
            traceback.print_exc()
            text = '<div></div>'
        if isinstance(doc_path, io.BytesIO) and os.path.exists(file_path):
            os.remove(file_path)
        return text


def extract_html_from_doc(doc_path):
    '''
    Helper function to extract plain text from .doc files

    :param doc_path: path to .doc file to be extracted
    :return: string of extracted text
    '''
    file_path = ""
    docx_path = ""
    try:
        if isinstance(doc_path, io.BytesIO):
            file_path = "/tmp/" + datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f") + ".doc"
            with open(file_path, "wb") as outfile:
                # Copy the BytesIO stream to the output file
                outfile.write(doc_path.getvalue())
            outfile.close()
            retry = 1
            while not os.path.exists(file_path) and retry <= 200:
                sleep(0.01)
                retry += 1
        else:
            file_path = doc_path
        docx_path = "/tmp/" + os.path.splitext(os.path.basename(file_path))[0] + ".docx"
        subprocess.call(['soffice', '--headless', '--convert-to', 'docx', "--outdir", "/tmp", file_path])
        retry = 1
        while not os.path.exists(docx_path) and retry <= 200:
            sleep(0.01)
            retry += 1
        try:
            html = extract_html_from_docx(docx_path)
            if os.path.exists(docx_path):
                os.remove(docx_path)
            if isinstance(doc_path, io.BytesIO) and os.path.exists(file_path):
                os.remove(file_path)
        except:
            traceback.print_exc()
            if os.path.exists(docx_path):
                os.remove(docx_path)
            if isinstance(doc_path, io.BytesIO) and os.path.exists(file_path):
                os.remove(file_path)
            html = '<div></div>'
        return html
    except:
        traceback.print_exc()
        if os.path.exists(docx_path):
            os.remove(docx_path)
        if isinstance(doc_path, io.BytesIO) and os.path.exists(file_path):
            os.remove(file_path)
        return '<div></div>'


def extract_text_from_rtf(rtf_path):
    try:
        if isinstance(rtf_path, io.BytesIO):
            text = rtf_path.getvalue().decode('utf8', errors='ignore')
        else:
            f = open(rtf_path, encoding="utf8", errors='ignore')
            text = f.read()
            f.close()
        text = rtf_to_text(text)
        return text
    except:
        traceback.print_exc()
        return ' '


def extract_text_from_txt(txt_path):
    text = ''
    if isinstance(txt_path, io.BytesIO):
        try:
            text = txt_path.getvalue().decode('utf8', errors='ignore')
        except:
            traceback.print_exc()
    else:
        f = open(txt_path, encoding="utf8", errors='ignore')
        text = f.read()
        f.close()
    return text


def extract_text_from_html(html_path):
    html = '<p></p>'
    if isinstance(html_path, io.BytesIO):
        try:
            html = html_path.getvalue().decode('utf8', errors='ignore')
        except:
            traceback.print_exc()
            pass
    else:
        f = open(html_path, encoding="utf8", errors='ignore')
        html = f.read()
        f.close()
    html = fold(html)
    dom = htmlParser.fromstring(html)
    text = str(dom.text_content())
    return text


def extract_text(file_path, extension):
    '''
    Wrapper function to detect the file extension and call text/html
    extraction function accordingly

    :param file_path: path of file of which text is to be extracted
    :param extension: extension of file `file_name`
    '''
    # text = ''
    docs = []
    if extension == 'pdf':
        for page in extract_data_from_pdf(file_path):
            if page.strip():
                docs.append(Document(page_content=page, metadata={"source": "local"}))
        # for page in extract_text_by_page(saved_file_path):
        #     if page.strip():
        #         docs.append(Document(page_content=page, metadata={"source": "local"}))
        # print("extract_data_from_pdf", docs)
        # sys.stdout.flush()
        if not docs:
            save_path = "/tmp/{}.pdf".format(
                datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
            )
            saved_file_path = save_uploaded_file(file_path, save_path)
            retry = 1
            while not os.path.exists(saved_file_path) and retry <= 200:
                sleep(0.01)
                retry += 1
            docs = process_pdf(saved_file_path)
            # print("process_pdf", docs)
            # sys.stdout.flush()
            if os.path.exists(saved_file_path):
                os.remove(saved_file_path)
    elif extension == 'docx':
        html = extract_html_from_docx(file_path)
        html = fold(html)
        dom = htmlParser.fromstring(html)
        text = str(dom.text_content())
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": "local"}))
        # print("extract_html_from_docx", docs)
        # sys.stdout.flush()
    elif extension == 'doc':
        html = extract_html_from_doc(file_path)
        html = fold(html)
        dom = htmlParser.fromstring(html)
        text = str(dom.text_content())
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": "local"}))
        # print("extract_html_from_doc", text, type(text))
        # sys.stdout.flush()
    elif extension == 'rtf':
        text = extract_text_from_rtf(file_path)
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": "local"}))
        # print("extract_text_from_rtf", text)
        # sys.stdout.flush()
    elif extension == 'txt':
        text = extract_text_from_txt(file_path)
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": "local"}))
        # print("extract_text_from_txt", text)
        # sys.stdout.flush()
    elif extension == 'html':
        text = extract_text_from_html(file_path)
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": "local"}))
        # print("extract_text_from_html", text)
        # sys.stdout.flush()
    return docs
