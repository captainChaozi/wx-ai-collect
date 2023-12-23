import os
from flask import Flask, send_file
from app.wechat_file import WXFilehelper
from app.celery_task import celery_init_app
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url=os.environ.get('REDIS_URL', "redis://localhost:6379/0"),
        result_backend=os.environ.get(
            'REDIS_URL', "redis://localhost:6379/0"),
        task_ignore_result=True,
        broker_connection_retry_on_startup=True,
    ),
)
celery_app = celery_init_app(app)


@celery_app.task
def receive_msg(uuid):
    # 长时间运行的任务
    filehelper = WXFilehelper(uuid=uuid)
    filehelper.run()


app = Flask(__name__)
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


@app.route('/')
@auth.login_required
def home():
    filehelper = WXFilehelper()
    image = filehelper.get_qrcode()
    receive_msg.delay(filehelper.uuid)
    return send_file(image, mimetype='image/jpeg')

    # return render_template('index.html', image=image)


if __name__ == '__main__':
    app.run(debug=True)
