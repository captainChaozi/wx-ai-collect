import datetime
from flask import Flask, render_template
from wechat_file import WXFilehelper
from flask_apscheduler import APScheduler

app = Flask(__name__)


# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True


# create app
app = Flask(__name__)
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()


@app.route('/')
def home():
    filehelper = WXFilehelper()
    scheduler.add_job(id='job', func=filehelper.run,
                      trigger='date', run_date=datetime.datetime.now())

    # 这里添加 apschedue的后台任务

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
