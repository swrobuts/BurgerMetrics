"""Kontaktdaten und Links erkennen, bevor Jev gefragt wird.

Zeichenketten wie E-Mail-Adressen, Telefonnummern und Links gehören zu Jevs
dokumentierten Schwächen. Reguläre Ausdrücke finden sie zuverlässiger.
"""
import re

MUSTER = {
    "E-Mail": re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)*\.[a-z]{2,}", re.IGNORECASE),
    # Deutsche Nummern: +49, 0049 oder 0, dann Vorwahl und mindestens vier Ziffern.
    "Telefonnummer": re.compile(r"(?<!\d)(\+49|0049|0)[\s/-]*\d{2,5}([\s/-]*\d){4,10}(?!\d)"),
    # Adressen mit http, www oder einer gängigen Endung; nicht der Teil nach @.
    "Link": re.compile(r"(https?://|www\.)\S+|(?<![@\w.-])[\w-]+\.(de|com|net|org|io|shop|info)\b(/\S*)?",
                       re.IGNORECASE),
}


def treffer(text):
    """Die Musterarten, die im Text vorkommen, in fester Reihenfolge."""
    return [name for name, ausdruck in MUSTER.items() if ausdruck.search(text or "")]
