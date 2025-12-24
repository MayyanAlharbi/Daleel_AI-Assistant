
def check_environment():
    import numpy, faiss
    from sentence_transformers import SentenceTransformer
    import fitz
    from docx import Document
    from fastapi import FastAPI

    print("numpy", numpy.__version__)
    print("faiss ok")
    print("sentence-transformers ok")
    print("PyMuPDF ok")
    print("python-docx ok")
    print("fastapi ok")
