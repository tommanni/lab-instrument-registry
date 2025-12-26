import os
from sentence_transformers import SentenceTransformer
from transformers import MarianMTModel, MarianTokenizer


def download_models():
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)

    # --- Fine tuned Helsinki-NLP/opus-mt-fi-en ---
    opus_mt_model_name = "tommanni/fine-tuned-opus-mt-fi-en"
    model_path_fi_en = os.path.join(models_dir, opus_mt_model_name.replace("/", "_"))

    if not os.path.exists(model_path_fi_en):
        print(f"Downloading {opus_mt_model_name}...")
        tokenizer = MarianTokenizer.from_pretrained(opus_mt_model_name)
        model = MarianMTModel.from_pretrained(opus_mt_model_name)
        model.save_pretrained(model_path_fi_en)
        tokenizer.save_pretrained(model_path_fi_en)
        print(f"Downloaded {opus_mt_model_name}")
    else:
        print(f"Model already exists at {model_path_fi_en}")

    # --- English BGE model ---
    embedding_model = "BAAI/bge-base-en-v1.5"
    embedding_model_path = os.path.join(models_dir, "bge-base-en-v1.5")
    if not os.path.exists(embedding_model_path):
        print(f"Downloading {embedding_model}...")
        SentenceTransformer(embedding_model).save(embedding_model_path)
        print(f"Downloaded {embedding_model}")
    else:
        print(f"Model already exists at {embedding_model_path}")

if __name__ == "__main__":
    download_models()