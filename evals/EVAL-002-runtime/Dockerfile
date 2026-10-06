# Source-free runtime: base must be the frozen EVAL-001 runner image.
FROM efficient-coding-eval-001:runner
COPY requirements.txt /opt/eval-requirements.txt
RUN /root/.local/bin/uv python install 3.8.20 \
 && rm -rf /opt/eval-venv \
 && /root/.local/bin/uv venv --python 3.8.20 /opt/eval-venv \
 && /root/.local/bin/uv pip install --python /opt/eval-venv/bin/python -r /opt/eval-requirements.txt \
 && /opt/eval-venv/bin/python -m ensurepip
ENV PATH="/opt/eval-venv/bin:$PATH"
