FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir ".[ocr]"

# Pre-download OCR model weights (bypasses SSL for corporate proxy environments)
RUN python -c "\
import ssl; \
ssl._create_default_https_context = ssl._create_unverified_context; \
from doctr.models import ocr_predictor; \
ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True) \
"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
