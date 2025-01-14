FROM python:3.12-bookworm

WORKDIR /app

RUN apt-get update -y
RUN apt-get install -y locales
RUN echo "locales locales/default_environment_locale select en_US.UTF-8" | debconf-set-selections
RUN echo "locales locales/locales_to_be_generated multiselect en_US.UTF-8 UTF-8" | debconf-set-selections
RUN rm /etc/locale.gen
RUN dpkg-reconfigure --frontend=noninteractive locales

RUN apt-get install -y golang-go
RUN go version
RUN go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@v4.16.2

RUN apt-get install -y cron
COPY config/crontab /etc/cron.d/cron-force
RUN chmod 0644 /etc/cron.d/cron-force
RUN crontab /etc/cron.d/cron-force

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /app

EXPOSE 80

CMD ["gunicorn", "manage:app", "--bind", "0.0.0.0:80", "--workers", "4"]