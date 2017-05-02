FROM ubuntu:16.04

LABEL maintainer "Datagrid Systems, Inc. <support@datagridsys.com>"

WORKDIR /app

RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y --no-install-recommends \
	    python-pip python-setuptools \
        curl \
        python3 \
        python3-requests \
        python3-setuptools \
        python3-pip && \
    pip3 install --upgrade pip && \
    pip3 install docker

COPY plugin/swarm-exec lib/skpp.py /app/

ENTRYPOINT [ "./swarm-exec" ]