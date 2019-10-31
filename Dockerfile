# Version 1.0 template-transformer-simple 

FROM agpipeline/gantry-base-image:latest
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

# Build environment values
ARG arg_terra_stereo_rgb_url=https://github.com/terraref/stereo_rgb.git
ENV terra_stereo_rgb_url=$arg_terra_stereo_rgb_url

ARG arg_terra_stereo_rgb_branch=master
ENV terra_stereo_rgb_branch=$arg_terra_stereo_rgb_branch

COPY requirements.txt packages.txt /home/extractor/

USER root

RUN [ -s /home/extractor/packages.txt ] && \
    (echo 'Installing packages' && \
        apt-get update && \
        cat /home/extractor/packages.txt | xargs apt-get install -y --no-install-recommends && \
        rm /home/extractor/packages.txt && \
        apt-get autoremove -y && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*) || \
    (echo 'No packages to install' && \
        rm /home/extractor/packages.txt)

RUN python3 -m pip install --no-cache-dir -r /home/extractor/requirements.txt && \
    rm /home/extractor/requirements.txt

# Install from source
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git && \
    git clone $terra_stereo_rgb_url --branch $terra_stereo_rgb_branch --single-branch "/home/extractor/stereo_rgb" && \
    cp -r "/home/extractor/stereo_rgb/terraref" "/home/extractor/terraref" && \
    rm -rf /home/extractor/stereo_rgb && \
    apt-get remove -y \
        git && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER extractor

COPY *.py /home/extractor/
