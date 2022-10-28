FROM python:3
WORKDIR /app
COPY . .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 8028
CMD bash start.sh /app/config/config.yaml 8028