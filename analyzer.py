"""
Text sentiment and toxicity analysis using pretrained models
"""

import logging
from transformers import pipeline
# from config import Config

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """Handles text analysis using pretrained models"""

    def __init__(self):
        """Initialize sentiment and toxicity models"""
        try:
            self.sentiment = pipeline(
                "text-classification",
                model="finiteautomata/bertweet-base-sentiment-analysis",  # 3x smaller
                device=-1  # Force CPU usage
            )

            self.toxicity = pipeline(
                "text-classification",
                model="unitary/toxic-bert",  # Optimized for low-resource environments
                device=-1
            )
            logger.info("Models loaded successfully")

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to load models: %s", e)
            raise

    def analyze(self, text):
        """
        Analyze text for sentiment and toxicity
        Args:
            text: Input text to analyze
        Returns:
            dict: Analysis results
        """
        try:
            # Get sentiment
            sentiment_result = self.sentiment(text)[0]

            # Get toxicity
            toxicity_result = self.toxicity(text)[0]

            # Determine final classification
            if toxicity_result['label'] == 'hate' and toxicity_result['score'] > 0.85:
                return {
                    "sentiment": "toxic",
                    "confidence": toxicity_result['score'],
                    "is_toxic": True,
                    "original_sentiment": sentiment_result['label']
                }
            return {
                "sentiment": sentiment_result['label'].lower(),
                "confidence": sentiment_result['score'],
                "is_toxic": False
            }
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Analysis failed: %s", e)
            return {
                "sentiment": "error",
                "confidence": 0,
                "is_toxic": False
            }
