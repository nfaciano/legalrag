"""
Document generation module for creating formatted legal documents.
"""

from .template_manager import TemplateManager, get_template_manager
from .template_document_generator import TemplateDocumentGenerator, get_template_generator
from .document_builder import DocumentBuilder, get_document_builder
from .envelope_generator import EnvelopeGenerator, get_envelope_generator
from .envelope_builder import EnvelopeBuilder, get_envelope_builder
from .pleading_generator import PleadingGenerator, get_pleading_generator
from .pleading_builder import PleadingBuilder, get_pleading_builder

__all__ = [
    "TemplateManager",
    "get_template_manager",
    "TemplateDocumentGenerator",
    "get_template_generator",
    "DocumentBuilder",
    "get_document_builder",
    "EnvelopeGenerator",
    "get_envelope_generator",
    "EnvelopeBuilder",
    "get_envelope_builder",
    "PleadingGenerator",
    "get_pleading_generator",
    "PleadingBuilder",
    "get_pleading_builder",
]
