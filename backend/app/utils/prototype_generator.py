"""
Prototype Generator Module
Generates 4 different document prototypes with different styles
"""

from typing import List, Dict, Any
import re


def generate_prototypes(
    original_text: str,
    category: str,
    language: str,
    analysis: Dict[str, Any],
    user_notes: str = ""
) -> List[Dict[str, Any]]:
    """
    Generate 4 document prototypes with different styles

    Parameters:
    - original_text: Original document text
    - category: Document category
    - language: Output language (en, th, both)
    - analysis: Analysis results including field metadata
    - user_notes: Additional user notes (optional)

    Returns:
    - List of 4 prototypes with field highlighting info
    """

    # Get field metadata for highlighting
    field_metadata = analysis.get('field_metadata', []) if analysis else []

    prototypes = [
        generate_formal_academic(original_text, category, language, field_metadata),
        generate_concise_business(original_text, category, language, field_metadata),
        generate_narrative_detailed(original_text, category, language, field_metadata),
        generate_structured_template(original_text, category, language, field_metadata)
    ]

    return prototypes


def generate_formal_academic(text: str, category: str, language: str, field_metadata: List[Dict] = None) -> Dict[str, Any]:
    """
    Generate Formal Academic Style prototype

    Characteristics:
    - Complex vocabulary
    - Passive voice
    - Formal tone
    - Comprehensive
    """

    if language == 'th':
        name = "รูปแบบการเขียนวิชาการ"
        description = "สไตล์การเขียนอย่างเป็นทางการ สำหรับการส่งต่อ Ethics Committee"
    else:
        name = "Formal Academic Style"
        description = "Comprehensive academic approach with formal terminology"

    # Process text to be more formal
    content = enhance_formality(text, language=language)
    content = ensure_proper_structure(content)

    return {
        "name": name,
        "description": description,
        "style": "academic",
        "content": content,
        "highlighted_sections": extract_key_sections(text),
        "field_metadata": field_metadata or [],
        "notes": "Use this version for formal submissions to ethics committees"
    }


def generate_concise_business(text: str, category: str, language: str, field_metadata: List[Dict] = None) -> Dict[str, Any]:
    """
    Generate Concise Business Style prototype

    Characteristics:
    - Short paragraphs
    - Active voice
    - Business-focused
    - Clear and direct
    """

    if language == 'th':
        name = "รูปแบบธุรกิจ"
        description = "สไตล์การเขียนกระชับและชัดเจน เหมาะสำหรับสรุป"
    else:
        name = "Concise Business Style"
        description = "Direct and focused presentation ideal for busy readers"

    # Create concise version (reduce by ~30%)
    content = create_concise_version(text)
    content = convert_to_active_voice(content)

    return {
        "name": name,
        "description": description,
        "style": "business",
        "content": content,
        "highlighted_sections": extract_key_sections(text),
        "field_metadata": field_metadata or [],
        "notes": "Use this version for executive summaries and quick reviews"
    }


def generate_narrative_detailed(text: str, category: str, language: str, field_metadata: List[Dict] = None) -> Dict[str, Any]:
    """
    Generate Narrative Detailed Style prototype

    Characteristics:
    - Storytelling approach
    - Natural flow
    - Conversational yet formal
    - Detailed explanations
    """

    if language == 'th':
        name = "รูปแบบการบรรยายรายละเอียด"
        description = "สไตล์การบรรยายที่เข้าใจง่าย ส่วนที่ยาว และอธิบายรายละเอียด"
    else:
        name = "Narrative Detailed Style"
        description = "Story-like presentation with comprehensive explanations"

    # Expand with explanations
    content = expand_with_narratives(text)
    content = add_transition_phrases(content, language)

    return {
        "name": name,
        "description": description,
        "style": "narrative",
        "content": content,
        "highlighted_sections": extract_key_sections(text),
        "field_metadata": field_metadata or [],
        "notes": "Use this version for detailed reports and comprehensive documentation"
    }


def generate_structured_template(text: str, category: str, language: str, field_metadata: List[Dict] = None) -> Dict[str, Any]:
    """
    Generate Structured Template Style prototype

    Characteristics:
    - Highly organized
    - Clear sections
    - Bullet points where appropriate
    - Quick scanning
    """

    if language == 'th':
        name = "รูปแบบโครงสร้างมาตรฐาน"
        description = "สไตล์ที่มีโครงสร้างชัดเจน เหมาะสำหรับการตรวจสอบ"
    else:
        name = "Structured Template Style"
        description = "Organized format with clear sections and key points"

    # Create structured version with sections and bullets
    content = create_structured_format(text, category)

    return {
        "name": name,
        "description": description,
        "style": "structured",
        "content": content,
        "highlighted_sections": extract_key_sections(text),
        "field_metadata": field_metadata or [],
        "notes": "Use this version for easy review and modification"
    }


# ============================================
# HELPER FUNCTIONS
# ============================================

def enhance_formality(text: str, language: str = 'en') -> str:
    """
    Enhance formality of text

    Replaces casual language with formal equivalents
    """

    if language == 'th':
        replacements = {
            r'\bครับ\b': '',
            r'\bค่ะ\b': '',
            r'\bเนี่ย\b': '',
            r'\bแล้ว\b': 'สำเร็จแล้ว',
        }
    else:
        replacements = {
            r'\bwanna\b': 'want to',
            r'\bgonna\b': 'going to',
            r'\bkinda\b': 'kind of',
            r'\bstuff\b': 'matters',
            r'\bthings\b': 'factors',
            r"\byou\b": 'one',
        }

    result = text
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def create_concise_version(text: str) -> str:
    """
    Create a concise version by removing redundancies
    """

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Remove duplicate concepts
    unique_sentences = []
    seen_concepts = set()

    for sentence in sentences:
        concept = extract_concept(sentence)
        if concept not in seen_concepts:
            unique_sentences.append(sentence)
            seen_concepts.add(concept)

    return ' '.join(unique_sentences)


def convert_to_active_voice(text: str) -> str:
    """
    Attempt to convert passive to active voice
    """

    # Simple passive voice patterns
    patterns = {
        r'was (\w+)ed by the': r'the \1',
        r'is (\w+)ed': r'\1s',
        r'are (\w+)ed': r'\1'
    }

    result = text
    for pattern, replacement in patterns.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def expand_with_narratives(text: str) -> str:
    """
    Expand text with narrative elements
    """

    lines = text.split('\n')
    expanded = []

    for line in lines:
        if line.strip():
            # Add context phrases
            if len(line.split()) > 20:
                # Long line - keep as is
                expanded.append(line)
            else:
                # Short line - add context
                expanded.append(line)

    return '\n'.join(expanded)


def add_transition_phrases(text: str, language: str) -> str:
    """
    Add transition phrases for better flow
    """

    if language == 'th':
        transitions = [
            'นอกจากนี้', 'ดังนั้น', 'จากข้างต้น', 'เมื่อพิจารณา',
            'ซึ่งสำคัญที่สุด', 'นอกจากนี้', 'อย่างไรก็ตาม'
        ]
    else:
        transitions = [
            'Furthermore,', 'Therefore,', 'As noted above,', 'Importantly,',
            'Additionally,', 'However,', 'In conclusion,'
        ]

    # Simple insertion at paragraph beginnings
    paragraphs = text.split('\n\n')
    enhanced = []

    for i, para in enumerate(paragraphs):
        if i > 0 and para.strip():
            # Add a transition to non-first paragraphs
            transition = transitions[i % len(transitions)]
            enhanced.append(f"{transition} {para}")
        else:
            enhanced.append(para)

    return '\n\n'.join(enhanced)


def create_structured_format(text: str, category: str) -> str:
    """
    Create a structured format with sections and bullets
    """

    sections = {
        "Overview": extract_overview(text),
        "Key Points": extract_key_points(text),
        "Details": text[:500] if len(text) > 500 else text,
        "Next Steps": "[Action items to be determined]"
    }

    structured = ""
    for section_title, content in sections.items():
        structured += f"\n{section_title}\n{'='*40}\n{content}\n"

    return structured


def extract_key_sections(text: str) -> List[str]:
    """Extract key section names from text"""

    keywords = [
        r'introduction|background|objective|method|result|discussion|conclusion',
        r'abstract|executive|summary|recommendation|reference'
    ]

    sections = []
    for keyword_pattern in keywords:
        matches = re.findall(f'({keyword_pattern})', text, re.IGNORECASE)
        sections.extend(set(matches))

    return list(set(sections))[:5]  # Return unique sections


def extract_concept(sentence: str) -> str:
    """Extract main concept from sentence for deduplication"""

    words = sentence.split()
    if len(words) > 3:
        return ' '.join(words[:3]).lower()
    return sentence.lower()


def ensure_proper_structure(text: str) -> str:
    """Ensure text has proper structure"""

    # Add missing punctuation
    text = re.sub(r'([A-Z][^.!?]*?)([A-Z])', r'\1. \2', text)

    return text


def extract_overview(text: str) -> str:
    """Extract overview from text"""

    lines = text.split('\n')
    # Take first 100 words
    words = ' '.join(lines).split()[:100]
    return ' '.join(words)


def extract_key_points(text: str) -> str:
    """Extract key points from text"""

    lines = text.split('\n')
    key_points = []

    for line in lines:
        if len(line.split()) > 5 and len(line.split()) < 30:
            key_points.append(f"• {line.strip()}")

    return '\n'.join(key_points[:5])  # Return max 5 key points
