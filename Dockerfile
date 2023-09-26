FROM python:alpine

ARG FOLDER_NAME

# Require to update the HOSTNAME and review the time-zone (TZ)
ENV HOSTNAME="YOUR_DOMAIN.dyndns.org"
ENV TZ="Hongkong"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apk update && apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Create a non-root user
RUN adduser -D worker

RUN mkdir -p /app/$FOLDER_NAME

RUN pip install cryptography
RUN pip install apscheduler
RUN pip install requests
RUN pip install tzlocal

COPY ./wrk/*.py /app/$FOLDER_NAME/
COPY ./wrk/*.config /app/$FOLDER_NAME/
RUN if [ ! -s /app/$FOLDER_NAME/main.config ]; then echo "HOSTNAME = \"$HOSTNAME\"" > /app/$FOLDER_NAME/main.config; else echo -e "\nHOSTNAME = \"$HOSTNAME\"" >> /app/$FOLDER_NAME/main.config; fi

RUN chown -R worker:worker /app/$FOLDER_NAME/
# Switch to the non-root user
USER worker

WORKDIR /app/$FOLDER_NAME/

CMD ["python", "main.py"]