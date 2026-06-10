"""Entity extraction from text, audio, and images."""

import logging
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Supported entity types."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    DATE = "date"
    OBJECT = "object"
    DOCUMENT = "document"
    DEVICE = "device"


@dataclass
class Entity:
    """Extracted entity with metadata."""
    id: str
    name: str
    type: EntityType
    confidence: float
    source: str
    metadata: Dict
    
    def __hash__(self):
        return hash(self.id)


class EntityExtractor:
    """Extract entities from multiple modalities."""

    def __init__(self, config: Dict):
        self.config = config
        self.spacy_model = None
        self.whisper_model = None
        self.yolo_model = None
        self.entity_cache: Dict[str, Entity] = {}
        self._initialize_models()

    def _initialize_models(self) -> None:
        """Load NLP and perception models."""
        try:
            import spacy
            self.spacy_model = spacy.load(self.config.get("spacy_model", "en_core_web_lg"))
            logger.info("spaCy model loaded")
        except Exception as e:
            logger.error(f"Failed to load spaCy: {str(e)}")

    def extract_from_text(self, text: str, source: str = "unknown") -> List[Entity]:
        """Extract entities from text using spaCy NER."""
        if not self.spacy_model:
            logger.warning("spaCy model not loaded")
            return []
        
        try:
            doc = self.spacy_model(text)
            entities = []
            
            for ent in doc.ents:
                entity = self._create_entity_from_spacy(ent, source)
                if entity:
                    entities.append(entity)
                    self.entity_cache[entity.id] = entity
            
            return entities
        
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return []

    def _create_entity_from_spacy(self, ent, source: str) -> Entity:
        """Convert spaCy entity to Entity object."""
        type_mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "EVENT": EntityType.EVENT,
            "DATE": EntityType.DATE,
            "PRODUCT": EntityType.OBJECT,
        }
        
        entity_type = type_mapping.get(ent.label_, EntityType.OBJECT)
        
        return Entity(
            id=f"{entity_type.value}_{hash(ent.text) % 1000000}",
            name=ent.text,
            type=entity_type,
            confidence=1.0,  # spaCy doesn't provide confidence
            source=source,
            metadata={
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "text": ent.text
            }
        )

    def extract_from_audio(self, audio_path: str, source: str = "audio") -> List[Entity]:
        """Transcribe audio using Whisper and extract entities."""
        try:
            # Placeholder: would use Whisper for transcription
            transcribed_text = self._transcribe_audio(audio_path)
            return self.extract_from_text(transcribed_text, source=source)
        except Exception as e:
            logger.error(f"Audio extraction error: {str(e)}")
            return []

    def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file using Whisper."""
        # Implementation: call Whisper API
        pass

    def extract_from_image(self, image_path: str, source: str = "image") -> List[Entity]:
        """Extract entities from image using YOLO and OCR."""
        try:
            entities = []
            
            # Object detection
            objects = self._detect_objects(image_path)
            entities.extend(objects)
            
            # OCR text extraction
            text = self._extract_text_from_image(image_path)
            if text:
                text_entities = self.extract_from_text(text, source=source)
                entities.extend(text_entities)
            
            return entities
        except Exception as e:
            logger.error(f"Image extraction error: {str(e)}")
            return []

    def _detect_objects(self, image_path: str) -> List[Entity]:
        """Detect objects in image using YOLO."""
        # Implementation: call YOLO v8
        pass

    def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using Tesseract OCR."""
        # Implementation: call Tesseract
        pass

    def deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities using fuzzy matching."""
        deduplicated = []
        
        for entity in entities:
            is_duplicate = False
            
            for existing in deduplicated:
                if self._are_entities_similar(entity, existing):
                    is_duplicate = True
                    # Merge confidence scores
                    existing.confidence = max(existing.confidence, entity.confidence)
                    break
            
            if not is_duplicate:
                deduplicated.append(entity)
        
        return deduplicated

    def _are_entities_similar(self, e1: Entity, e2: Entity) -> bool:
        """Check if two entities are likely the same using fuzzy matching."""
        if e1.type != e2.type:
            return False
        
        # Simple string similarity
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, e1.name.lower(), e2.name.lower()).ratio()
        return similarity > 0.8

    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all cached entities of a specific type."""
        return [e for e in self.entity_cache.values() if e.type == entity_type]

    def clear_cache(self) -> None:
        """Clear entity cache."""
        self.entity_cache.clear()
        logger.info("Entity cache cleared")
