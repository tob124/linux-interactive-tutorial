#!/usr/bin/env bash
set -euo pipefail
python3 /opt/course/seed.py
chown -R student:student /workspace /home/student
if [ "${COURSE_WEEK:-0}" = 1 ] || [ "${COURSE_WEEK:-0}" = 6 ]; then
  echo 'student ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/course
  chmod 440 /etc/sudoers.d/course
else
  rm -f /etc/sudoers.d/course
fi
if [ "${1:-lab}" = remote ]; then
  mkdir -p /run/sshd
  ssh-keygen -A
  touch /tmp/course-ready
  exec /usr/sbin/sshd -D -e
fi
touch /tmp/course-ready
exec sleep infinity
