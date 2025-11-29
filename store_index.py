from dotenv import load_dotenv
from src.helper import (
    load_pdf_file,
    filter_to_minimal_docs,
    text_split,
    download_hugging_face_embeddings,
)
from langchain_community.vectorstores import FAISS
import os

load_dotenv()
extracted_data = load_pdf_file(data="data/")
if not extracted_data:
    exit(1)
filter_data = filter_to_minimal_docs(extracted_data)
text_chunks = text_split(filter_data)
embeddings = download_hugging_face_embeddings()
vectorstore = FAISS.from_documents(documents=text_chunks, embedding=embeddings)
vectorstore.save_local("faiss_index")
