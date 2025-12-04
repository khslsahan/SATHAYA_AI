"""Tests for Citation Service."""

from src.services.citation_service import CitationService


def test_format_act_citation():
    """Test Act citation formatting."""
    service = CitationService()
    citation = service.format_act_citation("Companies Act", "18")
    assert citation == "Companies Act, Section 18"


def test_extract_citations():
    """Test citation extraction."""
    service = CitationService()
    text = "According to Companies Act, Section 18, companies must register."
    citations = service.extract_citations(text)
    
    assert len(citations) > 0
    assert citations[0]["type"] == "act"
    assert citations[0]["act_name"] == "Companies Act"
    assert citations[0]["section"] == "18"

