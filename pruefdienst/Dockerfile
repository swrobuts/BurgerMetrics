# Prüfdienst für BurgerMetrics: prüft neue Shop-Rezensionen mit Jev.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pruefdienst/requirements.txt pruefdienst/requirements.txt
RUN pip install --no-cache-dir -r pruefdienst/requirements.txt
COPY bm_jev/__init__.py bm_jev/fragen.py bm_jev/muster.py bm_jev/regeln.py bm_jev/jev.py bm_jev/datenbank.py bm_jev/
COPY pruefdienst/dienst.py pruefdienst/dienst.py
USER nobody
CMD ["python", "pruefdienst/dienst.py"]
