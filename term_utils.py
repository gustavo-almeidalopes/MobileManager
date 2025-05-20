import os
from PyPDF2 import PdfReader
from docx import Document

# Usar um caminho relativo ao diretório da aplicação
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TERMS_DIR = os.path.join(BASE_DIR, "..", "terms")

def load_term_for(device_type: str, model: str) -> tuple:
    """
    Busca o arquivo .pdf ou .docx em terms/{device_type}/{model}.* e retorna uma tupla (texto, caminho_do_arquivo).
    O texto é uma mensagem descritiva, e o caminho_do_arquivo é None se não encontrado.
    """
    if not device_type or not model:
        return "Tipo de dispositivo ou modelo não especificado.", None

    device_type = device_type.lower().strip()
    model = model.lower().strip().replace(" ", "_")  # Sanitiza o modelo

    dir_path = os.path.join(TERMS_DIR, device_type)
    if not os.path.isdir(dir_path):
        return f"Diretório de termos para '{device_type}' não encontrado em '{dir_path}'.", None

    # Listar possíveis arquivos com extensão
    for filename in os.listdir(dir_path):
        name, ext = os.path.splitext(filename.lower())
        if name == model and ext in ('.pdf', '.docx'):
            path = os.path.join(dir_path, filename)
            try:
                if ext == '.pdf':
                    reader = PdfReader(path)
                    text_parts = []
                    for page in reader.pages:
                        text_parts.append(page.extract_text() or "")
                    texto = "\n".join(text_parts).strip()
                    return (texto or "PDF encontrado mas sem texto extraído.", path)
                else:  # .docx
                    doc = Document(path)
                    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                    texto = "\n".join(paragraphs).strip()
                    return (texto or "DOCX encontrado mas sem texto.", path)
            except Exception as e:
                return f"Erro ao ler o arquivo '{filename}': {str(e)}", None

    return f"Termo não encontrado para '{device_type}/{model}' em '{dir_path}'.", None
