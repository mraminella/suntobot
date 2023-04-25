# Dockerfile
FROM python:slim
WORKDIR /usr/local/bin
COPY . app
RUN pip install -r app/requirements.txt
CMD ["python", "app/app.py"]