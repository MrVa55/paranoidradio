#!/bin/bash
# Activate the virtual environment
source /home/radio/paranoidradio/venv/bin/activate

# Start rowdyradio
python /home/radio/paranoidradio/rowdyradio.py >> /home/radio/paranoidradio/rowdy.log

# Start paranoid_radio
python /home/radio/paranoidradio/paranoid_radio.py >> /home/radio/paranoidradio/paranoid.log