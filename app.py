import utils
import os.path
from flask import render_template
from flask import  send_from_directory
from datetime import timedelta
from jieba.analyse import extract_tags
from flask import Flask as _Flask,jsonify
from flask.json import JSONEncoder as _JSONEncoder
import string
import decimal


class JSONEncoder(_JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        super(_JSONEncoder, self).default(o)

class Flask(_Flask):
    json_encoder = JSONEncoder

app = Flask(__name__)

# 配置缓存更新时间
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1) #将缓存时间设置为一秒


#配置默认路由，指向模板页
@app.route('/')
def index():
    return render_template("main.html")

@app.route('/main')
def index2():
    return render_template("main.html")

@app.route('/index')
def index1():
    return render_template("index.html")


@app.route("/download/<filename>",methods=["GET"])
def download_file(filename):
    BASE_PATH = os.path.dirname(os.path.abspath(__file__)) #获取文件所在目录的完整路径
    dir = os.path.join(BASE_PATH,'download')
    return send_from_directory(dir,filename,as_attachment=True)


#配置中间C1部分数据格式
@app.route("/c1")
def get_c1_data():
    data = utils.get_c1_data()
    return jsonify({"confirm":data[0],"suspect":data[1],"heal":data[2],"dead":data[3]})

#配置中间C2部分数据格式
@app.route("/c2")
def get_c2_data():
    res = [] #创建空的list列表
    for tup in utils.get_c2_data():
        # print(tup)
        res.append({"name":tup[0],"value":int(tup[1])})
    return jsonify({"data":res})

#配置左边第一部分数据格式
@app.route("/l1")
def get_l1_data():
    data = utils.get_l1_data()
    day,confirm,suspect,heal,dead = [],[],[],[],[]
    for a,b,c,d,e in data[7:]:
        day.append(a.strftime("%m-%d"))
        #  a是datatime类型
        confirm.append(b)
        suspect.append(c)
        heal.append(d)
        dead.append(e)
    return jsonify({"day": day, "confirm": confirm, "suspect": suspect, "heal": heal, "dead": dead})

#配置左边第二部分数据格式
@app.route("/l2")
def get_l2_data():
    data = utils.get_l2_data()
    day, confirm_add, suspect_add = [], [], []
    for a, b, c in data[7:]:
        day.append(a.strftime("%m-%d"))  # a是datatime类型
        confirm_add.append(b)
        suspect_add.append(c)
    return jsonify({"day": day, "confirm_add": confirm_add, "suspect_add": suspect_add})

#配置右边第一部分数据格式
@app.route("/r1")
def get_r1_data():
    data = utils.get_r1_data()
    city = []
    confirm = []
    for k,v in data:
        city.append(k)
        confirm.append(int(v))
    return jsonify({"city": city, "confirm": confirm})

#配置右边第二部分数据格式
@app.route('/r2')
def get_r2_data():
    data = utils.get_r2_data()
    d = []
    for i in data:
        k = i[0].rstrip(string.digits)
        v = i[0][len(k):]
        ks = extract_tags(k)
        for j in ks:
            if not j.isdigit():
                d.append({"name": j,"value": v})
    return jsonify({"kws": d})

#获取服务器时间
@app.route("/time")
def get_time():
    return utils.get_time()

#主函数
if __name__ == '__main__':
    #app.run(host='127.0.0.1', port=5000)
    app.run()