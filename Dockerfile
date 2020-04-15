FROM registry.access.redhat.com/ubi8/ubi-minimal
LABEL maintainer "Red Hat OpenShift Dedicated SRE Team"

RUN microdnf install -y python3 python3-pip
RUN pip3 install openshift
RUN pip3 install kubernetes

RUN mkdir /app
WORKDIR /app

COPY . ./

ENTRYPOINT [ "/app/apischeme_SSS.py" ]