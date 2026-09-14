FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends bash nano sudo git python3 python3-venv python3-pip openssh-client openssh-server rsync tmux build-essential cmake gdb ca-certificates curl gnupg dpkg-dev && rm -rf /var/lib/apt/lists/*
RUN if getent passwd 1000 >/dev/null; then usermod -l student -d /home/student -m "$(getent passwd 1000 | cut -d: -f1)"; else useradd -m -u 1000 -s /bin/bash student; fi && if ! getent group student >/dev/null; then groupmod -n student "$(getent group 1000 | cut -d: -f1)"; fi && usermod -g student -s /bin/bash student && echo 'student:linuxlab' | chpasswd && mkdir -p /workspace /opt/course /opt/apt-repo /opt/wheels && chown student:student /workspace /home/student
COPY lab/science-requirements.txt /opt/course/science-requirements.txt
RUN python3 -m pip download --only-binary=:all: -r /opt/course/science-requirements.txt -d /opt/wheels
RUN apt-get update && cd /opt/apt-repo && apt-get download tree && dpkg-scanpackages . /dev/null > Packages && rm -rf /etc/apt/sources.list.d/* /var/lib/apt/lists/* && printf 'deb [trusted=yes] file:/opt/apt-repo ./\n' > /etc/apt/sources.list && chmod -R a+rX /opt/apt-repo /opt/wheels
COPY lab/ /opt/course/
COPY server/motor.py /opt/course/motor.py
RUN printf '#!/bin/sh\nexec python3 /opt/course/labtool.py "$@"\n' > /usr/local/bin/labtool && chmod +x /usr/local/bin/labtool /opt/course/entrypoint.sh && printf 'export PATH=/workspace/.venv/bin:$PATH\nexport MODELICAPATH=/opt/modelica\n' >> /home/student/.bashrc && chown student:student /home/student/.bashrc
RUN rm -f /etc/ssh/ssh_host_*
WORKDIR /workspace
ENTRYPOINT ["/opt/course/entrypoint.sh"]
CMD ["lab"]
