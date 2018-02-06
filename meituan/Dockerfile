FROM python:3.5-alpine
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
meituan.jsonCMD ["python", "meituan_spider.py", "app.py"]