FROM python:3-onbuild

RUN apt-get update

# Install and configure the zktesting script
# Code is automatically copied to /usr/src/app
RUN pip install -r /usr/src/app/requirements.txt

# Run that beautiful zktesting
WORKDIR /usr/src/app
CMD ["python", "zktesting.py"]