#!/bin/bash
# cd ~/project/stockerCrawler
cd ~/stocker/stocker-crawler
source venv/bin/activate
python3 criticalInfoNotifier.py
deactivate
exit 0
