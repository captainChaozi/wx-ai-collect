import os
import datetime
from flask import Flask, send_file
from wechat_file import WXFilehelper
from flask_apscheduler import APScheduler
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


class Config:
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config.from_object(Config())
auth = HTTPBasicAuth()


users = {
    os.environ.get('USER_NAME'): generate_password_hash(os.environ.get('PASSWORD'))
}

# 验证函数


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


scheduler = APScheduler()

scheduler.init_app(app)
scheduler.start()


@app.route('/')
@auth.login_required
def home():
    filehelper = WXFilehelper()
    image = filehelper.get_qrcode()

    scheduler.add_job(id='job', func=filehelper.run,
                      trigger='date', run_date=datetime.datetime.now())
    return send_file(image, mimetype='image/jpeg')

    # return render_template('index.html', image=image)


if __name__ == '__main__':
    app.run(debug=True)
