import json
import os
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import re

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

# Import local model trainer (will initialize lazily)
_model_trainer = None

def get_model_trainer():
    """Get or initialize model trainer"""
    global _model_trainer
    if _model_trainer is None:
        from services.model_training import LocalModelTrainer
        _model_trainer = LocalModelTrainer()
    return _model_trainer

class GeminiLabelingService:
    """Service for AI-powered data labeling using Google Gemini API"""

    def __init__(self):
        """Initialize Gemini service with API key from environment"""
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please configure it in .env file"
            )

        if genai is None:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)
        self.client = genai
        self.model = "gemini-1.5-flash"
        logger.info(f"Initialized Gemini service with model: {self.model}")

    def _create_tabular_prompt(self, content_preview: str, file_type: str) -> str:
        """Create prompt for tabular data (CSV/Excel/JSON)"""
        return f"""Analyze the following {file_type.upper()} data record and provide a classification label.

Data: {content_preview}

IMPORTANT: Respond ONLY with a valid JSON object (no markdown, no extra text).
The JSON must contain exactly these two keys:
- "label": A concise classification label (string, max 50 characters)
- "confidence_score": A float between 0.0 and 1.0 indicating your confidence

Example response:
{{"label": "electronics", "confidence_score": 0.95}}

Now classify the data above:"""

    def _create_image_prompt(self) -> str:
        """Create prompt for image data"""
        return """Analyze this image and provide a classification label based on its content.

IMPORTANT: Respond ONLY with a valid JSON object (no markdown, no extra text).
The JSON must contain exactly these two keys:
- "label": A concise classification label describing the main content (string, max 50 characters)
- "confidence_score": A float between 0.0 and 1.0 indicating your confidence

Example response:
{{"label": "landscape", "confidence_score": 0.85}}

Now classify the image:"""

    def _create_audio_prompt(self) -> str:
        """Create prompt for audio data (when transcription is available)"""
        return """Analyze the following audio content and provide a classification label.

Content: {content}

IMPORTANT: Respond ONLY with a valid JSON object (no markdown, no extra text).
The JSON must contain exactly these two keys:
- "label": A classification label for the audio content (string, max 50 characters)
- "confidence_score": A float between 0.0 and 1.0 indicating your confidence

Example response:
{{"label": "speech", "confidence_score": 0.88}}

Now classify the audio:"""

    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON response from Gemini with robust error handling.
        Attempts to extract and validate JSON from the response.
        """
        try:
            # First, try direct JSON parsing
            result = json.loads(response_text)
            return self._validate_response(result)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from text (in case of markdown or extra content)
        json_match = re.search(r'\{[^{}]*\}', response_text)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return self._validate_response(result)
            except json.JSONDecodeError:
                pass

        # Try extracting more complex JSON structures
        try:
            # Find the first { and last } and try to parse everything between
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_str = response_text[start_idx:end_idx + 1]
                result = json.loads(json_str)
                return self._validate_response(result)
        except json.JSONDecodeError:
            pass

        raise ValueError(
            f"Could not parse valid JSON from response: {response_text[:200]}"
        )

    def _validate_response(self, data: Dict) -> Dict:
        """Validate that response has required fields with correct types"""
        required_fields = {"label", "confidence_score"}

        if not isinstance(data, dict):
            raise ValueError(f"Response must be a JSON object, got: {type(data)}")

        if not required_fields.issubset(data.keys()):
            missing = required_fields - set(data.keys())
            raise ValueError(
                f"Response missing required fields: {missing}. "
                f"Got fields: {list(data.keys())}"
            )

        # Validate label
        label = data.get("label")
        if not isinstance(label, str):
            raise ValueError(
                f"Field 'label' must be a string, got: {type(label)}"
            )

        if len(label) == 0 or len(label) > 50:
            raise ValueError(
                f"Field 'label' must be 1-50 characters, got {len(label)}"
            )

        # Validate confidence_score
        try:
            confidence = float(data.get("confidence_score"))
        except (TypeError, ValueError):
            raise ValueError(
                f"Field 'confidence_score' must be a number, "
                f"got: {data.get('confidence_score')}"
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"Field 'confidence_score' must be between 0.0 and 1.0, "
                f"got: {confidence}"
            )

        return {
            "label": label.strip(),
            "confidence_score": round(confidence, 4)
        }

    def label_text_data(self, content_preview: str, file_type: str) -> Dict:
        """
        Label text/tabular data (CSV, Excel, JSON).

        Args:
            content_preview: String representation of data item
            file_type: Type of file ('csv', 'excel', 'json')

        Returns:
            Dict with 'label' and 'confidence_score'

        Raises:
            ValueError: If API fails or response is invalid
        """
        try:
            prompt = self._create_tabular_prompt(content_preview, file_type)

            response = self.client.GenerativeModel(
                self.model
            ).generate_content(prompt)

            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")

            logger.debug(f"Raw Gemini response: {response.text}")

            result = self._parse_json_response(response.text)
            logger.info(
                f"Successfully labeled {file_type} data: "
                f"label={result['label']}, "
                f"confidence={result['confidence_score']}"
            )

            return result

        except self.client.APIError as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise ValueError(f"Gemini API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error labeling text data: {str(e)}")
            raise

    def label_image_data(self, image_path: str) -> Dict:
        """
        Label image data using multimodal Gemini vision.

        Args:
            image_path: Path to image file

        Returns:
            Dict with 'label' and 'confidence_score'

        Raises:
            ValueError: If image not found or API fails
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Upload image to Gemini (required for vision tasks)
            image_file = self.client.upload_file(image_path)

            prompt = self._create_image_prompt()

            response = self.client.GenerativeModel(
                self.model
            ).generate_content([prompt, image_file])

            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")

            logger.debug(f"Raw Gemini response for image: {response.text}")

            result = self._parse_json_response(response.text)
            logger.info(
                f"Successfully labeled image: "
                f"label={result['label']}, "
                f"confidence={result['confidence_score']}"
            )

            return result

        except FileNotFoundError as e:
            logger.error(f"Image file error: {str(e)}")
            raise ValueError(str(e))
        except self.client.APIError as e:
            logger.error(f"Gemini API error for image: {str(e)}")
            raise ValueError(f"Gemini API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error labeling image data: {str(e)}")
            raise

    def label_audio_metadata(self, metadata: Dict) -> Dict:
        """
        Label audio data based on metadata.
        Full audio processing would require transcription service.

        Args:
            metadata: Audio metadata (duration, sample_rate, etc.)

        Returns:
            Dict with 'label' and 'confidence_score'

        Raises:
            ValueError: If API fails or response is invalid
        """
        try:
            content = json.dumps(metadata)
            prompt = self._create_audio_prompt().format(content=content)

            response = self.client.GenerativeModel(
                self.model
            ).generate_content(prompt)

            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")

            logger.debug(f"Raw Gemini response for audio: {response.text}")

            result = self._parse_json_response(response.text)
            logger.info(
                f"Successfully labeled audio: "
                f"label={result['label']}, "
                f"confidence={result['confidence_score']}"
            )

            return result

        except self.client.APIError as e:
            logger.error(f"Gemini API error for audio: {str(e)}")
            raise ValueError(f"Gemini API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error labeling audio data: {str(e)}")
            raise

    def label_data_item(self, data_item, dataset_id: Optional[int] = None) -> Tuple[str, float, str]:
        """
        Route data item to appropriate labeling function based on type.

        Uses local model first if available, falls back to Gemini API.

        Args:
            data_item: DataItem model instance
            dataset_id: Optional dataset ID to check for local model

        Returns:
            Tuple of (label, confidence_score, model_used)
            where model_used is 'local' or 'gemini'

        Raises:
            ValueError: If labeling fails
        """
        try:
            file_type = data_item.file_type.lower()

            # Try local model first for text data
            if file_type in ['csv', 'excel', 'json'] and dataset_id:
                try:
                    trainer = get_model_trainer()
                    if trainer.model_exists(dataset_id):
                        label, confidence = trainer.predict(
                            dataset_id,
                            data_item.content_preview
                        )

                        # Use local model only if confidence is high enough
                        if confidence >= 0.7:
                            logger.info(
                                f"Used local model for item {data_item.id}: "
                                f"label={label}, confidence={confidence:.4f}"
                            )
                            return label, confidence, "local"
                        else:
                            logger.info(
                                f"Local model confidence too low ({confidence:.4f}), "
                                f"falling back to Gemini"
                            )
                except Exception as e:
                    logger.warning(f"Local model inference failed: {str(e)}")
                    # Fall through to Gemini API

            # Fall back to Gemini API
            if file_type in ['csv', 'excel', 'json']:
                result = self.label_text_data(
                    data_item.content_preview,
                    file_type
                )
            elif file_type == 'image':
                result = self.label_image_data(data_item.raw_data_path)
            elif file_type == 'audio':
                # For audio, parse metadata from preview
                try:
                    metadata = json.loads(data_item.content_preview)
                except:
                    metadata = {"info": data_item.content_preview}
                result = self.label_audio_metadata(metadata)
            else:
                raise ValueError(
                    f"Unsupported file type for labeling: {file_type}"
                )

            return result["label"], result["confidence_score"], "gemini"

        except Exception as e:
            logger.error(
                f"Error labeling DataItem {data_item.id}: {str(e)}"
            )
            raise
