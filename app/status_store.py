from threading import Lock

status_store = {}
status_lock = Lock()

def set_status(task_id, status):
    with status_lock:
        status_store[task_id] = status

def get_status(task_id):
    with status_lock:
        return status_store.get(task_id, None) 