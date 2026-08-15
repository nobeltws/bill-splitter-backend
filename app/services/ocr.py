import io

from PIL import Image


class OCRService:
    def __init__(self):
        self.model = None

    def load_model(self):
        from doctr.models import ocr_predictor

        self.model = ocr_predictor(
            det_arch="db_resnet50",
            reco_arch="crnn_vgg16_bn",
            pretrained=True,
        )

    def extract_words(self, image_bytes: bytes) -> list[dict]:
        if self.model is None:
            raise RuntimeError("OCR model not loaded. Call load_model() first.")

        return self._run_inference(image_bytes)

    def _run_inference(self, image_bytes: bytes) -> list[dict]:
        from PIL import ImageOps

        import numpy as np

        image = Image.open(io.BytesIO(image_bytes))

        # Auto-orient from EXIF
        image = ImageOps.exif_transpose(image)

        # Resize if too large
        max_dim = 4000
        if max(image.size) > max_dim:
            ratio = max_dim / max(image.size)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Convert to numpy for docTR
        img_array = np.array(image)

        # Run docTR
        result = self.model([img_array])

        # Extract words with bounding boxes
        words = []
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    for word in line.words:
                        # docTR geometry is ((x_min, y_min), (x_max, y_max))
                        bbox = [
                            word.geometry[0][0],
                            word.geometry[0][1],
                            word.geometry[1][0],
                            word.geometry[1][1],
                        ]
                        words.append({
                            "text": word.value,
                            "bbox": bbox,
                            "confidence": word.confidence,
                        })

        return words


# Singleton instance
ocr_service = OCRService()
