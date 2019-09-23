#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "slave_server.settings")
    try:
        from django.core.management import execute_from_command_line
        import redis

        rds = redis.Redis(host='localhost', port=6379)
        rds_keys = ["atf_task_id", "atf_test_id", "case_name", "pid", "atf_progress", "atf_case_index", "atf_loop_index", "atf_config", "atf_current"]
        if not rds.get("atf_task_id"):
            for k in rds_keys:
                rds.set(k, None)
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
