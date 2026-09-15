# Lokale Sicherheitstests

Voraussetzungen: Docker, OpenSSL und Python mit `pytest`, `psycopg2-binary`
und den Abhängigkeiten aus `mcp/requirements.txt`.

```bash
BM_TEST_PYTHON=mcp/.venv/bin/python bash db/tests/security_local.sh -q
```

Der Runner erstellt einen frischen PostgreSQL-17-Container mit einem nur für
`localhost` gültigen Testzertifikat. Er verwendet ausschließlich synthetische
Testdaten und eigene Testzugänge; Container und Volume werden anschließend
entfernt. Er kontaktiert keine Supabase- oder Web-Endpunkte.

Geprüft werden die alte Transaktionsumgehung über MCP in beiden Betriebsarten,
Lesen und Betreiberzugriffe, Zertifikatsprüfung aller vier Python-Zugänge,
Bestellungen mit fehlender oder wechselnder Sitzungskennung, Parallelzugriffe,
historische Daten, Rechnungsbeträge und die wiederholte Anwendung der Migration.
Die bestehenden Rechte- und Materialisierungstests laufen ebenfalls.

`test_security_boundaries.py` lässt sich auch direkt über `BM_SECURITY_TEST_DSN`
und `BM_SECURITY_TEST_CA` starten. **Nur eine leere, wegwerfbare lokale Instanz
verwenden:** Diese Tests legen Rollen und Schemata an und ändern Instanzrechte.
Ohne diese Variablen werden die Integrationstests übersprungen.
