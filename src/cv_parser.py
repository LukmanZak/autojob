import json, re, pathlib
import pymupdf

def parse_cv(pdf_path="F:/alpha/CV.pdf"):
    doc = pymupdf.open(pdf_path)
    text = "\n".join([p.get_text() for p in doc])
    # basic extraction
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
    import pathlib
    data = parse_cv()
    out = pathlib.Path("F:/alpha/data/cv_data.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    # remove raw_text for json pretty? keep
    json.dump(data, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Saved {out} with email {data['email']}")
