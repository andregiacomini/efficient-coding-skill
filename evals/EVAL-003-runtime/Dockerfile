# Base image identity is checked against the frozen EVAL-002 image before build.
# Source-free runtime: no Django package, benchmark dataset or gold answers.
FROM efficient-coding-eval-002:runner
COPY requirements.txt /opt/eval-003-requirements.txt
RUN /root/.local/bin/uv python install 3.10.16 \
 && /root/.local/bin/uv venv --python 3.10.16 /opt/eval-003-venv \
 && /root/.local/bin/uv pip install --python /opt/eval-003-venv/bin/python -r /opt/eval-003-requirements.txt
ENV PATH="/opt/eval-003-venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
