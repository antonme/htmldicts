# Ossetian Transliteration in the Dictionary Search API

This document explains the transliteration system implemented in the Dictionary Search API to improve search capabilities across different script variants of Ossetian words.

## Overview

Ossetian language texts can be written in two different scripts:

1. **Cyrillic script** - The official script used in North Ossetia–Alania (Russia)
2. **Latin script** - Used in academic publications, linguistic works, and sometimes in South Ossetia

Our dictionaries contain entries in both scripts, which means that searching for a term in one script might miss relevant results written in the other script. The transliteration system addresses this issue by automatically converting search terms between scripts and combining the search results.

## Scholarly Transcription System

The transliteration system follows scholarly conventions for Ossetian with these specific features:

- **æ/ä**: Both forms are recognized (æ is transcribed as ä in some scholarly works)
- **у/ә**: The Cyrillic 'у' is sometimes transcribed as 'ә' rather than 'u'
- **Glottal stops**: Marked with apostrophes (k', p', t', c')
- **Iron dialect affricates**: Derived from k, g, k' are represented as k, g, k'
- **Secondary labialization**: Marked with a small circle (kẜ, gẜ, k'ẜ) rather than 'w'
- **Indo-European palatalized sounds**: Represented as ḱ, ǵ

This academic transliteration system has two key advantages:
1. Iron dialect words are not separated from related Digor dialect words
2. Etymological relationships are more visible

## How Transliteration Works

When transliteration is enabled (which is the default behavior), the system:

1. Takes your search query (in either Latin or Cyrillic script)
2. Generates script variants using transliteration rules
3. Also generates common spelling variants to improve typo tolerance
4. Searches for all variants in the dictionary database
5. Combines and deduplicates the results
6. Ranks the combined results by relevance

This approach ensures you can find all relevant dictionary entries regardless of which script they use and accommodates common variations in spelling.

## Examples

The transliteration system allows you to find matches across script variants. For example:

| Original Search Term | Also Finds Matches For |
|----------------------|------------------------|
| tærqūs               | тæрхъус                |
| tärqūs               | тæрхъус                |
| тæрхъус              | tærqūs, tærqos, tärqūs |
| kẜyd                 | хъуыд                  |
| k'ẜym                | къуым                  |

## Using Transliteration in API Requests

The transliteration feature is controlled by a `transliteration` parameter available in all search endpoints:

### GET Request

```
GET /search?query=tærqūs&transliteration=true
```

### POST Request

```json
POST /search
{
  "query": "тæрхъус",
  "limit": 10,
  "transliteration": true
}
```

## Disabling Transliteration

If you want to search only for the exact script variant that you provided, you can disable the transliteration feature:

```
GET /search?query=tærqūs&transliteration=false
```

## Transliteration Character Mappings

The system uses a carefully constructed mapping between Latin and Cyrillic characters based on standard Ossetian transliteration conventions. Some notable mappings include:

| Latin | Cyrillic |  | Latin | Cyrillic |
|-------|----------|-|-------|----------|
| æ, ä  | æ        |  | k'    | къ       |
| q     | хъ       |  | p'    | пъ       |
| ğ     | гъ       |  | t'    | тъ       |
| ә     | у        |  | c'    | цъ       |
| š     | ш        |  | kẜ    | хъу      |
| ž     | ж        |  | gẜ    | гъу      |

## Typo Tolerance

The system includes additional typo tolerance by generating common spelling variants:

| Character | Common Variants |
|-----------|----------------|
| æ, ä      | a, e           |
| ū         | u              |
| ә         | u, y           |
| ẜ         | w              |
| ğ         | gh             |
| š         | sh             |
| ž         | zh             |
| č         | ch             |

## Special Cases

Some words have specific transliteration rules or multiple acceptable variants. These special cases are handled explicitly in the system. For example:

- `tærqūs`, `tærqos`, `tärqūs`, and `tärqos` are all valid Latin variants for the Cyrillic `тæрхъус`

## Limitations

The transliteration system has some limitations:

1. It focuses primarily on Ossetian-specific character mappings and may not handle all loanwords or dialectal variations perfectly.
2. Words with multiple valid transliterations might prioritize one variant over others.
3. Processing multiple search queries can increase response time slightly, though this is generally negligible.
4. Some very specialized scholarly notations might not be fully supported.

## Future Improvements

Potential improvements to the transliteration system include:

1. Adding more special case mappings for common words with irregular transliterations
2. Implementing context-aware transliteration for ambiguous characters
3. Incorporating more comprehensive support for historical and academic notations
4. Adding support for additional Ossetian dialects 