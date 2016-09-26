export TIMES=2 REDIS_URL=redis://h:p2pmvkju1jvenqa00jv07mf8h6n@ec2-184-73-182-113.compute-1.amazonaws.com:13869 && celery worker --app=core.tasks.app --loglevel=info
