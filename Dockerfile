# Contained environment for the AutoPYara ACSAC 2026 artifact.
#
# Pinned Python 3.12 + OpenJDK 17 + the dependency set in
# artifact/requirements-lock.txt, so evaluation does not depend on the host.
#
# BUILD (from the repository root; ~10-20 min, most of it the Bloom filter download)
#
#     docker build -t autopyara-artifact .
#
# FETCH THE EVALUATION DATA onto the host once (claims 4-9), then mount it:
#
#     mkdir -p data
#     docker run --rm -v "$PWD/data:/opt/artifact/data" autopyara-artifact \
#         python3 artifact/download_data.py
#
# RUN
#
#     # every claim
#     docker run --rm -it --memory=16g -v "$PWD/data:/opt/artifact/data" \
#         autopyara-artifact ./run_all_claims.sh -j 8
#
#     # a single claim, or an interactive shell
#     docker run --rm -it --memory=16g autopyara-artifact ./claims/claim1_install/run.sh
#     docker run --rm -it --memory=16g -v "$PWD/data:/opt/artifact/data" autopyara-artifact bash
#
#     # keep the regenerated figures: also mount results/
#     ... -v "$PWD/results:/opt/artifact/results" ...
#
# MEMORY
#     The JVM of claims 1-3 is started with a fixed 14 GB maximum heap; give the
#     container at least 16 GB or the kernel may kill it mid-run. Claims 4-9 need
#     well under 8 GB. See infrastructure/constraints.txt.

FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/artifact

# Dependencies first (pinned, including autopyara==0.1.2), so this layer caches
# independently of the artifact's own files.
COPY artifact/requirements-lock.txt /tmp/requirements-lock.txt
RUN python3 -m pip install -r /tmp/requirements-lock.txt

# AutoPYara's pre-trained Bloom filters (~600 MB), baked in so the tool claims run offline.
RUN autopyara-download

# Fail at build time, not at evaluation time, if the JVM cannot start.
RUN python3 -c "from autopyara import AutoPYara; AutoPYara(); print('JVM OK')"

COPY . /opt/artifact
RUN chmod +x install.sh run_all_claims.sh claims/*/run.sh

CMD ["bash", "-lc", "echo 'AutoPYara artifact container. Try: ./run_all_claims.sh -j 8 (mount the data at /opt/artifact/data)'; exec bash"]
