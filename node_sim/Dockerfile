FROM python:3.9-slim

WORKDIR /app

COPY node.py /app/
COPY requirements.txt /app/

RUN pip install -r requirements.txt

ENV CPU_CORES=2

CMD ["python", "node.py"] 