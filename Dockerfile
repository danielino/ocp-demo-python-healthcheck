FROM registry.redhat.io/rhel8/python-36

WORKDIR /opt/app-root/src

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "app.py"]
