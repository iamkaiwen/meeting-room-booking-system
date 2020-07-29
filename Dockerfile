FROM python:3.8-alpine
ADD ./code /code
WORKDIR /code
RUN pip install -r requirements.txt
RUN ["chmod", "+x", "wait-for-it.sh"]
CMD ["sh", "wait-for-it.sh", "db", "3306", "python main.py"]