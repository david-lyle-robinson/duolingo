#!/usr/bin/sh

echo "================================================"
echo Today: `date`

max_attempts=5
attempt_num=1

until /home/robinson/src/python/duolingo/duolingo.py -headless || [ $attempt_num -ge $max_attempts ]; do
#until /home/robinson/src/python/duolingo/duolingo.py -stay || [ $attempt_num -ge $max_attempts ]; do
  echo "Attempt $attempt_num failed. Retrying..."
  sleep 90
  attempt_num=$((attempt_num + 1))
done

if [ $? -eq 0 ]; then
  echo "Command succeeded after $attempt_num attempts."
else
  echo "Command failed after $max_attempts attempts."
fi
