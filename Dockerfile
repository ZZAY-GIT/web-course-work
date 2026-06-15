FROM mirror.gcr.io/library/python:3.11-slim

WORKDIR /app

COPY clinic_app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY clinic_app/ /app/clinic_app/

WORKDIR /app/clinic_app

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000


CMD ["sh", "-c", "mkdir -p static/uploads && if [ ! -f static/uploads/.seeded ]; then python seed.py && touch static/uploads/.seeded; fi && python app.py"]
