# =========================================================
# scoring.py  —  NLP scoring engine for the FYP Dashboard
# =========================================================
# Implements the three similarity metrics described in the
# Final-Year Project proposal:
#
#   Equation (4)  TF-IDF cosine similarity        (RealTFIDF)
#   Equations (5–7)  SBERT mean-pooled cosine     (SBERTSimilarity)
#   Equation (8)  Keyword coverage                (KeywordCoverage)
#
# The composite alignment score used in the dashboard is:
#   alignment = 0.60 × SBERT + 0.25 × TF-IDF + 0.15 × coverage
#
# SBERT is a required dependency.  Missing it raises immediately
# so the problem is visible at startup rather than silently
# producing wrong (zero) scores.
# =========================================================

import math
import re
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer

from utils import normalize_text, get_score_tier, get_score_tier_colors, get_score_css_class

SBERT_AVAILABLE = True  # Always True — import above raises if missing


# =========================================================
# TEXT PROCESSING
# =========================================================

class TextCleaner:
    """
    Lightweight text pre-processor: clean → tokenise → remove stopwords.

    No external NLP library is required; everything is done with
    Python builtins and regular expressions.
    """

    # General English + Malay stopwords
    DEFAULT_STOPWORDS: Set[str] = {
        # English
        "the", "a", "an", "and", "of", "to", "is", "in", "on", "for", "with",
        "that", "this", "it", "as", "are", "was", "were", "be", "by", "or",
        "from", "at", "which", "can", "may", "should", "would", "will", "if",
        "about", "into", "than", "then", "also", "such", "their", "there",
        "these", "those", "has", "have", "had", "but", "not", "no", "yes",
        # Malay
        "dan", "atau", "yang", "di", "ke", "dengan", "untuk", "pada", "adalah",
        "ialah", "ini", "itu", "dalam", "oleh", "sebagai", "bagi", "jika",
        "maka", "sahaja", "agar", "supaya", "kerana", "daripada", "kepada",
        "masih", "telah", "akan", "boleh", "tidak", "ya", "lebih", "kurang",
        "semasa", "selepas", "sebelum", "antara", "setelah", "serta", "juga",
        "bukan", "lagi", "satu", "dua", "tiga", "rawatan", "proses",
        "menurut", "islam", "hukum", "apakah", "ringkasnya", "kesimpulan",
        "contoh", "status", "menjadi", "berhak", "sah", "dibenarkan",
        "ulama", "fatwa", "malaysia", "jelas", "tegas",
    }

    # Domain-specific terms that must NOT be removed as stopwords
    DOMAIN_KEEPWORDS: Set[str] = {
        "ivf", "iui", "icsi", "art", "fatwa", "hukum", "harus", "haram",
        "bayi", "tabung", "uji", "sperma", "ovum", "embrio", "rahim",
        "surrogacy", "nasab", "ibu", "tumpang", "penderma", "suami", "isteri",
        "zuriat", "persenyawaan", "donor", "abortion", "pengguguran",
        "mani", "bank", "air", "bankairmani", "spermbank", "ketiga",
        "halal", "syariah", "syarak", "perkahwinan", "wali", "pusaka", "benih",
        "carrier", "surrogate", "susu", "susuan", "mahram", "radhaah", "radha",
        "penyusuan", "milk", "klon", "cloning", "stem", "cell", "sel",
        "terapeutik", "reproduktif", "rogol", "rape", "zina", "thalassemia",
        "talasemia", "genetic", "genetik", "kontraseptif", "contraceptive",
        "hiv", "aids", "oku", "janin", "foetus", "fetus", "kandungan",
        "maternal", "kesihatan", "kondom", "mahram", "pembiakan", "perubatan",
    }

    @staticmethod
    def clean(text: str) -> str:
        """Lower-case, strip URLs/punctuation, collapse whitespace."""
        text = normalize_text(text).lower()
        text = re.sub(r"http\S+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s\-/]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Manual tokenisation — no external library dependency.

        Splits on whitespace, then expands hyphenated and slash-separated
        compound tokens so both the parts and the joined form are indexed.
        """
        cleaned = TextCleaner.clean(text)
        if not cleaned:
            return []

        raw_tokens = cleaned.split()
        normalised: List[str] = []

        for token in raw_tokens:
            token = token.strip().lower()
            if not token:
                continue

            # Hyphen: "in-vitro" → ["in", "vitro", "invitro", "in-vitro"]
            if "-" in token:
                parts = [p for p in token.split("-") if p]
                normalised.extend(parts)
                normalised.append(token.replace("-", ""))

            # Slash: "HIV/AIDS" → ["HIV", "AIDS", "HIVAIDS", "HIV/AIDS"]
            if "/" in token:
                parts = [p for p in token.split("/") if p]
                normalised.extend(parts)
                normalised.append(token.replace("/", ""))

            normalised.append(token)

        return normalised

    @staticmethod
    def remove_stopwords(tokens: List[str]) -> List[str]:
        """
        Remove stopwords from a token list.

        Domain keep-words are never removed, even if they appear in the
        DEFAULT_STOPWORDS set (they don't currently, but this guard is safe).
        Single-character tokens are always removed.
        """
        filtered: List[str] = []
        for token in tokens:
            if len(token) <= 1:
                continue
            # Keep domain keywords unconditionally
            if token in TextCleaner.DOMAIN_KEEPWORDS:
                filtered.append(token)
                continue
            # Remove general stopwords
            if token not in TextCleaner.DEFAULT_STOPWORDS:
                filtered.append(token)
        return filtered

    @staticmethod
    def preprocess(text: str) -> List[str]:
        """Tokenise and remove stopwords, returning a token list."""
        return TextCleaner.remove_stopwords(TextCleaner.tokenize(text))

    @staticmethod
    def preprocess_to_string(text: str) -> str:
        """Preprocess and join tokens back into a single string."""
        return " ".join(TextCleaner.preprocess(text))


# =========================================================
# MANUAL TF-IDF IMPLEMENTATION
# Equation (4): Cosine Similarity(A, B) = (A·B) / (|A|·|B|)
# where A and B are TF-IDF vectors of the two texts.
# =========================================================

class ManualTFIDF:
    """
    Manual TF-IDF implementation — no scikit-learn required.

    Term Frequency  : TF(t, d)  = count(t in d) / |d|
    Inverse Doc Freq: IDF(t)    = log((N+1)/(df+1)) + 1   (smoothed)
    Vector weight   : w(t, d)   = TF(t, d) × IDF(t)
    Cosine similarity: (A·B) / (|A|·|B|)   — Equation (4)
    """

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self._fitted = False

    def fit(self, corpus: List[str]) -> "ManualTFIDF":
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

        # Build vocabulary from all unique terms
        vocab_set: Set[str] = set()
        for doc in cleaned_corpus:
            vocab_set.update(doc.split())
        self.vocabulary = {term: idx for idx, term in enumerate(sorted(vocab_set))}

        # Document frequency: how many documents contain each term
        df: Dict[str, int] = {term: 0 for term in self.vocabulary}
        for doc in cleaned_corpus:
            present = set(doc.split())
            for term in present:
                if term in df:
                    df[term] += 1

        # Smoothed IDF: log((N+1)/(df+1)) + 1  → avoids zero-division
        self.idf = {
            term: math.log((N + 1) / (df[term] + 1)) + 1.0
            for term in self.vocabulary
        }

        self._fitted = True
        return self

    def transform(self, text: str) -> np.ndarray:
        """
        Convert a document into a TF-IDF weight vector.

        TF(t) = count(t) / total_tokens
        w(t)  = TF(t) × IDF(t)
        """
        if not self._fitted or not self.vocabulary:
            return np.zeros(1)

        cleaned = TextCleaner.preprocess_to_string(text)
        tokens = cleaned.split()
        total_terms = len(tokens) if tokens else 1

        # Term frequency counts
        tf: Dict[str, float] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        for term in tf:
            tf[term] /= total_terms

        # Build the weight vector
        vec = np.zeros(len(self.vocabulary))
        for term, idx in self.vocabulary.items():
            if term in tf:
                vec[idx] = tf[term] * self.idf[term]

        return vec

    @staticmethod
    def cosine_similarity_vectors(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Equation (4): Cosine Similarity = (A·B) / (|A|·|B|)

        Returns 0.0 when either vector is the zero vector.
        """
        dot   = float(np.dot(vec_a, vec_b))
        mag_a = float(np.linalg.norm(vec_a))
        mag_b = float(np.linalg.norm(vec_b))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)


class RealTFIDF:
    """
    Public interface used by the rest of the codebase.
    Wraps ManualTFIDF so callers stay unchanged if the backend changes.
    """

    @staticmethod
    def fit_vectorizer(corpus_texts: List[str]):
        """Fit and return a ManualTFIDF instance, or None on failure."""
        valid = [t for t in corpus_texts if normalize_text(t).strip()]
        if not valid:
            return None
        try:
            v = ManualTFIDF()
            v.fit(valid)
            return v if v._fitted else None
        except Exception:
            return None

    @staticmethod
    def calculate(text1: str, text2: str, vectorizer=None) -> float:
        """
        TF-IDF cosine similarity between text1 and text2 — Equation (4).

        Returns a value in [0, 100].  Fits a fresh vectorizer when none
        is supplied (less efficient, but always correct).
        """
        if not normalize_text(text1).strip() or not normalize_text(text2).strip():
            return 0.0

        if vectorizer is None:
            vectorizer = RealTFIDF.fit_vectorizer([text1, text2])
        if vectorizer is None:
            return 0.0

        try:
            vec_a = vectorizer.transform(text1)
            vec_b = vectorizer.transform(text2)
            raw   = ManualTFIDF.cosine_similarity_vectors(vec_a, vec_b)
            return round(float(raw) * 100.0, 2)
        except Exception:
            return 0.0


# =========================================================
# SBERT SIMILARITY — MEAN POOLING + COSINE
# Equation (5): e_i = SBERT(s_i)
# Equation (6): e_i = (1/m) Σ h_{i,j}   (mean pooling)
# Equation (7): Cosine(A_i, F_i) = (e_AI · e_Fatwa) / (|e_AI|·|e_Fatwa|)
# =========================================================

class SBERTSimilarity:
    """
    Wraps the all-MiniLM-L6-v2 SBERT model and exposes a single
    .calculate(text1, text2) → float[0,100] method.

    Mean pooling and cosine similarity are computed manually to match
    Equations (5)–(7) from the proposal.
    """

    def __init__(self):
        # Raise immediately if the model cannot load — don't silently return 0s
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _mean_pool(self, sentence: str) -> np.ndarray:
        """
        Equations (5) + (6):
        Encode sentence s_i through SBERT, extract all m token embeddings
        h_{i,1} … h_{i,m}, then compute the mean e_i = (1/m) Σ h_{i,j}.
        """
        if not str(sentence).strip():
            return np.zeros(384)  # all-MiniLM-L6-v2 hidden size

        try:
            # output_value='token_embeddings' → list of one array per sentence
            token_embeddings = self.model.encode(
                [sentence],
                output_value="token_embeddings",
                convert_to_numpy=True,
            )[0]  # shape: (m, 384)

            # Equation (6): e_i = mean over m token vectors
            m = token_embeddings.shape[0]
            return (np.sum(token_embeddings, axis=0) / m).astype(float)

        except Exception:
            # Fallback: use the library's built-in sentence-level output
            return np.asarray(
                self.model.encode(sentence, convert_to_numpy=True),
                dtype=float,
            )

    def calculate(self, text1: str, text2: str) -> float:
        """
        Equation (7): Cosine(A_i, F_i) = (e_AI · e_Fatwa) / (|e_AI|·|e_Fatwa|)

        Returns a score in [0, 100].
        """
        if not str(text1).strip() or not str(text2).strip():
            return 0.0

        e_ai    = self._mean_pool(text1)   # e_AI    — Eqs (5)+(6)
        e_fatwa = self._mean_pool(text2)   # e_Fatwa — Eqs (5)+(6)

        dot     = float(np.dot(e_ai, e_fatwa))
        mag_ai  = float(np.linalg.norm(e_ai))
        mag_f   = float(np.linalg.norm(e_fatwa))

        if mag_ai == 0.0 or mag_f == 0.0:
            return 0.0

        similarity = dot / (mag_ai * mag_f)   # Equation (7)
        return round(float(similarity) * 100.0, 2)


# =========================================================
# KEYWORD COVERAGE
# Equation (8): Coverage = |K_AI ∩ K_Fatwa| / |K_Fatwa| × 100
# =========================================================

class KeywordCoverage:
    """
    Implements Equation (8):
      K_Fatwa = top-N TF-IDF keywords extracted from the official fatwa
      K_AI    = tokens present in the AI-generated response
      Coverage = |K_AI ∩ K_Fatwa| / |K_Fatwa| × 100
    """

    @staticmethod
    def extract_keywords_from_fatwa(
        fatwa_text: str,
        vectorizer,
        top_n: int = 14,
    ) -> List[str]:
        """
        Extract the top-N highest-weighted terms from the fatwa TF-IDF vector.
        These form the set K_Fatwa in Equation (8).
        """
        if not TextCleaner.preprocess_to_string(fatwa_text) or vectorizer is None:
            return []

        try:
            fatwa_vec = vectorizer.transform(fatwa_text)
            if fatwa_vec.size == 0 or not vectorizer.vocabulary:
                return []

            # Rank terms by their TF-IDF weight in this fatwa
            term_weights = [
                (term, fatwa_vec[idx])
                for term, idx in vectorizer.vocabulary.items()
                if fatwa_vec[idx] > 0
            ]
            term_weights.sort(key=lambda x: x[1], reverse=True)

            # Deduplicate while preserving rank order
            keywords: List[str] = []
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
    def calculate(
        ai_text: str,
        fatwa_text: str,
        vectorizer=None,
        top_n: int = 14,
    ) -> Tuple[List[str], List[str], float, List[str]]:
        """
        Equation (8): Coverage = |K_AI ∩ K_Fatwa| / |K_Fatwa| × 100

        Returns:
            matched   — fatwa keywords found in the AI response
            unmatched — fatwa keywords NOT found in the AI response
            coverage  — percentage (0–100)
            keywords  — full K_Fatwa list (for display)
        """
        if vectorizer is None:
            vectorizer = RealTFIDF.fit_vectorizer([ai_text, fatwa_text])

        # K_AI: set of pre-processed tokens from the AI response
        ai_tokens: Set[str] = set(TextCleaner.preprocess(ai_text))

        # K_Fatwa: top-N TF-IDF keywords from the fatwa
        fatwa_keywords = KeywordCoverage.extract_keywords_from_fatwa(
            fatwa_text=fatwa_text,
            vectorizer=vectorizer,
            top_n=top_n,
        )

        matched   = [kw for kw in fatwa_keywords if kw in ai_tokens]
        unmatched = [kw for kw in fatwa_keywords if kw not in ai_tokens]
        coverage  = (len(matched) / len(fatwa_keywords)) * 100.0 if fatwa_keywords else 0.0

        return matched, unmatched, round(float(coverage), 2), fatwa_keywords


# =========================================================
# TOPIC KNOWLEDGE — STATIC ALIAS TABLE
# =========================================================

STATIC_TOPIC_ALIASES: Dict[str, Set[str]] = {
    "Surrogacy": {
        "surrogacy", "ibu tumpang", "khidmat ibu tumpang", "sewa rahim",
        "rahim tumpang", "surrogate", "gestational carrier",
    },
    "Gamete Implantation for Reproduction": {
        "gamete implantation", "implantation of gamete", "implantasi gamet",
        "mencantumkan benih", "pencantuman benih", "benih sebelum akad nikah",
        "benih selepas kematian suami", "benih selepas penceraian",
        "memasukkan embrio", "embrio ke dalam rahim",
    },
    "IVF": {
        "ivf", "bayi tabung", "bayi tabung uji", "in vitro fertilization",
        "persenyawaan in vitro", "test tube baby", "benih pihak ketiga",
        "bayi tabung dari segi wali", "wali dan harta pusaka",
    },
    "Human Milk Bank": {
        "bank susu ibu", "bank susu manusia", "pendermaan susu ibu",
        "susu ibu penderma", "hubungan mahram susuan", "anak susuan menjadi mahram",
        "rekod pendermaan susu", "darurat bayi pramatang", "bank susu",
        "penderma susu",
    },
    "Abortion due to fetal abnormality": {
        "kecacatan janin", "janin tidak normal", "abnormality of fetus",
        "fetal abnormality",
    },
    "Abortion for maternal health": {
        "nyawa ibu terancam", "kesihatan ibu", "maternal health",
        "keselamatan ibu",
    },
    "Abortion ruling": {
        "pengguguran kandungan", "janin mangsa yang dirogol", "abortion ruling",
    },
    "Abortion resulting from rape": {
        "akibat rogol", "mangsa rogol", "pregnancy from rape", "rape abortion",
    },
    "Abortion of fetus conceived through zina": {
        "hasil zina", "anak zina", "kandungan hasil zina", "zina pregnancy",
    },
    "Abortion for OKU victims": {
        "mangsa oku", "oku akibat rogol", "orang kurang upaya",
    },
    "Abortion in high-risk groups": {
        "golongan berisiko tinggi", "high risk pregnancy", "berisiko tinggi",
    },
    "Provision of contraceptives": {
        "membekalkan bahan kontraseptif", "pasangan berkahwin",
        "contraceptives for married couples",
    },
    "Contraceptives for unmarried individuals": {
        "belum berkahwin", "individu belum berkahwin", "unmarried contraceptives",
        "kontraseptif kepada individu belum berkahwin",
    },
    "Contraceptives for rape victims": {
        "kontraseptif kepada mangsa rogol", "rape victims contraceptives",
        "mangsa rogol kontraseptif",
    },
    "Contraceptives for adolescents": {
        "kontraseptif kepada remaja", "remaja berisiko tinggi",
        "adolescent contraceptives", "membekalkan kontraseptif kepada remaja",
        "kontraseptif remaja", "bekalkan kontraseptif", "remaja yang berisiko",
        "remaja berisiko", "bekalan kontraseptif remaja",
        "hukum membekalkan kontraseptif", "kontraseptif kepada golongan remaja",
        "kontraseptif untuk remaja", "remaja dan kontraseptif",
    },
    "Contraceptives for HIV/AIDS prevention": {
        "kondom pencegahan hiv", "mencegah hiv", "hiv aids prevention",
        "pencegahan hiv", "pencegahan aids", "kondom hiv", "hiv kontraseptif",
    },
    "Abortion due to genetic disease (Example, Thalassemia)": {
        "penyakit genetik serius", "genetic disease abortion", "thalassemia",
        "talasemia", "penyakit genetik",
    },
    "Abortion of Foetus with Thalassemia": {
        "janin talasemia", "janin thalassemia", "40 hari", "120 hari",
        "sebelum 120 hari", "telah berumur 120 hari",
    },
    "Sperm Bank": {
        "bank air mani", "bank sperma", "air mani manusia",
        "permanian beradas", "bank mani", "simpanan sperma",
    },
    "Human Cloning (Reproductive)": {
        "pengklonan manusia untuk tujuan pembiakan", "reproductive cloning",
        "klon manusia reproduktif",
    },
    "Human Cloning (Therapeutic)": {
        "pengklonan manusia untuk tujuan perubatan", "therapeutic cloning",
        "klon manusia terapeutik",
    },
    "Stem Cell Research": {
        "sel stem", "stem cell research", "penyelidikan sel stem",
        "rawatan menggunakan sel stem",
    },
}

ISSUE_CATALOG = {
    issue: {"aliases": set(aliases)}
    for issue, aliases in STATIC_TOPIC_ALIASES.items()
}


# =========================================================
# INTERPRETATION HELPER
# =========================================================

def interpret(score) -> Tuple[str, str]:
    """
    Convert a numeric score into a (label, explanation) pair.

    Thresholds (aligned with proposal):
        High Alignment     >= 70  — green  (Reliable)
        Moderate Alignment >= 40  — orange (Moderate)
        Low Alignment       < 40  — red    (Not Reliable)
    """
    try:
        score = float(score)
    except Exception:
        score = 0.0

    if score >= 70:
        return (
            "High Alignment",
            "The AI answer closely matches the fatwa guidance and covers the main ruling points well. This response is considered reliable.",
        )
    if score >= 40:
        return (
            "Moderate Alignment",
            "The AI answer is partially aligned with the fatwa. Some key rulings or conditions are missing or imprecise — review before relying on this response.",
        )
    return (
        "Low Alignment",
        "The AI answer does not closely match the fatwa guidance. It should not be relied on without significant correction and review.",
    )


# =========================================================
# SBERT LOADER (cached so the model loads only once per session)
# =========================================================

@st.cache_resource
def load_sbert_engine() -> SBERTSimilarity:
    """Load the SBERT model once and reuse it across all calls."""
    return SBERTSimilarity()


def sbert_is_ready() -> bool:
    """Always True — SBERT is a required dependency."""
    return True


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _get_intro_focus_text(text: str, max_chars: int = 320) -> str:
    """
    Extract the first two sentences of a text as a short 'intro'
    for higher-precision alias matching.
    """
    cleaned = normalize_text(text)
    if not cleaned:
        return ""
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    primary = " ".join(lines[:2]) if lines else cleaned
    sentences = re.split(r"(?<=[.!?])\s+", primary)
    return " ".join(sentences[:2]).strip()[:max_chars]


def _important_ngrams(text: str) -> Set[str]:
    """Build 1–4-gram set from preprocessed tokens (minimum 3-char grams)."""
    tokens = TextCleaner.preprocess(text)
    ngrams: Set[str] = set()
    for n in (1, 2, 3, 4):
        for i in range(len(tokens) - n + 1):
            gram = " ".join(tokens[i:i + n]).strip()
            if len(gram) >= 3:
                ngrams.add(gram)
    return ngrams


def _expand_dynamic_aliases(issue_name: str, question_texts: List[str]) -> Set[str]:
    """
    Build the full alias set for a topic by combining:
      1. Static aliases from STATIC_TOPIC_ALIASES
      2. The issue name itself
      3. Cleaned question text and its n-grams
      4. Topic-specific heuristic expansions
    """
    aliases: Set[str] = set(STATIC_TOPIC_ALIASES.get(issue_name, set()))
    aliases.add(issue_name)
    aliases.add(issue_name.lower())

    for q in question_texts:
        q_clean = TextCleaner.clean(q)
        if q_clean:
            aliases.add(q_clean)
        aliases.update(_important_ngrams(q))

    q_joined = " ".join(question_texts).lower()

    # Topic-specific extra aliases
    if "thalassemia" in issue_name.lower() or "talasemia" in q_joined:
        aliases.update({"thalassemia", "talasemia", "40 hari", "120 hari", "sebelum 120 hari"})

    if "ivf" in issue_name.lower() or "bayi tabung" in q_joined:
        aliases.update({"ivf", "bayi tabung", "bayi tabung uji", "in vitro fertilization"})

    if "milk" in issue_name.lower() or (
        "susu" in q_joined and "remaja" not in q_joined and "kontraseptif" not in q_joined
    ):
        aliases.update({
            "bank susu ibu", "bank susu manusia", "mahram susuan",
            "anak susuan", "penderma susu", "bank susu",
        })

    if "sperm" in issue_name.lower() or "air mani" in q_joined:
        aliases.update({"bank air mani", "bank sperma", "air mani manusia"})

    if "contraceptives" in issue_name.lower() or "kontraseptif" in q_joined:
        aliases.update({"kontraseptif", "contraceptive", "membekalkan kontraseptif"})

        if "remaja" in q_joined or "adolescent" in issue_name.lower():
            aliases.update({
                "kontraseptif kepada remaja", "remaja berisiko tinggi",
                "remaja berisiko", "membekalkan kontraseptif kepada remaja",
                "hukum membekalkan kontraseptif", "kontraseptif remaja",
                "bekalan kontraseptif remaja",
            })

        if "belum berkahwin" in q_joined or "unmarried" in issue_name.lower():
            aliases.update({"belum berkahwin", "individu belum berkahwin"})

        if "rogol" in q_joined or "rape" in issue_name.lower():
            aliases.update({"mangsa rogol kontraseptif", "kontraseptif kepada mangsa rogol"})

        if "hiv" in q_joined or "hiv" in issue_name.lower():
            aliases.update({"kondom pencegahan hiv", "pencegahan hiv", "pencegahan aids"})

    if "cloning" in issue_name.lower() or "pengklonan" in q_joined:
        aliases.update({"pengklonan manusia", "klon manusia"})

    if "stem cell" in issue_name.lower() or "sel stem" in q_joined:
        aliases.update({"sel stem", "stem cell"})

    return {TextCleaner.clean(a) for a in aliases if TextCleaner.clean(a)}


def _alias_signal_scores(ai_text: str, aliases: Set[str]) -> Dict[str, float]:
    """
    Score how strongly the AI text matches a topic's alias set.

    Checks both the full text and the intro section separately so that
    aliases appearing near the start of the answer score higher.

    Returns a dict with keys:
        full       — strength over the full text  (0–100)
        intro      — strength over intro only     (0–100)
        alias_hits — number of aliases matched
        best_alias — the alias that scored highest
        score      — composite signal score       (0–100)
    """
    full_clean  = TextCleaner.clean(ai_text)
    intro_clean = TextCleaner.clean(_get_intro_focus_text(ai_text))

    if not full_clean:
        return {"full": 0.0, "intro": 0.0, "alias_hits": 0, "best_alias": "", "score": 0.0}

    full_tokens  = full_clean.split()
    intro_tokens = intro_clean.split() if intro_clean else []
    best_alias   = ""
    alias_hits   = 0
    full_strength  = 0.0
    intro_strength = 0.0

    for alias_clean in aliases:
        alias_tokens  = alias_clean.split()
        if not alias_tokens:
            continue
        is_multiword = len(alias_tokens) >= 2

        exact_full  = alias_clean in full_clean
        exact_intro = alias_clean in intro_clean if intro_clean else False
        token_full  = all(tok in full_tokens for tok in alias_tokens)
        token_intro = (all(tok in intro_tokens for tok in alias_tokens)
                       if intro_tokens else False)

        local_full = local_intro = 0.0

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

        full_strength  = max(full_strength,  local_full)
        intro_strength = max(intro_strength, local_intro)

    composite = min(
        100.0,
        full_strength * 35.0 + intro_strength * 65.0 + min(alias_hits, 4) * 5.0,
    )
    return {
        "full":       round(full_strength  * 100.0, 2),
        "intro":      round(intro_strength * 100.0, 2),
        "alias_hits": alias_hits,
        "best_alias": best_alias,
        "score":      round(composite, 2),
    }


def _build_issue_profiles(fatwa_df: pd.DataFrame) -> List[Dict[str, object]]:
    """
    Build one profile dict per issue (topic) in the fatwa database.
    Each profile bundles all information needed for the first-stage
    topic-detection scoring.
    """
    profiles = []
    for issue_name, group in fatwa_df.groupby("issue"):
        question_texts = (
            group["question_text"].fillna("").astype(str).unique().tolist()
            if "question_text" in group.columns
            else []
        )
        fatwa_texts  = group["fatwa_text"].fillna("").astype(str).tolist()
        issue_focus  = " ".join([issue_name] + question_texts).strip()
        issue_ref    = " ".join([issue_name] + question_texts + fatwa_texts[:3]).strip()
        aliases      = _expand_dynamic_aliases(issue_name, question_texts)

        profiles.append({
            "issue":         issue_name,
            "question_texts": question_texts,
            "issue_focus":   issue_focus,
            "issue_reference": issue_ref,
            "fatwa_summary": " ".join(fatwa_texts[:3]).strip(),
            "aliases":       aliases,
        })
    return profiles


# =========================================================
# TOPIC LABELING
# =========================================================

def infer_topic_label(best_question_row: dict, fatwa_subset: pd.DataFrame) -> str:
    """
    Return the best human-readable label for the detected topic.

    Priority: issue field → question text → fallback string.
    """
    issue = normalize_text(best_question_row.get("issue", "")).strip()
    if issue:
        return issue
    question_text = normalize_text(best_question_row.get("question_text", "")).strip()
    if question_text:
        return question_text[:80]
    return "Related Fatwa Topic"


# =========================================================
# TOPIC DISAMBIGUATION
# =========================================================

def _disambiguate_topic(ai_text: str, issue_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adjust issue scores after the initial ranking using keyword signals.

    Topics with strong positive keyword signals get a score boost;
    topics that require specific keywords which are absent get a penalty.
    This prevents topic confusion where e.g. "Human Milk Bank" outranks
    "Contraceptives for adolescents" just because of shared vocabulary.
    """
    clean = TextCleaner.clean(ai_text)

    # Signal table: each topic lists required and supporting keywords
    TOPIC_SIGNALS: Dict[str, dict] = {
        "Contraceptives for adolescents": {
            "required_any": ["remaja", "adolescent", "teenager"],
            "supporting":   ["kontraseptif", "contraceptive", "berisiko", "risk"],
            "boost": 18.0,
        },
        "Contraceptives for unmarried individuals": {
            "required_any": ["belum berkahwin", "unmarried"],
            "supporting":   ["kontraseptif", "contraceptive"],
            "boost": 18.0,
        },
        "Contraceptives for rape victims": {
            "required_any": ["rogol", "rape"],
            "supporting":   ["kontraseptif", "contraceptive"],
            "boost": 18.0,
        },
        "Contraceptives for HIV/AIDS prevention": {
            "required_any": ["hiv", "aids"],
            "supporting":   ["kontraseptif", "contraceptive", "kondom"],
            "boost": 18.0,
        },
        "Provision of contraceptives": {
            "required_any": ["kontraseptif", "contraceptive"],
            "supporting":   ["berkahwin", "pasangan"],
            "boost": 10.0,
        },
        "IVF": {
            "required_any": ["ivf", "bayi tabung", "in vitro"],
            "supporting":   ["persenyawaan", "fertilization"],
            "boost": 18.0,
        },
        "Human Milk Bank": {
            "required_any":   ["bank susu", "penderma susu", "bank susu ibu"],
            "supporting":     ["mahram susuan", "anak susuan"],
            "boost": 18.0,
            "penalty_if_absent": 20.0,
        },
        "Surrogacy": {
            "required_any":   ["ibu tumpang", "surrogacy", "surrogate", "sewa rahim"],
            "supporting":     ["rahim", "tumpang"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Sperm Bank": {
            "required_any":   ["bank air mani", "bank sperma", "sperm bank"],
            "supporting":     ["mani", "sperma"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Abortion resulting from rape": {
            "required_any": ["rogol", "rape"],
            "supporting":   ["pengguguran", "abortion", "kandungan"],
            "boost": 15.0,
        },
        "Abortion for OKU victims": {
            "required_any": ["oku", "orang kurang upaya"],
            "supporting":   ["pengguguran", "abortion"],
            "boost": 15.0,
        },
        "Abortion due to genetic disease (Example, Thalassemia)": {
            "required_any": ["thalassemia", "talasemia", "genetic"],
            "supporting":   ["pengguguran", "genetik", "penyakit"],
            "boost": 15.0,
        },
        "Abortion of Foetus with Thalassemia": {
            "required_any": ["thalassemia", "talasemia"],
            "supporting":   ["120 hari", "40 hari", "janin"],
            "boost": 15.0,
        },
        "Human Cloning (Reproductive)": {
            "required_any":   ["pengklonan", "cloning", "klon"],
            "supporting":     ["pembiakan", "reproduktif"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Human Cloning (Therapeutic)": {
            "required_any":   ["pengklonan", "cloning", "klon"],
            "supporting":     ["perubatan", "terapeutik"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
        "Stem Cell Research": {
            "required_any":   ["sel stem", "stem cell"],
            "supporting":     ["penyelidikan", "research"],
            "boost": 18.0,
            "penalty_if_absent": 15.0,
        },
    }

    result_df = issue_df.copy()

    for topic, signals in TOPIC_SIGNALS.items():
        if topic not in result_df["issue"].values:
            continue

        required_any = signals.get("required_any", [])
        supporting   = signals.get("supporting",   [])
        boost        = signals.get("boost",  10.0)
        penalty      = signals.get("penalty_if_absent", 0.0)

        found_required   = any(req in clean for req in required_any)
        found_supporting = any(sup in clean for sup in supporting)
        mask = result_df["issue"] == topic

        if found_required:
            extra = boost + (5.0 if found_supporting else 0.0)
            result_df.loc[mask, "issue_score"] = result_df.loc[mask, "issue_score"] + extra
        elif penalty > 0:
            result_df.loc[mask, "issue_score"] = (
                result_df.loc[mask, "issue_score"] - penalty
            ).clip(lower=0)

    return result_df.sort_values(
        by=["issue_score", "rule_boost", "issue_tfidf", "issue_sbert", "coverage"],
        ascending=False,
    ).reset_index(drop=True)


# =========================================================
# STAGE 1 — BEST QUESTION DETECTION
# =========================================================

def detect_best_question(
    ai_text: str,
    fatwa_df: pd.DataFrame,
) -> Tuple[dict, pd.DataFrame]:
    """
    Two-stage topic detection:

    Stage 1  — rank all issues (topics) to find the best-matching one.
    Stage 2  — within that issue, rank all questions to find the best one.

    Returns (best_question_row_dict, full_question_scores_DataFrame).
    """
    sbert_engine  = load_sbert_engine()
    issue_profiles = _build_issue_profiles(fatwa_df)

    if not issue_profiles:
        st.error("No topics found in the fatwa database.")
        st.stop()

    # ── Stage 1: build issue-level corpus and vectorizer ──────────────
    corpus = [ai_text]
    for p in issue_profiles:
        corpus.extend([p["issue_focus"], p["issue_reference"]])
    issue_vectorizer = RealTFIDF.fit_vectorizer(corpus)

    issue_rows = []
    for p in issue_profiles:
        focus_lexical  = RealTFIDF.calculate(ai_text, p["issue_focus"],      vectorizer=issue_vectorizer)
        ref_lexical    = RealTFIDF.calculate(ai_text, p["issue_reference"],   vectorizer=issue_vectorizer)
        focus_semantic = sbert_engine.calculate(ai_text, p["issue_focus"])
        alias_signal   = _alias_signal_scores(ai_text, p["aliases"])
        matched, _, coverage, _ = KeywordCoverage.calculate(
            ai_text, p["fatwa_summary"], vectorizer=issue_vectorizer, top_n=18
        )

        issue_score = round(
            focus_lexical  * 0.34
            + ref_lexical    * 0.16
            + focus_semantic * 0.20
            + coverage       * 0.10
            + alias_signal["score"] * 0.20,
            2,
        )

        issue_rows.append({
            "issue":                p["issue"],
            "issue_tfidf":         focus_lexical,
            "issue_reference_tfidf": ref_lexical,
            "issue_sbert":         focus_semantic,
            "coverage":            coverage,
            "keyword_overlap":     coverage,
            "rule_boost":          alias_signal["score"],
            "alias_intro_signal":  alias_signal["intro"],
            "alias_full_signal":   alias_signal["full"],
            "alias_hits":          alias_signal["alias_hits"],
            "best_alias":          alias_signal["best_alias"],
            "issue_score":         issue_score,
            "matched_issue_keywords": ", ".join(matched) if matched else "-",
        })

    issue_df = (
        pd.DataFrame(issue_rows)
        .sort_values(
            by=["issue_score", "rule_boost", "issue_tfidf", "issue_sbert", "coverage"],
            ascending=False,
        )
        .reset_index(drop=True)
    )

    # Disambiguation: re-rank using keyword presence signals
    issue_df = _disambiguate_topic(ai_text, issue_df)

    best_issue  = issue_df.iloc[0]["issue"]
    narrowed_df = fatwa_df[fatwa_df["issue"] == best_issue].copy()

    # ── Stage 2: question-level scoring within the best issue ─────────
    references: List[str] = []
    metadata:   List[tuple] = []

    for qid, group in narrowed_df.groupby("question_id"):
        combined_fatwa = " ".join(
            group["fatwa_text"].fillna("").astype(str).tolist()
        ).strip()
        issue_text    = normalize_text(group["issue"].iloc[0]) if "issue" in group.columns else ""
        question_text = normalize_text(group["question_text"].iloc[0]) if "question_text" in group.columns else ""
        focus_text    = f"{issue_text}. {question_text}".strip()
        ref_text      = f"{focus_text} {combined_fatwa}".strip()

        references.extend([focus_text, ref_text])
        metadata.append((qid, issue_text, question_text, combined_fatwa, focus_text, ref_text))

    question_vectorizer = RealTFIDF.fit_vectorizer([ai_text] + references)

    question_results = []
    for qid, issue_text, question_text, combined_fatwa, focus_text, ref_text in metadata:
        lexical       = RealTFIDF.calculate(ai_text, ref_text,    vectorizer=question_vectorizer)
        semantic      = sbert_engine.calculate(ai_text, ref_text)
        cov_matched, _, coverage, _ = KeywordCoverage.calculate(
            ai_text, combined_fatwa, vectorizer=question_vectorizer
        )
        issue_lexical  = RealTFIDF.calculate(ai_text, focus_text, vectorizer=question_vectorizer)
        issue_semantic = sbert_engine.calculate(ai_text, focus_text)
        alias_signal   = _alias_signal_scores(
            ai_text, _expand_dynamic_aliases(issue_text, [question_text])
        )

        topic_score = round(
            issue_lexical  * 0.34
            + issue_semantic * 0.16
            + lexical        * 0.14
            + semantic       * 0.12
            + coverage       * 0.08
            + alias_signal["score"] * 0.16,
            2,
        )

        high_signal = (
            topic_score >= 80
            or (alias_signal["intro"] >= 95 and issue_semantic >= 60)
            or (topic_score >= 74 and semantic >= 60 and issue_lexical >= 55)
        )
        medium_signal = (
            topic_score >= 58
            or (alias_signal["score"] >= 50 and issue_lexical >= 45)
            or (semantic >= 50 and issue_semantic >= 48)
        )

        confidence = "High" if high_signal else "Medium" if medium_signal else "Low"

        question_results.append({
            "question_id":          qid,
            "issue":                issue_text,
            "question_text":        question_text,
            "topic_score":          topic_score,
            "confidence":           confidence,
            "tfidf":                lexical,
            "sbert":                semantic,
            "coverage":             coverage,
            "keyword_overlap":      coverage,
            "issue_tfidf":          issue_lexical,
            "issue_sbert":          issue_semantic,
            "rule_boost":           alias_signal["score"],
            "alias_intro_signal":   alias_signal["intro"],
            "alias_full_signal":    alias_signal["full"],
            "alias_hits":           alias_signal["alias_hits"],
            "best_alias":           alias_signal["best_alias"],
            "issue_stage_score":    float(issue_df.iloc[0]["issue_score"]),
            "issue_stage_alias":    str(issue_df.iloc[0]["best_alias"]),
            "issue_stage_keywords": str(issue_df.iloc[0]["matched_issue_keywords"]),
            "matched_focus_keywords": ", ".join(cov_matched) if cov_matched else "-",
        })

    question_df = pd.DataFrame(question_results)
    if question_df.empty:
        st.error("No topics found in the database for the detected issue.")
        st.stop()

    question_df = question_df.sort_values(
        by=["topic_score", "rule_boost", "issue_tfidf", "alias_intro_signal",
            "sbert", "coverage", "tfidf"],
        ascending=False,
    ).reset_index(drop=True)

    return question_df.iloc[0], question_df


# =========================================================
# STAGE 2 — STATE-LEVEL COMPARISON
# Equation (9):  MaxAlign_i  = max alignment across all states
# Equation (10): MeanAlign_i = mean alignment across all states
# =========================================================

def compare_states_within_question(
    ai_text: str,
    fatwa_subset: pd.DataFrame,
    top_n_keywords: int = 14,
) -> Tuple[dict, pd.DataFrame]:
    """
    For each state-fatwa pair in fatwa_subset, compute the three metrics
    then the weighted alignment score:

        alignment = 0.60 × SBERT + 0.25 × TF-IDF + 0.15 × keyword coverage

    After processing all states:
      Equation (9)  MaxAlign  — row with highest alignment score
      Equation (10) MeanAlign — mean of all states' alignment scores

    Returns (best_state_dict, full_results_DataFrame).
    """
    sbert_engine = load_sbert_engine()
    fatwa_texts  = fatwa_subset["fatwa_text"].fillna("").astype(str).tolist()
    vectorizer   = RealTFIDF.fit_vectorizer([ai_text] + fatwa_texts)

    results = []
    for _, row in fatwa_subset.iterrows():
        state        = normalize_text(row["state"])
        fatwa        = normalize_text(row["fatwa_text"])
        qid          = normalize_text(row["question_id"])
        issue        = normalize_text(row.get("issue",         ""))
        question_text = normalize_text(row.get("question_text", ""))

        if not fatwa:
            continue

        # Equation (4): TF-IDF cosine similarity
        lexical = RealTFIDF.calculate(ai_text, fatwa, vectorizer=vectorizer)

        # Equations (5)–(7): SBERT mean-pooled cosine
        semantic = sbert_engine.calculate(ai_text, fatwa)

        # Equation (8): keyword coverage
        matched, unmatched, coverage, keywords = KeywordCoverage.calculate(
            ai_text=ai_text,
            fatwa_text=fatwa,
            vectorizer=vectorizer,
            top_n=top_n_keywords,
        )

        # Composite alignment score per state
        alignment_score = (semantic * 0.60) + (lexical * 0.25) + (coverage * 0.15)

        results.append({
            "question_id":         qid,
            "issue":               issue,
            "question_text":       question_text,
            "state":               state,
            "tfidf":               lexical,
            "lexical_similarity":  lexical,
            "semantic_similarity": semantic,
            "coverage":            coverage,
            "alignment_score":     round(float(alignment_score), 2),
            "matched_keywords":    ", ".join(matched)   if matched   else "-",
            "missing_keywords":    ", ".join(unmatched) if unmatched else "-",
            "fatwa_keywords":      ", ".join(keywords)  if keywords  else "-",
            "fatwa_text":          fatwa,
        })

    results_df = pd.DataFrame(results)
    if results_df.empty:
        st.error("No state-level fatwa records found for this topic.")
        st.stop()

    results_df = results_df.sort_values(
        by=["alignment_score", "semantic_similarity", "coverage"],
        ascending=False,
    ).reset_index(drop=True)

    # Equation (9): MaxAlign — best-matching state
    best_state    = results_df.iloc[0]
    # Equation (10): MeanAlign — average alignment across all states
    mean_alignment = results_df["alignment_score"].mean()

    return {
        "state":               best_state["state"],
        "issue":               best_state["issue"],
        "fatwa_text":          best_state["fatwa_text"],
        "best_match_alignment": best_state["alignment_score"],   # Eq. (9)
        "mean_alignment":       round(float(mean_alignment), 2), # Eq. (10)
        "lexical_similarity":   best_state["lexical_similarity"],
        "semantic_similarity":  best_state["semantic_similarity"],
        "coverage":             best_state["coverage"],
        "matched_keywords":     best_state["matched_keywords"],
        "missing_keywords":     best_state["missing_keywords"],
    }, results_df