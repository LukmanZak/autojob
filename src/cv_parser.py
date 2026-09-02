import json, re, pathlib
import pymupdf
from .config import CV_PDF, CV_JSON, ensure_dirs

def parse_cv(pdf_path=None):
    # pakai config jika tidak diisi
    pdf_path = pathlib.Path(pdf_path) if pdf_path else CV_PDF
    doc = pymupdf.open(str(pdf_path))
    text = "\n".join([p.get_text() for p in doc])
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    linkedin = re.search(r"https?://www\.linkedin\.com[^\s]+", text)
    phone = re.search(r"\+?\d[\d\s-]{8,}", text)
    data = {
        "name": "Lukman Zakaria",
        "email": email.group(0) if email else "lukmanzakaria04@gmail.com",
        "phone": phone.group(0).strip() if phone else "",
        "location": "Setiabudi, Jakarta Selatan",
        "linkedin": linkedin.group(0) if linkedin else "https://www.linkedin.com/in/lukman-zakaria-3443a522a/",
        "education": "S1 Matematika Universitas Brawijaya GPA 3.43",
        "skills": ["Python","FastAPI","PyTorch","Docker","PostgreSQL","S3","Vector DB","LLMs","RAG","Computer Vision","AWS"],
        "summary": "Machine Learning Engineer dengan latar S1 Matematika, spesialis Python/FastAPI/PyTorch/Docker/PostgreSQL/S3/VectorDB/LLMs, RAG chatbot & n8n automation.",
        "raw_text": text[:3000]
    }
    return data

if __name__ == "__main__":
    ensure_dirs()
    data = parse_cv()
    import json as _json
    _json.dump(data, open(CV_JSON,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Saved {CV_JSON} with email {data['email']}")
