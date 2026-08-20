# Minimal build image for the songbook (LuaLaTeX + songs/songidx + CMU fonts).
# Build:  docker build -t songbook .
# Run:    docker run --rm -v "$PWD:/songbook" songbook a4
#         docker run --rm -v "${PWD}:/songbook" songbook all   (PowerShell)
FROM debian:bookworm-slim

RUN apt-get update && apt-get install --no-install-recommends -y \
        texlive-luatex \
        texlive-latex-recommended \
        texlive-music \
        texlive-lang-czechslovak \
        texlive-lang-english \
        texlive-lang-cyrillic \
        texlive-lang-european \
        fonts-cmu \
        python3 \
        locales \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i 's/^# *cs_CZ.UTF-8/cs_CZ.UTF-8/; s/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen \
    && locale-gen

ENV LANG=cs_CZ.UTF-8

WORKDIR /songbook

# The repository (including the vendored script/songidx) is bind-mounted at /songbook.
ENTRYPOINT ["bash", "script/build.sh"]
CMD ["all"]
