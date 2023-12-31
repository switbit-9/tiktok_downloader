import logging
import os
import json

logger = logging.getLogger(__name__)
def delete_video(file_path):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        logger.error('DELETE : File not found:', file_path)
    except PermissionError:
        logger.error('DELETE : Permission denied to delete the file:', file_path)
    except Exception as e:
        logger.error('DELETE : An error occurred:', str(e))

def write_to_json(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        logger.error(e)
        return False

def read_json_file(filename):
    with open(filename, "r") as file:
        return json.load(file)