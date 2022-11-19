import mimetypes
import os
import threading
import time
import base64
from flask import Flask, request, send_file, redirect, make_response, abort
from DiskManager import DiskManager
from tools import *

disk_manager = DiskManager(sys.argv[1:])
root = disk_manager.disk_manager_dir
PORT = 80
get_preview_lock = threading.Semaphore(4)
app = Flask(__name__, static_url_path="", static_folder=resource_path('static'),
            template_folder=resource_path("templates"))


def require_login_with_callback(**kwargs):
    def a(fn):
        def b(*args, **kwargs_):
            token = verify_jwt(get_token(request))
            if token:
                return fn(*args, **kwargs_)
            else:
                return kwargs['callback'](kwargs['args'], **kwargs_)
        a.__name__ = fn.__name__
        return b
    return a


def require_login(fn):
    def a(*args, **kwargs):
        return require_login_with_callback(callback=abort, args=403)(fn)(*args, **kwargs)
    a.__name__ = fn.__name__
    return a


@app.route('/')
@require_login_with_callback(callback=redirect, args='/login')
def send_index_html():
    return send_html('index.html')


def send_html(path):
    return app.send_static_file(path), 200, [("Cache-Control", "no-cache, no-store, must-revalidate"),
                                             ("Pragma", "no-cache"), ("Expires", "0"),
                                             ("Cache-Control", "public, max-age=0")]


@app.route('/login')
def send_login_html():
    return send_html('login.html')


@app.route('/getAssets')
def send_assets():
    res = request.args.get("res")
    path = request.args.get("path")
    if res.startswith("mime-type-icon/video/") and path:
        return get_video_preview(path)
    return app.send_static_file(res)


@app.route('/getFileList')
@require_login
def send_file_list():
    json_array = []
    token = verify_jwt(get_token(request))
    for f in disk_manager.listdir(request.args.get("path")):
        mime = mimetypes.guess_type(f)[0]
        user_level_bookmark = path_join(disk_manager.bookmark_cache_dir, token['user'])
        bookmark_flag_file = path_join(user_level_bookmark, name_from_path(f) + '.b')
        if os.path.isdir(path_join(root, f)) and not os.path.exists(triple_path_join(root, f, '.cover')):
            # skip folders that might not contains media file
            continue
        score = -1
        title = ""
        if os.path.isfile(path_join(root, f)):
            if ("application/octet-stream" if mime is None else mime).startswith('video/'):
                f_type = "File"
            elif not f[f.rindex('/') + 1:].startswith('.'):
                f_type = "Attach"
            else:
                continue
            watch_flag = "watched" if os.path.exists(bookmark_flag_file) else ""
        else:
            f_type = "Directory"
            _album = path_join(root, f)
            watch_flag = "watched" if False not in [os.path.exists(path_join(user_level_bookmark, e + '.b')) for e in
                                                    os.listdir(_album) if is_video(e)] else ""
            if os.path.exists(triple_path_join(root, f, '.info')):
                with open(triple_path_join(root, f, '.info'), 'r', encoding='utf-8') as f1:
                    j = json.loads(f1.read())
                    score = j['user_score_chart']
                    title = j['title']
        json_array.append({
            "name": f,
            "length": os.path.getsize(path_join(root, f)) if os.path.isfile(path_join(root, f)) else 0,
            "lasts": time_lasts(path_join(root, f)),
            "bitrate": bit_rate(path_join(root, f)),
            "desc": time.ctime(os.path.getmtime(path_join(root, f))),
            "type": f_type,
            "mime_type": "application/octet-stream" if mime is None else mime,
            "watched": watch_flag,
            "score": score,
            "title": title,
            "bookmark_state": "bookmark_add" if not os.path.exists(bookmark_flag_file) else "bookmark_added"
        })
    return json.dumps(json_array), 200, {"Content-Type": "application/json"}


@app.route('/toggleBookmark')
@require_login
def toggle_bookmark():
    token = verify_jwt(get_token(request))
    path = request.args.get("path")
    user_level_bookmark = path_join(disk_manager.bookmark_cache_dir, token['user'])
    if not os.path.exists(user_level_bookmark):
        os.mkdir(user_level_bookmark)
    bookmark_flag_file = path_join(user_level_bookmark, name_from_path(path) + '.b')
    state = os.path.exists(bookmark_flag_file)
    if state:
        os.remove(bookmark_flag_file)
    else:
        with open(bookmark_flag_file, 'w') as fp:
            fp.write("This is a Bookmark file!")
    return "成功取消标记" if state else "成功标记为看过"


@app.route("/getFile/<file_name>")
@require_login
def get_file(file_name):
    # url中加一个文件名避免播放器不知道视频文件名
    path = request.args.get('path')
    return get_file_core(path)


@app.route("/getFile2/<file_name>")
@require_login
def get_file2(file_name):
    # 使用based64
    path = request.args.get('path')
    return get_file_core(base64.urlsafe_b64decode(path.encode()).decode())


def get_file_core(path):
    if str(os.path.abspath(path_join(root, path))).startswith(os.path.abspath(root)):
        return send_file(path_join(root, path), as_attachment=True, download_name=name_from_path(path),
                         conditional=True)
    else:
        return abort(404)


@app.route("/getVideoPreview")
@require_login
def get_video_preview(_path=None):
    path = _path if _path else request.args.get("path")
    new_file = path_join(disk_manager.preview_cache_dir, name_from_path(path) + '.jpg')
    if not os.path.exists(new_file):
        if get_preview_lock.acquire():
            try:
                os.system(f'ffmpeg -i \"{path_join(root, path)}\" -ss 00:00:05.000 -vframes 1 \"{new_file}\"')
            except BaseException as a:
                print(a.__str__())
                return a.__str__()
            finally:
                get_preview_lock.release()
    return send_file(new_file)
    

@app.route("/getCover")
@require_login
def get_cover():
    return send_file(triple_path_join(root, request.args.get('cover'), '.cover'))


@app.route("/getDeviceName")
def get_device_name():
    import platform
    return platform.node()


@app.route("/getDeviceInfo")
def get_device_info():
    from plugin.logger import get_temp_value
    return dict(temp=get_temp_value(), fan=True)


@app.route("/notify")
def get_notify():
    return send_html('notify.html')


@app.route("/userLogin")
def user_login(name=None, psw=None):
    name = name if name else request.args.get("name")
    psw = psw if psw else request.args.get("psw")
    with open(resource_path('') + "user.json", 'r') as f:
        j = json.loads(f.read())
        if name in j:
            if j[name] == psw:
                # verification passed
                response = make_response(dict(code=200, msg='ok'))
                if not verify_jwt(get_token(request)):
                    token = gen_jwt(dict(user=name))
                    response.set_cookie('token', token, max_age=604800)
                return response
            else:
                return dict(code=-1, msg="密码错误")
        else:
            return dict(code=-1, msg="用户不存在")


@app.route("/remote_download", methods=['POST', 'GET'])
def add_remote_download():
    if request.method == 'GET':
        return send_html('remote_download.html')
    from pyaria2 import Aria2RPC
    out = request.form['out']
    url = request.form['url']
    jsonrpc = Aria2RPC(token="0930")
    season_name = get_season_name(out)
    season_name = camel(season_name.replace(".", " ") if season_name else "")
    options = {"out": out,
               "dir": triple_path_join(disk_manager.disk_manager_dir,
                                       disk_manager.get_max_avl_disk('Download' if not season_name else season_name),
                                       'Download' if not season_name else season_name),
               "user-agent": "AndroidDownloadManager/9 (Linux; U; Android 9; MIX 2 Build/PKQ1.190118.001)"}
    jsonrpc.addUri([url], options=options)
    return "<script>window.close();</script>", 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == '__main__':
    logo = r"""
                                                  __                                          
                                                 /\ \__                                       
     _____      __      __       ___     __  __  \ \ ,_\             ___       __       ____  
    /\ '__`\  /'__`\  /'__`\   /' _ `\  /\ \/\ \  \ \ \/   _______ /' _ `\   /'__`\    /',__\ 
    \ \ \L\ \/\  __/ /\ \L\.\_ /\ \/\ \ \ \ \_\ \  \ \ \_ /\______\/\ \/\ \ /\ \L\.\_ /\__, `\
     \ \ ,__/\ \____\\ \__/.\_\\ \_\ \_\ \ \____/   \ \__\\/______/\ \_\ \_\\ \__/.\_\\/\____/
      \ \ \/  \/____/ \/__/\/_/ \/_/\/_/  \/___/     \/__/          \/_/\/_/ \/__/\/_/ \/___/ 
       \ \_\                                                                                  
        \/_/                                                         build.2021.8.3 by 花生酱啊
    """
    print(f"\033[1;33m{logo}\033[0m")
    start_services()
    app.run(host="::", port=PORT)
