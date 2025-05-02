from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from loguru import logger

nltk.download("vader_lexicon", quiet=True)


class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.harmful_keywords = {
            "offensive": ["idiot", "stupid", "hate you", "ugly"],
            "terrorism": ["bomb", "kill", "attack", "shoot"]
        }

    def analyze(self, text: str) -> dict:
        """Returns detailed sentiment + harmful content flags."""
        scores = self.analyzer.polarity_scores(text)
        label = self._get_label(scores["compound"])

        # Check for harmful content
        harmful_flags = self._detect_harmful(text)

        return {
            "label": label,
            "scores": scores,
            "harmful": harmful_flags
        }

    def _get_label(self, compound_score: float) -> str:
        if compound_score >= 0.05:
            return "Positive 😊"
        elif compound_score <= -0.05:
            return "Negative 😠"
        else:
            return "Neutral 😐"

    def _detect_harmful(self, text: str) -> dict:
        """Detects offensive/terrorism-related content."""
        text_lower = text.lower()
        flags = {
            "is_offensive": any(word in text_lower for word in self.harmful_keywords["offensive"]),
            "is_terrorism": any(word in text_lower for word in self.harmful_keywords["terrorism"])
        }
        return flags
