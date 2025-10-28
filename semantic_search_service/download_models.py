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
        print(f"✅ Downloaded {opus_mt_model_name}")
    else:
        print(f"Model already exists at {model_path_fi_en}")

    # --- Finnish SBERT model ---
    fi_sbert = "TurkuNLP/sbert-uncased-finnish-paraphrase"
    fi_sbert_path = os.path.join(models_dir, "sbert-uncased-finnish-paraphrase")
    if not os.path.exists(fi_sbert_path):
        print(f"Downloading {fi_sbert}...")
        SentenceTransformer(fi_sbert).save(fi_sbert_path)

    # --- English MPNet model ---
    en_mpnet = "sentence-transformers/all-mpnet-base-v2"
    en_mpnet_path = os.path.join(models_dir, "all-mpnet-base-v2")
    if not os.path.exists(en_mpnet_path):
        print(f"Downloading {en_mpnet}...")
        SentenceTransformer(en_mpnet).save(en_mpnet_path)

if __name__ == "__main__":
    download_models()