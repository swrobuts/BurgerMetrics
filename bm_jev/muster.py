"""Kontaktdaten und Links erkennen, bevor Jev gefragt wird.

Zeichenketten wie E-Mail-Adressen, Telefonnummern und Links gehören zu Jevs
dokumentierten Schwächen. Reguläre Ausdrücke finden sie zuverlässiger.
"""
import re

MUSTER = {
    "E-Mail": re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)*\.[a-z]{2,}", re.IGNORECASE),
    # Nummern aus Deutschland, Österreich und der Schweiz: +49, 0049, +43, +41 oder 0,
    # dann Vorwahl (auch in Klammern, auch mit „(0)“) und mindestens vier Ziffern.
    "Telefonnummer": re.compile(
        r"(?<![\d.,])((\+|00)(49|43|41)[\s/.-]*(\(0\)[\s/.-]*)?|\(?0)\d{2,5}\)?([\s/.-]*\d){4,10}(?!\d)"),
    # Adressen mit http, www oder einer gängigen Endung, auch mit Unterdomänen
    # wie shop.beispiel.de; nicht der Teil nach @.
    "Link": re.compile(
        r"(https?://|www\.)\S+"
        r"|(?<![@\w.-])[\w-]+(\.[\w-]+)*\.(de|at|ch|eu|com|net|org|io|co|me|ly|app|shop|info)\b(/\S*)?",
        re.IGNORECASE),
}


def treffer(text):
    """Die Musterarten, die im Text vorkommen, in fester Reihenfolge."""
    return [name for name, ausdruck in MUSTER.items() if ausdruck.search(text or "")]
