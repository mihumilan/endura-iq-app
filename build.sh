#!/usr/bin/env bash

# Instalacja standardowych pakietów
pip install -r requirements.txt

# Bezpieczna instalacja przeglądarki bezpośrednio przez moduł Pythona
python -m playwright install chromium

# Instalacja brakujących paczek systemowych Linuxa (KLUCZOWE NA SERWERZE!)
python -m playwright install-deps
