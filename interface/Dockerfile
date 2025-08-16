FROM python:3.10
RUN apt-get update && apt-get install -y iputils-ping
RUN pip3 install fastapi uvicorn
COPY ./* /app/
ENV PYTHONPATH "${PYTHONPATH}:/app/"
RUN pip install -r /app/requirements.txt
EXPOSE 8888 
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8888"]