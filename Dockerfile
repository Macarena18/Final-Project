FROM python:3.8-slim

ADD ./ ./

RUN pip3 install -r requirements.txt

EXPOSE 3500

CMD ["python3","-u", "api.py"]