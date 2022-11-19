import datetime
import json
import jwt
import sys


def file_size_desc(size):
    if size >> 30 >= 1.0:
        return f'{size / (1024 * 1024 * 1024):.2f}GB'
    if size >> 20 >= 1.0:
        return f'{size / (1024 * 1024):.2f}MB'
    if size >> 10 >= 1.0:
        return f'{size / 1024:.2f}KB'
    return f'{size:.2f}B'


def get_season_name(name: str):
    import re
    regex = r"(.*\.S\d+)"
    matches = re.finditer(regex, name, re.MULTILINE | re.IGNORECASE)
    for matchNum, match in enumerate(matches, start=1):
        return match.group(1).replace('.', ' ').strip()
    return None


def start_services():
    # Using terminal instead, this is only A web server.
    pass


def path_join(parent, file) -> str:
    parent = parent.replace("\\", "/")
    file = file.replace("\\", "/")
    parent = parent[1 if parent.startswith("/") else 0:-1 if parent.endswith("/") else len(parent)]
    file = file[1 if file.startswith("/") else 0:-1 if file.endswith("/") else len(file)]
    return parent + '/' + file


def triple_path_join(parent, file, child) -> str:
    return path_join(path_join(parent, file), child)


def name_from_path(path):
    return path[path[:-1].rfind("/") + 1:]


def resource_path(relative_path):
    return sys.path[0] + '/' + relative_path


def get_token(request):
    token = request.args.get('token')
    if token:
        return token
    token = request.cookies.get('token')
    if token:
        return token


def gen_jwt(payload):
    with open(resource_path('') + "app.json", 'r') as f:
        j = json.loads(f.read())['JWT']
        _payload = dict(exp=datetime.datetime.now() + datetime.timedelta(days=7))
        _payload.update(payload)
        return jwt.encode(_payload, j['secret'], algorithm=j['algorithm'])


def time_lasts(file_path):
    import os
    import mimetypes
    import subprocess

    bit_rate_cache_file = "bit_rate_cache.json"
    if os.path.isfile(file_path) and (mimetypes.guess_type(file_path)[0].startswith('video/') if mimetypes.guess_type(file_path)[0] else False):
        bit_rate_cache = {}
        if os.path.exists(bit_rate_cache_file):
            with open(bit_rate_cache_file, 'r', encoding='utf-8') as f:
                bit_rate_cache = json.loads(f.read())
        if file_path in bit_rate_cache:
            result = bit_rate_cache[file_path]
        else:
            result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                     "format=duration", "-of",
                                     "default=noprint_wrappers=1:nokey=1", file_path],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            result = float(result.stdout)
            bit_rate_cache[file_path] = result
            with open(bit_rate_cache_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(bit_rate_cache, ensure_ascii=False, indent=4))
        return result
    else:
        return -1


def bit_rate(file_path):
    import math
    import os
    result = time_lasts(file_path)
    if result > 0:
        return str(math.ceil(8 * os.path.getsize(file_path) / (result * 1024 * 1024))) + "Mbps"
    else:
        return ""


def verify_jwt(token):
    if not token:
        return None
    with open(resource_path('') + "app.json", 'r') as f:
        j = json.loads(f.read())['JWT']
        try:
            payload = jwt.decode(token, j['secret'], algorithms=j['algorithm'])
        except jwt.PyJWTError as e:
            print(e)
            payload = None
        return payload


def is_video(file):
    import mimetypes
    return mimetypes.guess_type(file)[0].startswith('video/') if mimetypes.guess_type(file)[0] else False


def camel(name: str):
    r = []
    for i in name.split(" "):
        r.append(i.upper()[0] + (i.lower()[1:]) if len(i) > 1 else "")
    return ' '.join(r)
