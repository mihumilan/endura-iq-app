#!/usr/bin/env bash

# Instalacja standardowych pakietów
pip install -r requirements.txt

# Instalacja przeglądarki Chromium
python -m playwright install chromium
