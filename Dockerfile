FROM amazonlinux:2

RUN yum install -y \
  python3 \
  zip

WORKDIR /data

RUN echo -e '\
  #!/bin/bash
  cp -a /src/* /data\n\
  pip3 install --requirement requirements.txt --upgrade --target .\n\
  zip -r packaged.zip . && cp packaged.zip /src\n\
  ' > /entry.sh && chmod +x /entry.sh

ENTRYPOINT ["/bin/bash"]
CMD ["-c", "/entry.sh"]