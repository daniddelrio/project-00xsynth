from datetime import datetime, timedelta
from textwrap import dedent

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

from project_00xsynth.airflow_dag.pipeline_class import scrape_follows, scrape_liked, categorize_follows, track_watchlist, join_discord

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args = {
    'owner': 'daniddelrio',
    'depends_on_past': False,
    'email': ['00xsynth@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}
with DAG(
    'scrape_dag',
    default_args=default_args,
    description='DAG for scraping Twitter by tracking certain accounts',
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2022, 1, 13),
    catchup=False,
    tags=['example']
) as dag:

    t1 = scrape_follows()
    t2 = scrape_liked()
    t3 = categorize_follows()

    [t1, t2] >> t3

    # t1.doc_md = dedent(
    #     """\
    # #### Task Documentation
    # You can document your task using the attributes `doc_md` (markdown),
    # `doc` (plain text), `doc_rst`, `doc_json`, `doc_yaml` which gets
    # rendered in the UI's Task Instance Details page.
    # ![img](http://montcs.bloomu.edu/~bobmon/Semesters/2012-01/491/import%20soul.png)

    # """
    # )

    # dag.doc_md = __doc__  # providing that you have a docstring at the beginning of the DAG
    # dag.doc_md = """
    # This is a documentation placed anywhere
    # """  # otherwise, type it like this
    # templated_command = dedent(
    #     """
    # {% for i in range(5) %}
    #     echo "{{ ds }}"
    #     echo "{{ macros.ds_add(ds, 7)}}"
    #     echo "{{ params.my_param }}"
    # {% endfor %}
    # """
    # )

with DAG(
    'watchlist_dag',
    default_args=default_args,
    description='DAG for tracking the watchlist to see if they have a Discord link',
    schedule_interval=timedelta(minutes=60),
    start_date=datetime(2022, 1, 13),
    catchup=False,
) as dag_2:

    t1 = track_watchlist()

with DAG(
    'discord_dag',
    default_args=default_args,
    description='DAG for joining the Discord servers stored in the DB.',
    schedule_interval=timedelta(minutes=45),
    start_date=datetime(2022, 1, 13),
    catchup=False,
) as dag_3:

    t1 = join_discord()
