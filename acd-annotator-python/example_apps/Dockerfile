FROM python:3.8

RUN pip install "git+https://github.com/Alvearie/acd-extension-framework/#egg=acd-annotator-python&subdirectory=acd-annotator-python"

#Copy the ASGI app that we want to the place Uvicorn expects it
COPY code_resolution_annotator.py /app/

EXPOSE 80

CMD ["uvicorn", "app.code_resolution_annotator:app", "--host", "0.0.0.0", "--port", "80", "--factory"]