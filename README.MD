

# Message in a bottle
[![Build Status](https://app.travis-ci.com/fcarli3/message-in-a-bottle.svg?token=3N4JdWYn7QpiZ6F6wFdB&branch=main)](https://app.travis-ci.com/fcarli3/message-in-a-bottle)

## Installation

Execute the following commands:

```bash
python -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Run the application

Execute the following commands:
```bash
docker run -d -p 6379:6379 redis
./run.sh
```

To monitor Celery output:
```bash
tail -f nohup.out
```
