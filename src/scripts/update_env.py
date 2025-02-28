import os


def find_env_file(env_file: str = '.env') -> str:
    """Ищет .env файл в текущей или родительских директориях."""
    current_dir = os.getcwd()
    while True:
        potential_path = os.path.join(current_dir, env_file)
        if os.path.exists(potential_path):
            return potential_path
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    raise FileNotFoundError(f"{env_file} not found")


def update_env_variable(key: str, value: str, env_file: str = '.env'):
    """Обновляет указанную переменную в .env файле или добавляет, если её нет."""
    env_file = find_env_file(env_file)
    lines = []
    found = False

    with open(env_file, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}\n'
            found = True
            break

    if not found:
        lines.append(f'{key}={value}\n')

    with open(env_file, 'w') as file:
        file.writelines(lines)


def set_proxy(ip: str, port: int, login: str, password: str):
    """Заменяет переменную PROXY в формате login:password@ip:port"""
    proxy_value = f'{login}:{password}@{ip}:{port}'
    update_env_variable('PROXY', proxy_value)


def set_compare_rating(value: str):
    """Заменяет переменную COMPARE_RATING."""
    update_env_variable('COMPARE_RATING', value)


def set_delta_threshold(value: str):
    """Заменяет переменную DELTA_THRESHOLD."""
    update_env_variable('DELTA_THRESHOLD', value)


update_env_variable("DELTA_THRESHOLD", 1)
