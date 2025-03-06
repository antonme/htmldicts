"""
Ossetian Transliteration Module

This module provides functions to convert between Cyrillic and Latin script
variants of Ossetian words to improve search capabilities across different
writing systems.

The transliteration follows scholarly conventions for Ossetian:
- æ is transcribed as ä
- у as ә 
- Glottal stops are marked with apostrophes: k', p', t', c'
- Iron dialect affricates derived from k, g, k' are represented as k, g, k'
- Secondary labialization is marked with a small circle (kẜ, gẜ, k'ẜ)
"""

# Latin to Cyrillic mapping
LATIN_TO_CYRILLIC = {
    'a': 'а', 'æ': 'æ', 'ä': 'æ', 'b': 'б', 'c': 'ц', 'č': 'ч', 'd': 'д',
    'e': 'е', 'f': 'ф', 'g': 'г', 'ğ': 'гъ', 'h': 'х', 'i': 'и',
    'j': 'й', 'k': 'к', 'ḱ': 'къ', 'l': 'л', 'm': 'м', 'n': 'н',
    'o': 'о', 'p': 'п', 'ṕ': 'пъ', 'q': 'хъ', 'r': 'р', 's': 'с',
    'š': 'ш', 't': 'т', 'ṭ': 'тъ', 'u': 'у', 'ū': 'у', 'v': 'в',
    'w': 'у', 'x': 'х', 'y': 'ы', 'z': 'з', 'ž': 'ж', 'ә': 'у',
    # Glottal stops with apostrophes
    "k'": 'къ', "p'": 'пъ', "t'": 'тъ', "c'": 'цъ',
    # Labialized velar consonants 
    'kẜ': 'хъу', 'gẜ': 'гъу', "k'ẜ": 'къу',
    # Common digraphs and special cases
    'dz': 'дз', 'dzh': 'дж'
}

# Cyrillic to Latin mapping
CYRILLIC_TO_LATIN = {
    'а': 'a', 'æ': 'æ', 'б': 'b', 'в': 'v', 'г': 'g', 'гъ': 'ğ',
    'д': 'd', 'дж': 'dzh', 'дз': 'dz', 'е': 'e', 'ё': 'jo', 'ж': 'ž',
    'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'къ': "k'", 'л': 'l',
    'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'пъ': "p'", 'р': 'r',
    'с': 's', 'т': 't', 'тъ': "t'", 'у': 'u', 'ф': 'f', 'х': 'h',
    'хъ': 'q', 'ц': 'c', 'цъ': "c'", 'ч': 'č', 'ш': 'š', 'щ': 'šč', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'ju', 'я': 'ja',
    # Labialized combinations
    'хъу': 'kẜ', 'гъу': 'gẜ', 'къу': "k'ẜ"
}

# Special case mapping for specific Ossetian word variants
SPECIAL_CASE_MAPPING = {
    'tærqūs': 'тæрхъус',
    'tærqos': 'тæрхъус',
    'tärqūs': 'тæрхъус',  # Alternative spelling with ä instead of æ
    'tärqos': 'тæрхъус',  # Alternative spelling with ä instead of æ
    'тæрхъус': ['tærqūs', 'tærqos', 'tärqūs', 'tärqos']
}

# Additional spelling variants for typo tolerance
COMMON_VARIANTS = {
    'æ': ['ä', 'a', 'e'],
    'ä': ['æ', 'a', 'e'],
    'ū': ['u'],
    'ә': ['u', 'y'],
    'ẜ': ['w'],
    'ğ': ['gh'],
    'š': ['sh'],
    'ž': ['zh'],
    'č': ['ch']
}

def latin_to_cyrillic(text):
    """
    Convert Latin script Ossetian text to Cyrillic script.
    
    Args:
        text (str): The Latin script text to convert
        
    Returns:
        str: The Cyrillic script equivalent
    """
    # Check for special case matches first
    if text.lower() in SPECIAL_CASE_MAPPING:
        return SPECIAL_CASE_MAPPING[text.lower()]
    
    # Process general case with character mapping
    result = ''
    i = 0
    while i < len(text):
        # Check for trigraphs first (like "k'ẜ")
        if i < len(text) - 2 and text[i:i+3].lower() in LATIN_TO_CYRILLIC:
            char = text[i:i+3].lower()
            result += LATIN_TO_CYRILLIC[char]
            i += 3
        # Then check for digraphs (like "k'", "dz")
        elif i < len(text) - 1 and text[i:i+2].lower() in LATIN_TO_CYRILLIC:
            char = text[i:i+2].lower()
            result += LATIN_TO_CYRILLIC[char]
            i += 2
        # Then check for single characters
        elif text[i].lower() in LATIN_TO_CYRILLIC:
            if text[i].isupper():
                result += LATIN_TO_CYRILLIC[text[i].lower()].upper()
            else:
                result += LATIN_TO_CYRILLIC[text[i].lower()]
            i += 1
        else:
            # If character not in mapping, keep it as is
            result += text[i]
            i += 1
    
    return result

def cyrillic_to_latin(text):
    """
    Convert Cyrillic script Ossetian text to Latin script.
    
    Args:
        text (str): The Cyrillic script text to convert
        
    Returns:
        str: The Latin script equivalent
    """
    # Check for special case matches first
    if text.lower() in SPECIAL_CASE_MAPPING:
        result = SPECIAL_CASE_MAPPING[text.lower()]
        # If the result is a list (multiple variants), return the first one
        if isinstance(result, list):
            return result[0]
        return result
    
    # Process general case with character mapping
    result = ''
    i = 0
    while i < len(text):
        # Check for digraphs/trigraphs first (like "хъу", "гъу")
        if i < len(text) - 2 and text[i:i+3].lower() in CYRILLIC_TO_LATIN:
            char = text[i:i+3].lower()
            result += CYRILLIC_TO_LATIN[char]
            i += 3
        # Then check for digraphs (like "къ", "хъ")
        elif i < len(text) - 1 and text[i:i+2].lower() in CYRILLIC_TO_LATIN:
            char = text[i:i+2].lower()
            result += CYRILLIC_TO_LATIN[char]
            i += 2
        # Then check for single characters
        elif text[i].lower() in CYRILLIC_TO_LATIN:
            if text[i].isupper():
                result += CYRILLIC_TO_LATIN[text[i].lower()].upper()
            else:
                result += CYRILLIC_TO_LATIN[text[i].lower()]
            i += 1
        else:
            # If character not in mapping, keep it as is
            result += text[i]
            i += 1
    
    return result

def generate_variants(text):
    """
    Generate common spelling variants to improve typo tolerance.
    
    Args:
        text (str): The original text
        
    Returns:
        list: List of common spelling variants
    """
    variants = [text]
    
    for i, char in enumerate(text):
        if char.lower() in COMMON_VARIANTS:
            for variant_char in COMMON_VARIANTS[char.lower()]:
                variant = text[:i] + variant_char + text[i+1:]
                variants.append(variant)
    
    return list(set(variants))

def get_all_script_variants(text):
    """
    Generate all possible script variants for a given text.
    
    Args:
        text (str): The input text in either Latin or Cyrillic script
        
    Returns:
        list: A list of all possible script variants (both Latin and Cyrillic)
    """
    variants = set([text])  # Start with the original text
    
    # Add special case variants if available
    if text.lower() in SPECIAL_CASE_MAPPING:
        special_variants = SPECIAL_CASE_MAPPING[text.lower()]
        if isinstance(special_variants, list):
            variants.update(special_variants)
        else:
            variants.add(special_variants)
    
    # Add transliteration variant
    has_cyrillic = any(char in CYRILLIC_TO_LATIN for char in text.lower())
    
    if has_cyrillic:
        latin_variant = cyrillic_to_latin(text)
        variants.add(latin_variant)
        # Add common spelling variants of the Latin form
        variants.update(generate_variants(latin_variant))
    else:
        cyrillic_variant = latin_to_cyrillic(text)
        variants.add(cyrillic_variant)
        # Add common spelling variants of the original Latin form
        variants.update(generate_variants(text))
    
    return list(variants) 