FROM python:3.8

RUN pip install "git+https://github.com/Alvearie/acd-extension-framework/#egg=acd-annotator-python&subdirectory=acd-annotator-python"

#Copy the ASGI app that we want to the place Uvicorn expects it
COPY code_resolution_annotator.py /app/

EXPOSE 9443

# non-ssl
CMD ["uvicorn", "app.code_resolution_annotator:app", "--host", "0.0.0.0", "--port", "9443", "--factory"]

# ssl-enabled variant (to integrate with ACD, these keys should be generated via OpenShift where your ACD instance is deployed)
# CMD ["uvicorn", "app.code_resolution_annotator:app", "--host", "0.0.0.0", "--port", "9443", "--factory", "--ssl-keyfile", "/ssl/tls.key", "--ssl-certfile", "/ssl/tls.crt", "--ssl-ciphers", "TLSv1.2"]
