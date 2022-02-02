# project-00xsynth

Workflow for automation of scraping of Tweets and verification on Discord

`airflow standalone`
Username and password are in the terminal output

```
ssh -i ~/Desktop/Project\ 00xsynth/dani.pem -L 0.0.0.0:8080:54.255.234.57:8080 ec2-user@54.255.234.57
sudo systemctl start airflow
sudo journalctl -u service-name.service
```

Printing and killing the processes

```
fuser 8080/tcp
fuser -k 8080/tcp
lsof -i tcp:8080
```

[How to Run Apache Airflow as Daemon Using Linux “systemd”](https://towardsdatascience.com/how-to-run-apache-airflow-as-daemon-using-linux-systemd-63a1d85f9702)
[Airflow on AWS EC2 - Python 3 Virtual Environment](https://medium.com/@itsmeviru/airflow-on-aws-ec2-python-3-virtual-environment-3c85a8b8da0f)
[Airflow on AWS EC2 instance with Ubuntu](https://medium.com/@abraham.pabbathi/airflow-on-aws-ec2-instance-with-ubuntu-aff8d3206171)
[How do I restart airflow webserver?](https://stackoverflow.com/questions/39073443/how-do-i-restart-airflow-webserver)
[How did you deploy Airflow into production? (AWS)](https://www.reddit.com/r/dataengineering/comments/dvyt8c/how_did_you_deploy_airflow_into_production_aws/)
[How to deploy Apache Airflow with Celery on AWS](https://towardsdatascience.com/how-to-deploy-apache-airflow-with-celery-on-aws-ce2518dbf631)
[Docker Airflow](https://github.com/puckel/docker-airflow)
