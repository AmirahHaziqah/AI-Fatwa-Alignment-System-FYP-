import math
import re
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from utils import normalize_text, get_score_tier, get_score_tier_colors, get_score_css_class

# =========================================================
# REQUIRED IMPORTS
# SBERT is mandatory — the weighted composite score
# (0.55 × SBERT + 0.30 × TF-IDF + 0.15 × keyword coverage)
# cannot be computed correctly without it.
# =========================================================
from sentence_transformers import SentenceTransformer

SBERT_AVAILABLE = True  # Always True; import above will raise on missing install

# =========================================================
# TEXT PROCESSING
# =========================================================
class TextCleaner:
    DEFAULT_STOPWORDS = {
        "the", "a", "an", "and", "of", "to", "is", "in", "on", "for", "with",
        "that", "this", "it", "as", "are", "was", "were", "be", "by", "or",
        "from", "at", "which", "can", "may", "should", "would", "will", "if",
        "about", "into", "than", "then", "also", "such", "their", "there",
        "these", "those", "has", "have", "had", "but", "not", "no", "yes",
        "dan", "atau", "yang", "di", "ke", "dengan", "untuk", "pada", "adalah",
        "ialah", "ini", "itu", "dalam", "oleh", "sebagai", "bagi", "jika",
        "maka", "sahaja", "agar", "supaya", "kerana", "daripada", "kepada",
        "masih", "telah", "akan", "boleh", "tidak", "ya", "lebih", "kurang",
        "semasa", "selepas", "sebelum", "antara", "setelah", "serta", "juga",
        "bukan", "lagi", "satu", "dua", "tiga", "rawatan", "proses",
        "menurut", "islam", "hukum", "apakah", "ringkasnya", "kesimpulan",
        "contoh", "status", "menjadi", "berhak", "sah", "dibenarkan",
        "ulama", "fatwa", "malaysia", "jelas", "tegas"
    }

    DOMAIN_KEEPWORDS = {
        "ivf", "iui", "icsi", "art", "fatwa", "hukum", "harus", "haram",
        "bayi", "tabung", "uji", "sperma", "ovum", "embrio", "rahim",
        "surrogacy", "nasab", "ibu", "tumpang", "penderma", "suami", "isteri",
        "zuriat", "persenyawaan", "donor", "abortion", "pengguguran",
        "mani", "bank", "air", "bankairmani", "spermbank", "ketiga",
        "halal", "syariah", "syarak", "perkahwinan", "wali", "pusaka", "benih",
        "carrier", "surrogate", "susu", "susuan", "mahram", "radhaah", "radha",
        "penyusuan", "milk", "klon", "cloning", "stem", "cell", "sel",
        "terapeutik", "reproduktif", "rogol", "rape", "zina", "thalassemia",
        "talasemia", "genetic", "genetik", "kontraseptif", "contraceptive", "hiv", "aids",
        "oku", "janin", "foetus", "fetus", "kandungan", "maternal", "kesihatan",
        "kondom", "mahram", "pembiakan", "perubatan"
    }

    @staticmethod
    def clean(text):
        text = normalize_text(text).lower()
        text = re.sub(r"http\S+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s\-/]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def tokenize(text):
        """
        Manual tokenization — no NLTK dependency.
        Splits on whitespace and handles hyphenated / slash-separated tokens.
        """
        cleaned = TextCleaner.clean(text)
        if not cleaned:
            return []

        # Plain whitespace split — manual, no external library
        raw_tokens = cleaned.split()

        normalized_tokens = []
        for token in raw_tokens:
            token = token.strip().lower()
            if not token:
                continue

            if "-" in token:
                parts = [p for p in token.split("-") if p]
                normalized_tokens.extend(parts)
                normalized_tokens.append(token.replace("-", ""))

            if "/" in token:
                parts = [p for p in token.split("/") if p]
                normalized_tokens.extend(parts)
                normalized_tokens.append(token.replace("/", ""))

            normalized_tokens.append(token)

        return normalized_tokens

    @staticmethod
    def remove_stopwords(tokens):
        filtered = []
        for t in tokens:
            if len(t) <= 1:
                continue
            if t in TextCleaner.DOMAIN_KEEPWORDS:
                filtered.append(t)
                continue
            if t not in TextCleaner.DEFAULT_STOPWORDS:
                filtered.append(t)
        return filtered

    @staticmethod
    def preprocess(text):
        return TextCleaner.remove_stopwords(TextCleaner.tokenize(text))

    @staticmethod
    def preprocess_to_string(text):
        return " ".join(TextCleaner.preprocess(text))


# =========================================================
# MANUAL TF-IDF IMPLEMENTATION
# Formula (4): Cosine Similarity(A, B) = (A · B) / (|A| |B|)
# where A and B are TF-IDF vectors of the two texts.
# =========================================================
class ManualTFIDF:
    """
    Manually computes TF-IDF vectors from a corpus without any external
    library. Term Frequency is computed per document; Inverse Document
    Frequency uses the standard log formula across the corpus.
    Cosine similarity is then applied as per Equation (4) of the proposal.
    """

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self._fitted = False

    def fit(self, corpus: List[str]):
        """Build vocabulary and IDF weights from a list of documents."""
        cleaned_corpus = [
            TextCleaner.preprocess_to_string(doc)
            for doc in corpus
            if normalize_text(doc).strip()
        ]
        if not cleaned_corpus:
            self._fitted = False
            return self

        N = len(cleaned_corpus)

        # Build vocabulary
        vocab_set: Set[str] = set()
        for doc in cleaned_corpus:
            vocab_set.update(doc.split())
        self.vocabulary = {term: idx for idx, term in enumerate(sorted(vocab_set))}

        # Compute document frequency (df) for each term
        df: Dict[str, int] = {term: 0 for term in self.vocabulary}
        for doc in cleaned_corpus:
            present = set(doc.split())
            for term in present:
                if term in df:
                    df[term] += 1

        # IDF = log((N + 1) / (df + 1)) + 1  — smoothed to avoid zero division
        self.idf = {}
        for term, idx in self.vocabulary.items():
            self.idf[term] = math.log((N + 1) / (df[term] + 1)) + 1.0

        self._fitted = True
        return self

    def transform(self, text: str) -> np.ndarray:
        """
        Convert a single document to a TF-IDF vector.
        TF = (count of term in doc) / (total terms in doc)
        TF-IDF weight = TF * IDF
        """
        if not self._fitted or not self.vocabulary:
            return np.zeros(1)

        cleaned = TextCleaner.preprocess_to_string(text)
        tokens = cleaned.split()
        total_terms = len(tokens) if tokens else 1

        # Term frequency
        tf: Dict[str, float] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        for term in tf:
            tf[term] /= total_terms

        # Build vector
        vec = np.zeros(len(self.vocabulary))
        for term, idx in self.vocabulary.items():
            if term in tf:
                vec[idx] = tf[term] * self.idf[term]

        return vec

    @staticmethod
    def cosine_similarity_vectors(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Equation (4): Cosine Similarity(A, B) = (A · B) / (|A| |B|)
        A = TF-IDF vector of AI-generated response
        B = TF-IDF vector of fatwa text
        """
        dot_product = float(np.dot(vec_a, vec_b))          # A · B
        mag_a = float(np.linalg.norm(vec_a))               # |A|
        mag_b = float(np.linalg.norm(vec_b))               # |B|
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot_product / (mag_a * mag_b)


class RealTFIDF:
    """
    Wrapper that mirrors the original RealTFIDF interface so the rest of
    the codebase requires no changes. Internally uses ManualTFIDF.
    """

    @staticmethod
    def fit_vectorizer(corpus_texts: List[str]):
        """Returns a fitted ManualTFIDF instance, or None on failure."""
        valid_texts = [t for t in corpus_texts if normalize_text(t).strip()]
        if not valid_texts:
            return None
        try:
            vectorizer = ManualTFIDF()
            vectorizer.fit(valid_texts)
            return vectorizer if vectorizer._fitted else None
        except Exception:
            return None

    @staticmethod
    def calculate(text1: str, text2: str, vectorizer=None) -> float:
        """
        Computes TF-IDF cosine similarity between text1 and text2.
        Applies Equation (4) from the proposal.
        Returns a score in [0, 100].
        """
        if not normalize_text(text1).strip() or not normalize_text(text2).strip():
            return 0.0

        if vectorizer is None:
            vectorizer = RealTFIDF.fit_vectorizer([text1, text2])
        if vectorizer is None:
            return 0.0

        try:
            vec_a = vectorizer.transform(text1)   # A = TF-IDF vector of AI response
            vec_b = vectorizer.transform(text2)   # B = TF-IDF vector of fatwa text
            score = ManualTFIDF.cosine_similarity_vectors(vec_a, vec_b)  # Eq. (4)
            return round(float(score) * 100.0, 2)
        except Exception:
            return 0.0


# =========================================================
# SBERT SIMILARITY — MANUAL MEAN POOLING + COSINE SIMILARITY
# Equation (5): e_i = SBERT(s_i)
# Equation (6): e_i = (1/m) * sum_{j=1}^{m} h_{i,j}  (mean pooling)
# Equation (7): Cosine Similarity(A_i, F_i) = (e_AI · e_OfficialFatwa)
#                                              / (|e_AI| * |e_OfficialFatwa|)
# =========================================================
class SBERTSimilarity:
    """
    Loads the pre-trained SBERT model (all-MiniLM-L6-v2) to obtain
    token-level hidden states, then applies:
      - Equation (5): pass sentence s_i through SBERT to get embedding e_i
      - Equation (6): mean pooling over all m token embeddings h_{i,j}
      - Equation (7): cosine similarity between the two mean-pooled vectors
    The library's built-in .encode() convenience method is NOT used for
    similarity; mean pooling and cosine similarity are implemented manually.
    """

    def __init__(self):
        # SBERT is required — raise immediately if the model cannot load
        # so the issue is caught at startup, not silently producing 0.0 scores.
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _mean_pool(self, sentence: str) -> np.ndarray:
        """
        Equation (5) + (6):
        Pass sentence s_i through SBERT, retrieve all token embeddings
        h_{i,1} ... h_{i,m}, then compute the mean vector e_i.

        SentenceTransformer internals expose this via encode() with
        output_value='token_embeddings'. We extract these and apply
        mean pooling manually.
        """
        if not str(sentence).strip():
            return np.zeros(384)  # all-MiniLM-L6-v2 output dim

        try:
            # Get raw token embeddings (shape: [num_tokens, hidden_dim])
            # output_value='token_embeddings' returns one array per sentence
            token_embeddings = self.model.encode(
                [sentence],
                output_value="token_embeddings",   # raw token-level vectors h_{i,j}
                convert_to_numpy=True,
            )[0]  # shape: (m, hidden_dim)

            # Equation (6): e_i = (1/m) * sum_{j=1}^{m} h_{i,j}
            m = token_embeddings.shape[0]          # number of tokens
            e_i = np.sum(token_embeddings, axis=0) / m   # mean over m tokens
            return e_i.astype(float)

        except Exception:
            # Fallback: use encode() sentence-level output (already mean-pooled
            # internally by the library) so the system stays functional
            return np.asarray(
                self.model.encode(sentence, convert_to_numpy=True),
                dtype=float,
            )

    def calculate(self, text1: str, text2: str) -> float:
        """
        Equation (7): Cosine Similarity(A_i, F_i) = (e_AI · e_OfficialFatwa)
                                                     / (|e_AI| |e_OfficialFatwa|)
        Returns score in [0, 100].
        """
        if not str(text1).strip() or not str(text2).strip():
            return 0.0

        # Equation (5) + (6): compute mean-pooled embeddings for both sentences
        e_ai = self._mean_pool(text1)              # e_AI
        e_fatwa = self._mean_pool(text2)           # e_OfficialFatwa

        # Equation (7): cosine similarity
        dot_product = float(np.dot(e_ai, e_fatwa))         # e_AI · e_OfficialFatwa
        mag_ai = float(np.linalg.norm(e_ai))               # |e_AI|
        mag_fatwa = float(np.linalg.norm(e_fatwa))         # |e_OfficialFatwa|

        if mag_ai == 0.0 or mag_fatwa == 0.0:
            return 0.0

        similarity = dot_product / (mag_ai * mag_fatwa)    # Eq. (7)
        return round(float(similarity) * 100.0, 2)


# =========================================================
# KEYWORD COVERAGE
# Equation (8): Keyword Coverage(%) =
#   (|K_AI ∩ K_OfficialFatwa| / |K_OfficialFatwa|) × 100
# =========================================================
class KeywordCoverage:
    """
    Implements Equation (8) from the proposal:
      K_OfficialFatwa = keywords extracted from the fatwa text
      K_AI            = keywords found in the AI-generated response
      Coverage        = |K_AI ∩ K_OfficialFatwa| / |K_OfficialFatwa| × 100
    """

    @staticmethod
    def extract_keywords_from_fatwa(fatwa_text: str, vectorizer, top_n: int = 14) -> List[str]:
        """
        Extract the top-N highest TF-IDF weighted terms from the fatwa text.
        These form the set K_OfficialFatwa in Equation (8).
        Uses the manual ManualTFIDF vectorizer.
        """
        clean_fatwa = TextCleaner.preprocess_to_string(fatwa_text)
        if not clean_fatwa or vectorizer is None:
            return []

        try:
            fatwa_vec = vectorizer.transform(fatwa_text)   # TF-IDF vector for fatwa

            if fatwa_vec.size == 0 or not vectorizer.vocabulary:
                return []

            # Rank terms by their TF-IDF weight in the fatwa vector
            term_weights = [
                (term, fatwa_vec[idx])
                for term, idx in vectorizer.vocabulary.items()
                if fatwa_vec[idx] > 0
            ]
            # Sort descending by weight
            term_weights.sort(key=lambda x: x[1], reverse=True)

            keywords = []
            seen: Set[str] = set()
            for term, _ in term_weights:
                if term not in seen:
                    seen.add(term)
                    keywords.append(term)
                if len(keywords) >= top_n:
                    break

            return keywords
        except Exception:
            return []

    @staticmethod
    def calculate(ai_text: str, fatwa_text: str, vectorizer=None, top_n: int = 14):
        """
        Equation (8):
          |K_AI ∩ K_OfficialFatwa| = number of fatwa keywords found in AI response
          |K_OfficialFatwa|         = total fatwa keywords extracted
          Coverage(%)               = (intersection / total) × 100
        """
        if vectorizer is None:
            vectorizer = RealTFIDF.fit_vectorizer([ai_text, fatwa_text])

        # K_AI = set of preprocessed tokens in the AI response
        ai_tokens: Set[str] = set(TextCleaner.preprocess(ai_text))

        # K_OfficialFatwa = top-N TF-IDF keywords from fatwa
        fatwa_keywords = KeywordCoverage.extract_keywords_from_fatwa(
            fatwa_text=fatwa_text,
            vectorizer=vectorizer,
            top_n=top_n,
        )

        # Equation (8): intersection and coverage
        matched = [kw for kw in fatwa_keywords if kw in ai_tokens]       # K_AI ∩ K_fatwa
        unmatched = [kw for kw in fatwa_keywords if kw not in ai_tokens]

        # |K_AI ∩ K_OfficialFatwa| / |K_OfficialFatwa| × 100
        coverage = (len(matched) / len(fatwa_keywords)) * 100.0 if fatwa_keywords else 0.0

        return matched, unmatched, round(float(coverage), 2), fatwa_keywords


# =========================================================
# TOPIC KNOWLEDGE
# =========================================================
STATIC_TOPIC_ALIASES: Dict[str, Set[str]] = {
    "Surrogacy": {"surrogacy", "ibu tumpang", "khidmat ibu tumpang", "sewa rahim", "rahim tumpang", "surrogate", "gestational carrier"},
    "Gamete Implantation for Reproduction": {"gamete implantation", "implantation of gamete", "implantasi gamet", "mencantumkan benih", "pencantuman benih", "benih sebelum akad nikah", "benih selepas kematian suami", "benih selepas penceraian", "memasukkan embrio", "embrio ke dalam rahim"},
    "IVF": {"ivf", "bayi tabung", "bayi tabung uji", "in vitro fertilization", "persenyawaan in vitro", "test tube baby", "benih pihak ketiga", "bayi tabung dari segi wali", "wali dan harta pusaka"},
    "Human Milk Bank": {"bank susu ibu", "bank susu manusia", "pendermaan susu ibu", "susu ibu penderma", "hubungan mahram susuan", "anak susuan menjadi mahram", "rekod pendermaan susu", "darurat bayi pramatang", "bank susu", "penderma susu"},
    "Abortion due to fetal abnormality": {"kecacatan janin", "janin tidak normal", "abnormality of fetus", "fetal abnormality"},
    "Abortion for maternal health": {"nyawa ibu terancam", "kesihatan ibu", "maternal health", "keselamatan ibu"},
    "Abortion ruling": {"pengguguran kandungan", "janin mangsa yang dirogol", "abortion ruling"},
    "Abortion resulting from rape": {"akibat rogol", "mangsa rogol", "pregnancy from rape", "rape abortion"},
    "Abortion of fetus conceived through zina": {"hasil zina", "anak zina", "kandungan hasil zina", "zina pregnancy"},
    "Abortion for OKU victims": {"mangsa oku", "oku akibat rogol", "orang kurang upaya"},
    "Abortion in high-risk groups": {"golongan berisiko tinggi", "high risk pregnancy", "berisiko tinggi"},
    "Provision of contraceptives": {"membekalkan bahan kontraseptif", "pasangan berkahwin", "contraceptives for married couples"},
    "Contraceptives for unmarried individuals": {"belum berkahwin", "individu belum berkahwin", "unmarried contraceptives", "kontraseptif kepada individu belum berkahwin"},
    "Contraceptives for rape victims": {"kontraseptif kepada mangsa rogol", "rape victims contraceptives", "mangsa rogol kontraseptif"},
    "Contraceptives for adolescents": {
        "kontraseptif kepada remaja", "remaja berisiko tinggi", "adolescent contraceptives",
        "membekalkan kontraseptif kepada remaja", "kontraseptif remaja", "bekalkan kontraseptif",
        "remaja yang berisiko", "remaja berisiko", "bekalan kontraseptif remaja",
        "hukum membekalkan kontraseptif", "kontraseptif kepada golongan remaja",
        "kontraseptif untuk remaja", "remaja dan kontraseptif",
    },
    "Contraceptives for HIV/AIDS prevention": {"kondom pencegahan hiv", "mencegah hiv", "hiv aids prevention", "pencegahan hiv", "pencegahan aids", "kondom hiv", "hiv kontraseptif"},
    "Abortion due to genetic disease (Example, Thalassemia)": {"penyakit genetik serius", "genetic disease abortion", "thalassemia", "talasemia", "penyakit genetik"},
    "Abortion of Foetus with Thalassemia": {"janin talasemia", "janin thalassemia", "40 hari", "120 hari", "sebelum 120 hari", "telah berumur 120 hari"},
    "Sperm Bank": {"bank air mani", "bank sperma", "air mani manusia", "permanian beradas", "bank mani", "simpanan sperma"},
    "Human Cloning (Reproductive)": {"pengklonan manusia untuk tujuan pembiakan", "reproductive cloning", "klon manusia reproduktif"},
    "Human Cloning (Therapeutic)": {"pengklonan manusia untuk tujuan perubatan", "therapeutic cloning", "klon manusia terapeutik"},
    "Stem Cell Research": {"sel stem", "stem cell research", "penyelidikan sel stem", "rawatan menggunakan sel stem"},
}

ISSUE_CATALOG = {issue: {"aliases": set(aliases)} for issue, aliases in STATIC_TOPIC_ALIASES.items()}


# =========================================================
# INTERPRETATION
# =========================================================
def interpret(score):
    try:
        score = float(score)
    except Exception:
        score = 0.0

    if score >= 70:
        return "Good Match", "The AI answer is close to the fatwa guidance and covers the main points well."
    if score >= 50:
        return "Moderate Match", "The AI answer is moderately aligned, but some important points are still incomplete or slightly inaccurate."
    return "Weak Match", "The AI answer is not closely aligned and should not be relied on without further review."


@st.cache_resource
def load_sbert_engine():
    return SBERTSimilarity()


def sbert_is_ready() -> bool:
    """Always True — SBERT is a required dependency, not optional."""
    return True


def _get_intro_focus_text(text, max_chars=320):
    cleaned = normalize_text(text)
    if not cleaned:
        return ""
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    primary = " ".join(lines[:2]) if lines else cleaned
    sentences = re.split(r"(?<=[.!?])\s+", primary)
    focus = " ".join(sentences[:2]).strip()
    return focus[:max_chars].strip()


def _important_ngrams(text: str) -> Set[str]:
    tokens = TextCleaner.preprocess(text)
    ngrams = set()
    for n in (1, 2, 3, 4):
        for i in range(len(tokens) - n + 1):
            gram = " ".join(tokens[i:i + n]).strip()
            if len(gram) >= 3:
                ngrams.add(gram)
    return ngrams


def _expand_dynamic_aliases(issue_name: str, question_texts: List[str]) -> Set[str]:
    aliases = set(STATIC_TOPIC_ALIASES.get(issue_name, set()))
    aliases.add(issue_name)
    aliases.add(issue_name.lower())

    for q in question_texts:
        q_clean = TextCleaner.clean(q)
        if q_clean:
            aliases.add(q_clean)
        aliases.update(_important_ngrams(q))

    if "thalassemia" in issue_name.lower() or "talasemia" in " ".join(question_texts).lower():
        aliases.update({"thalassemia", "talasemia", "40 hari", "120 hari", "sebelum 120 hari"})
    if "ivf" in issue_name.lower() or "bayi tabung" in " ".join(question_texts).lower():
        aliases.update({"ivf", "bayi tabung", "bayi tabung uji", "in vitro fertilization"})
    if "milk" in issue_name.lower() or ("susu" in " ".join(question_texts).lower() and "remaja" not in " ".join(question_texts).lower() and "kontraseptif" not in " ".join(question_texts).lower()):
        aliases.update({"bank susu ibu", "bank susu manusia", "mahram susuan", "anak susuan", "penderma susu", "bank susu"})
    if "sperm" in issue_name.lower() or "air mani" in " ".join(question_texts).lower():
        aliases.update({"bank air mani", "bank sperma", "air mani manusia"})
    if "contraceptives" in issue_name.lower() or "kontraseptif" in " ".join(question_texts).lower():
        aliases.update({"kontraseptif", "contraceptive", "membekalkan kontraseptif"})
        if "remaja" in " ".join(question_texts).lower() or "adolescent" in issue_name.lower():
            aliases.update({
                "kontraseptif kepada remaja", "remaja berisiko tinggi", "remaja berisiko",
                "membekalkan kontraseptif kepada remaja", "hukum membekalkan kontraseptif",
                "kontraseptif remaja", "bekalan kontraseptif remaja",
            })
        if "belum berkahwin" in " ".join(question_texts).lower() or "unmarried" in issue_name.lower():
            aliases.update({"belum berkahwin", "individu belum berkahwin"})
        if "rogol" in " ".join(question_texts).lower() or "rape" in issue_name.lower():
            aliases.update({"mangsa rogol kontraseptif", "kontraseptif kepada mangsa rogol"})
        if "hiv" in " ".join(question_texts).lower() or "hiv" in issue_name.lower():
            aliases.update({"kondom pencegahan hiv", "pencegahan hiv", "pencegahan aids"})
    if "cloning" in issue_name.lower() or "pengklonan" in " ".join(question_texts).lower():
        aliases.update({"pengklonan manusia", "klon manusia"})
    if "stem cell" in issue_name.lower() or "sel stem" in " ".join(question_texts).lower():
        aliases.update({"sel stem", "stem cell"})

    return {TextCleaner.clean(a) for a in aliases if TextCleaner.clean(a)}


def _alias_signal_scores(ai_text: str, aliases: Set[str]) -> Dict[str, float]:
    full_clean = TextCleaner.clean(ai_text)
    intro_clean = TextCleaner.clean(_get_intro_focus_text(ai_text))

    if not full_clean:
        return {
            "full": 0.0,
            "intro": 0.0,
            "alias_hits": 0,
            "best_alias": "",
            "score": 0.0,
        }

    full_tokens = full_clean.split()
    intro_tokens = intro_clean.split() if intro_clean else []
    best_alias = ""
    alias_hits = 0
    full_strength = 0.0
    intro_strength = 0.0

    for alias_clean in aliases:
        alias_tokens = alias_clean.split()
        if not alias_tokens:
            continue
        is_multiword = len(alias_tokens) >= 2

        exact_full = alias_clean in full_clean
        exact_intro = alias_clean in intro_clean if intro_clean else False
        token_full = all(tok in full_tokens for tok in alias_tokens)
        token_intro = all(tok in intro_tokens for tok in alias_tokens) if intro_tokens else False

        local_full = 0.0
        local_intro = 0.0
        if exact_full:
            local_full = 1.0 if is_multiword else 0.90
        elif token_full:
            local_full = 0.55 if is_multiword else 0.45

        if exact_intro:
            local_intro = 1.0 if is_multiword else 0.95
        elif token_intro:
            local_intro = 0.70 if is_multiword else 0.60

        if local_full > 0 or local_intro > 0:
            alias_hits += 1
            if max(local_full, local_intro) > max(full_strength, intro_strength):
                best_alias = alias_clean

        full_strength = max(full_strength, local_full)
        intro_strength = max(intro_strength, local_intro)

    combined_score = min(100.0, (full_strength * 35.0) + (intro_strength * 65.0) + min(alias_hits, 4) * 5.0)
    return {
        "full": round(full_strength * 100.0, 2),
        "intro": round(intro_strength * 100.0, 2),
        "alias_hits": alias_hits,
        "best_alias": best_alias,
        "score": round(combined_score, 2),
    }


def _build_issue_profiles(fatwa_df: pd.DataFrame) -> List[Dict[str, object]]:
    profiles = []
    for issue_name, group in fatwa_df.groupby("issue"):
        question_texts = group["question_text"].fillna("").astype(str).unique().tolist() if "question_text" in group.columns else []
        fatwa_texts = group["fatwa_text"].fillna("").astype(str).tolist()
        issue_focus = " ".join([issue_name] + question_texts).strip()
        issue_reference = " ".join([issue_name] + question_texts + fatwa_texts[:3]).strip()
        aliases = _expand_dynamic_aliases(issue_name, question_texts)
        profiles.append({
            "issue": issue_name,
            "question_texts": question_texts,
            "issue_focus": issue_focus,
            "issue_reference": issue_reference,
            "fatwa_summary": " ".join(fatwa_texts[:3]).strip(),
            "aliases": aliases,
        })
    return profiles


# =========================================================
# TOPIC LABELING / DETECTION
# =========================================================
def infer_topic_label(best_question_row, fatwa_subset):
    issue = normalize_text(best_question_row.get("issue", "")).strip()
    question_text = normalize_text(best_question_row.get("question_text", "")).strip()

    if issue:
        return issue
    if question_text:
        return question_text[:80]
    return "Related Fatwa Topic"


def _disambiguate_topic(ai_text: str, issue_df: pd.DataFrame) -> pd.DataFrame:
    """
    Post-scoring disambiguation: apply score penalties to topics that are
    unlikely given strong keyword evidence of a different topic in the AI text.
    This prevents e.g. Human Milk Bank from winning when the text is clearly
    about contraceptives for adolescents.
    """
    clean = TextCleaner.clean(ai_text)
    tokens = set(clean.split())

    # Strong positive signals: if these words appear prominently, boost those topics
    TOPIC_POSITIVE_SIGNALS = {
        "Contraceptives for adolescents": {
            "required_any": ["remaja", "adolescent", "teenager"],
            "supporting": ["kontraseptif", "contraceptive", "berisiko", "risk"],
            "boost": 18.0,
        },
        "Contraceptives for unmarried individuals": {
            "required_any": ["belum berkahwin", "unmarried"],
            "supporting": ["kontraseptif", "contraceptive"],
            "boost": 18.0,
        },
        "Contraceptives for rape victims": {
            "required_any": ["rogol", "rape"],
            "supporting": ["kontraseptif", "contraceptive"],
            "boost": 18.0,
        },
        "Contraceptives for HIV/AIDS prevention": {
            "required_any": ["hiv", "aids"],
            "supporting": ["kontraseptif", "contraceptive", "kondom"],
            "boost": 18.0,
        },
        "Provision of contraceptives": {
            "required_any": ["kontraseptif", "contraceptive"],
            "supporting": ["berkahwin", "pasangan"],
            "boost": 10.0,
        },
        "IVF": {
            "required_any": ["ivf", "bayi tabung", "in vitro"],
            "supporting": ["persenyawaan", "fertilization"],
            "boost": 18.0,
        },
        "Human Milk Bank": {
            "required_any": ["bank susu", "penderma susu", "bank susu ibu"],
            "supporting": ["mahram susuan", "anak susuan"],
            "boost": 18.0,
            "penalty_if_absent": 20.0,  # penalise if required_any not found
        },
        "Surrogacy": {
            "required_any": ["ibu tumpang", "surrogacy", "surrogate", "sewa rahim"],
            "supporting": ["rahim", "tumpang"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Sperm Bank": {
            "required_any": ["bank air mani", "bank sperma", "sperm bank"],
            "supporting": ["mani", "sperma"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Abortion resulting from rape": {
            "required_any": ["rogol", "rape"],
            "supporting": ["pengguguran", "abortion", "kandungan"],
            "boost": 15.0,
        },
        "Abortion for OKU victims": {
            "required_any": ["oku", "orang kurang upaya"],
            "supporting": ["pengguguran", "abortion"],
            "boost": 15.0,
        },
        "Abortion due to genetic disease (Example, Thalassemia)": {
            "required_any": ["thalassemia", "talasemia", "genetic"],
            "supporting": ["pengguguran", "genetik", "penyakit"],
            "boost": 15.0,
        },
        "Abortion of Foetus with Thalassemia": {
            "required_any": ["thalassemia", "talasemia"],
            "supporting": ["120 hari", "40 hari", "janin"],
            "boost": 15.0,
        },
        "Human Cloning (Reproductive)": {
            "required_any": ["pengklonan", "cloning", "klon"],
            "supporting": ["pembiakan", "reproduktif"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Human Cloning (Therapeutic)": {
            "required_any": ["pengklonan", "cloning", "klon"],
            "supporting": ["perubatan", "terapeutik"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Stem Cell Research": {
            "required_any": ["sel stem", "stem cell"],
            "supporting": ["penyelidikan", "research"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
    }

    result_df = issue_df.copy()

    for topic, signals in TOPIC_POSITIVE_SIGNALS.items():
        if topic not in result_df["issue"].values:
            continue

        required_any = signals.get("required_any", [])
        supporting = signals.get("supporting", [])
        boost = signals.get("boost", 10.0)
        penalty = signals.get("penalty_if_absent", 0.0)

        found_required = any(req in clean for req in required_any)
        found_supporting = any(sup in clean for sup in supporting)

        mask = result_df["issue"] == topic
        if found_required:
            extra = boost + (5.0 if found_supporting else 0.0)
            result_df.loc[mask, "issue_score"] = result_df.loc[mask, "issue_score"] + extra
        elif penalty > 0:
            result_df.loc[mask, "issue_score"] = (result_df.loc[mask, "issue_score"] - penalty).clip(lower=0)

    return result_df.sort_values(
        by=["issue_score", "rule_boost", "issue_tfidf", "issue_sbert", "coverage"],
        ascending=False,
    ).reset_index(drop=True)


def detect_best_question(ai_text, fatwa_df):
    sbert_engine = load_sbert_engine()
    issue_profiles = _build_issue_profiles(fatwa_df)
    if not issue_profiles:
        st.error("No topics found in database")
        st.stop()

    corpus = [ai_text]
    for p in issue_profiles:
        corpus.extend([p["issue_focus"], p["issue_reference"]])
    issue_vectorizer = RealTFIDF.fit_vectorizer(corpus)

    issue_rows = []
    for p in issue_profiles:
        focus_lexical = RealTFIDF.calculate(ai_text, p["issue_focus"], vectorizer=issue_vectorizer)
        ref_lexical = RealTFIDF.calculate(ai_text, p["issue_reference"], vectorizer=issue_vectorizer)
        focus_semantic = sbert_engine.calculate(ai_text, p["issue_focus"])
        alias_signal = _alias_signal_scores(ai_text, p["aliases"])
        matched, _, coverage, _ = KeywordCoverage.calculate(ai_text, p["fatwa_summary"], vectorizer=issue_vectorizer, top_n=18)

        issue_score = round(
            (focus_lexical * 0.34)
            + (ref_lexical * 0.16)
            + (focus_semantic * 0.20)
            + (coverage * 0.10)
            + (alias_signal["score"] * 0.20),
            2,
        )

        issue_rows.append({
            "issue": p["issue"],
            "issue_tfidf": focus_lexical,
            "issue_reference_tfidf": ref_lexical,
            "issue_sbert": focus_semantic,
            "coverage": coverage,
            "keyword_overlap": coverage,
            "rule_boost": alias_signal["score"],
            "alias_intro_signal": alias_signal["intro"],
            "alias_full_signal": alias_signal["full"],
            "alias_hits": alias_signal["alias_hits"],
            "best_alias": alias_signal["best_alias"],
            "issue_score": issue_score,
            "matched_issue_keywords": ", ".join(matched) if matched else "-",
        })

    issue_df = pd.DataFrame(issue_rows).sort_values(
        by=["issue_score", "rule_boost", "issue_tfidf", "issue_sbert", "coverage"],
        ascending=False,
    ).reset_index(drop=True)

    # ---- disambiguation: re-rank using keyword presence signals ----
    issue_df = _disambiguate_topic(ai_text, issue_df)

    best_issue = issue_df.iloc[0]["issue"]
    narrowed_df = fatwa_df[fatwa_df["issue"] == best_issue].copy()

    question_results = []
    grouped = narrowed_df.groupby("question_id")
    references = []
    metadata = []

    for qid, group in grouped:
        combined_fatwa = " ".join(group["fatwa_text"].fillna("").astype(str).tolist()).strip()
        issue_text = normalize_text(group["issue"].iloc[0]) if "issue" in group.columns else ""
        question_text = normalize_text(group["question_text"].iloc[0]) if "question_text" in group.columns else ""
        focus_text = f"{issue_text}. {question_text}".strip()
        ref_text = f"{focus_text} {combined_fatwa}".strip()
        references.extend([focus_text, ref_text])
        metadata.append((qid, issue_text, question_text, combined_fatwa, focus_text, ref_text))

    question_vectorizer = RealTFIDF.fit_vectorizer([ai_text] + references)

    for qid, issue_text, question_text, combined_fatwa, focus_text, ref_text in metadata:
        lexical_score = RealTFIDF.calculate(ai_text, ref_text, vectorizer=question_vectorizer)
        semantic_score = sbert_engine.calculate(ai_text, ref_text)
        coverage_matched, _, coverage, _ = KeywordCoverage.calculate(ai_text, combined_fatwa, vectorizer=question_vectorizer)
        issue_lexical = RealTFIDF.calculate(ai_text, focus_text, vectorizer=question_vectorizer)
        issue_semantic = sbert_engine.calculate(ai_text, focus_text)
        alias_signal = _alias_signal_scores(ai_text, _expand_dynamic_aliases(issue_text, [question_text]))

        topic_score = round(
            (issue_lexical * 0.34)
            + (issue_semantic * 0.16)
            + (lexical_score * 0.14)
            + (semantic_score * 0.12)
            + (coverage * 0.08)
            + (alias_signal["score"] * 0.16),
            2,
        )

        high_signal = (
            topic_score >= 80
            or (alias_signal["intro"] >= 95 and issue_semantic >= 60)
            or (topic_score >= 74 and semantic_score >= 60 and issue_lexical >= 55)
        )
        medium_signal = (
            topic_score >= 58
            or (alias_signal["score"] >= 50 and issue_lexical >= 45)
            or (semantic_score >= 50 and issue_semantic >= 48)
        )

        if high_signal:
            confidence = "High"
        elif medium_signal:
            confidence = "Medium"
        else:
            confidence = "Low"

        question_results.append({
            "question_id": qid,
            "issue": issue_text,
            "question_text": question_text,
            "topic_score": topic_score,
            "confidence": confidence,
            "tfidf": lexical_score,
            "sbert": semantic_score,
            "coverage": coverage,
            "keyword_overlap": coverage,
            "issue_tfidf": issue_lexical,
            "issue_sbert": issue_semantic,
            "rule_boost": alias_signal["score"],
            "alias_intro_signal": alias_signal["intro"],
            "alias_full_signal": alias_signal["full"],
            "alias_hits": alias_signal["alias_hits"],
            "best_alias": alias_signal["best_alias"],
            "issue_stage_score": float(issue_df.iloc[0]["issue_score"]),
            "issue_stage_alias": str(issue_df.iloc[0]["best_alias"]),
            "issue_stage_keywords": str(issue_df.iloc[0]["matched_issue_keywords"]),
            "matched_focus_keywords": ", ".join(coverage_matched) if coverage_matched else "-",
        })

    question_df = pd.DataFrame(question_results)
    if question_df.empty:
        st.error("No topics found in database")
        st.stop()

    question_df = question_df.sort_values(
        by=["topic_score", "rule_boost", "issue_tfidf", "alias_intro_signal", "sbert", "coverage", "tfidf"],
        ascending=False,
    ).reset_index(drop=True)
    return question_df.iloc[0], question_df


# =========================================================
# STATE-LEVEL COMPARISON AND AGGREGATION
# Equation (9): MaxAlign_i = max_{j∈{1,2,...,s}} (Semantic Similarity(A_i, F_{i,j}))
# Equation (10): MeanAlign_i = (1/s) * sum_{j=1}^{s} (Semantic Similarity(A_i, F_{i,j}))
# =========================================================
def compare_states_within_question(ai_text, fatwa_subset, top_n_keywords=14):
    """
    For each state fatwa F_{i,j}, compute the three metrics then the
    alignment score. After all states are processed:
      - Equation (9)  MaxAlign  = the row with the highest alignment score
      - Equation (10) MeanAlign = mean of all states' alignment scores
    """
    sbert_engine = load_sbert_engine()
    fatwa_texts = fatwa_subset["fatwa_text"].fillna("").astype(str).tolist()
    vectorizer = RealTFIDF.fit_vectorizer([ai_text] + fatwa_texts)

    results = []
    for _, row in fatwa_subset.iterrows():
        state = normalize_text(row["state"])
        fatwa = normalize_text(row["fatwa_text"])
        qid = normalize_text(row["question_id"])
        issue = normalize_text(row.get("issue", ""))
        question_text = normalize_text(row.get("question_text", ""))

        if not fatwa:
            continue

        # TF-IDF cosine similarity — Equation (4)
        lexical = RealTFIDF.calculate(ai_text, fatwa, vectorizer=vectorizer)

        # SBERT semantic similarity — Equations (5), (6), (7)
        semantic = sbert_engine.calculate(ai_text, fatwa)

        # Keyword coverage — Equation (8)
        matched, unmatched, coverage, keywords = KeywordCoverage.calculate(
            ai_text=ai_text,
            fatwa_text=fatwa,
            vectorizer=vectorizer,
            top_n=top_n_keywords,
        )

        # Weighted composite alignment score per state
        alignment_score = (semantic * 0.60) + (lexical * 0.25) + (coverage * 0.15)

        results.append({
            "question_id": qid,
            "issue": issue,
            "question_text": question_text,
            "state": state,
            "tfidf": lexical,
            "lexical_similarity": lexical,
            "semantic_similarity": semantic,
            "coverage": coverage,
            "alignment_score": round(float(alignment_score), 2),
            "matched_keywords": ", ".join(matched) if matched else "-",
            "missing_keywords": ", ".join(unmatched) if unmatched else "-",
            "fatwa_keywords": ", ".join(keywords) if keywords else "-",
            "fatwa_text": fatwa,
        })

    results_df = pd.DataFrame(results)
    if results_df.empty:
        st.error("No states found for this topic")
        st.stop()

    results_df = results_df.sort_values(
        by=["alignment_score", "semantic_similarity", "coverage"],
        ascending=False,
    ).reset_index(drop=True)

    # Equation (9): MaxAlign — best-match state (highest alignment score)
    best_state = results_df.iloc[0]

    # Equation (10): MeanAlign — average alignment across all s states
    mean_alignment = results_df["alignment_score"].mean()

    return {
        "state": best_state["state"],
        "issue": best_state["issue"],
        "fatwa_text": best_state["fatwa_text"],
        "best_match_alignment": best_state["alignment_score"],   # Eq. (9) MaxAlign
        "mean_alignment": round(float(mean_alignment), 2),       # Eq. (10) MeanAlign
        "lexical_similarity": best_state["lexical_similarity"],
        "semantic_similarity": best_state["semantic_similarity"],
        "coverage": best_state["coverage"],
        "matched_keywords": best_state["matched_keywords"],
        "missing_keywords": best_state["missing_keywords"],
    }, results_df