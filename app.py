import datetime
from flask import Flask, render_template
from wechat_file import WXFilehelper
from flask_apscheduler import APScheduler

app = Flask(__name__)


class Config:
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()

scheduler.init_app(app)
scheduler.start()


@app.route('/')
def home():
    filehelper = WXFilehelper()
    scheduler.add_job(id='job', func=filehelper.run,
                      trigger='date', run_date=datetime.datetime.now())
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
