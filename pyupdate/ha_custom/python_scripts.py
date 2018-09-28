"""Logic to handle python_scripts."""
import os
import re
import requests
from requests import RequestException
from pyupdate.ha_custom import common


def _normalize_path(path):
    path = path.replace('/', os.path.sep)\
        .replace('\\', os.path.sep)

    if path.startswith(os.path.sep):
        path = path[1:]

    return path


def get_info_all_python_scripts(custom_repos=None):
    """Return all remote info if any."""
    remote_info = {}
    for url in common.get_repo_data('python_script', custom_repos):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                for name, py_script in response.json().items():
                    try:
                        py_script = [
                            name,
                            py_script['version'],
                            _normalize_path(
                                py_script['local_location']),
                            py_script['remote_location'],
                            py_script['visit_repo'],
                            py_script['changelog']
                        ]
                        remote_info[name] = py_script
                    except KeyError:
                        print('Could not get remote info for ' + name)
        except RequestException:
            print('Could not get remote info for ' + url)
    return remote_info


def get_sensor_data():
    """Get sensor data."""
    python_scripts = get_info_all_python_scripts()
    cahce_data = {}
    cahce_data['domain'] = 'python_scripts'
    cahce_data['has_update'] = []
    count_updateable = 0
    if python_scripts:
        for name, py_script in python_scripts.items():
            remote_version = py_script[1]
            local_version = get_local_version(py_script[2])
            has_update = (remote_version and
                          remote_version != local_version)
            not_local = (remote_version and not local_version)
            if has_update and not not_local:
                count_updateable = count_updateable + 1
                cahce_data['has_update'].append(name)
            cahce_data[name] = {
                "local": local_version,
                "remote": remote_version,
                "has_update": has_update,
                "not_local": not_local,
                "repo": py_script[4],
                "change_log": py_script[5],
            }
    return [cahce_data, count_updateable]


def update_all(base_dir):
    """Update all python_script."""
    updates = get_sensor_data()[0]['has_update']
    if updates is not None:
        for name in updates:
            upgrade_single(base_dir, name)


def upgrade_single(base_dir, name):
    """Update one python_script."""
    remote_info = get_info_all_python_scripts()[name]
    remote_file = remote_info[3]
    local_file = os.path.join(base_dir, remote_info[2])
    common.download_file(local_file, remote_file)


def install(base_dir, name):
    """Install single python_script."""
    if name in get_sensor_data()[0]:
        if '.' in name:
            python_script = str(name).split('.')[0]
            path = base_dir + '/python_scripts/' + python_script
            if not os.path.isdir(path):
                os.mkdir(path)
        upgrade_single(base_dir, name)


def get_local_version(local_path):
    """Return the local version if any."""
    return_value = ''
    if os.path.isfile(local_path):
        with open(local_path, 'r') as local:
            pattern = re.compile(r"^__version__\s*=\s*['\"](.*)['\"]$")
            for line in local.readlines():
                matcher = pattern.match(line)
                if matcher:
                    return_value = str(matcher.group(1))
    return return_value
