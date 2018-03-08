#!/bin/bash

bot_token="******"
chat_id="@******"
interval_in_seconds=30

source ./venv/bin/activate &&
python ./run.py $bot_token $chat_id $interval_in_seconds
