import sys
import pymysql
import time
import json
import traceback  #追踪异常
import requests
from bs4 import BeautifulSoup
import re

import warnings

warnings.catch_warnings()

warnings.simplefilter("ignore")
def get_tencent_data():
    """
    :return: 此方法返回历史数据和当日详细数据
    """
    url = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5'
    url_his = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_other'  # 加上这个history大兄弟++++++++
	#添加headers
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    }
    r = requests.get(url, headers)
    res = json.loads(r.text)  # json字符串转字典
    data_all = json.loads(res['data'])

    # 添加history的相关信息
    r_his = requests.get(url_his, headers)
    res_his = json.loads(r_his.text)
    data_his = json.loads(res_his['data'])

    history = {}  # 历史数据

    for i in data_his["chinaDayList"]:
        year = i["y"]
        if year == "2020":
            ds = "2020." + i["date"]
        else:
            ds = year+ "." + i["date"]
        tup = time.strptime(ds, "%Y.%m.%d")
        ds = time.strftime("%Y-%m-%d", tup)  # 改变时间格式,不然插入数据库会报错，数据库是datetime类型
        confirm = i["confirm"]
        suspect = i["suspect"]
        heal = i["heal"] # 治愈人数
        dead = i["dead"] # 死亡人数
        history[ds] = {"confirm": confirm, "suspect": suspect, "heal": heal, "dead": dead}

    for i in data_his["chinaDayAddList"]:
        year = i["y"]
        if year == "2020":
            ds = "2020." + i["date"]
        else:
            ds = year+ "." + i["date"]
        tup = time.strptime(ds, "%Y.%m.%d")
        ds = time.strftime("%Y-%m-%d", tup)
        confirm = i["confirm"]
        suspect = i["suspect"]
        heal = i["heal"]
        dead = i["dead"]
        history[ds].update({"confirm_add": confirm, "suspect_add": suspect, "heal_add": heal, "dead_add": dead})

    # 获取当日疫情相关数据
    details = []  # 当日详细数据，返回的数据为最后更新时间，省名，市名，确诊人数，新增确诊人数，治愈人数，死亡人数
    update_time = data_all["lastUpdateTime"]
    data_country = data_all["areaTree"]  # list 25个国家
    data_province = data_country[0]["children"]  # 第一个元素内存取的是中国各省数据
    for pro_infos in data_province:
        province = pro_infos["name"]  # 省名
        for city_infos in pro_infos["children"]: #市名
            city = city_infos["name"]
            confirm = city_infos["total"]["confirm"] #确诊人数
            confirm_add = city_infos["today"]["confirm"] #确诊增加人数
            heal = city_infos["total"]["heal"] #治愈人数
            dead = city_infos["total"]["dead"] #死亡人数
            details.append([update_time, province, city, confirm, confirm_add, heal, dead]) # 在列表尾部添加新对象
    return history, details


def get_conn():
    """
    :return: 连接，游标
    """
    # 创建连接
    conn = pymysql.connect(host="127.0.0.1",
                           user="root",
                           password="zx1999818",
                           db="cov",
                           charset="utf8")
    # 创建游标
    cursor = conn.cursor()  # 执行完毕返回的结果集默认以元组显示
    return conn, cursor


def close_conn(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()


def update_details():
    """
    更新 details 表
    :return:
    """
    cursor = None
    conn = None
    try:
        li = get_tencent_data()[1]  #  0 是历史数据字典,1 最新详细数据列表
        conn, cursor = get_conn()
        sql = "insert into details(update_time,province,city,confirm,confirm_add,heal,dead) values(%s,%s,%s,%s,%s,%s,%s)"
        sql_query = 'select %s=(select update_time from details order by id desc limit 1)' #对比当前最大时间戳，相等返回1不相等返回0
        cursor.execute(sql_query,li[0][0])
        if not cursor.fetchone()[0]:
            print(f"{time.asctime()}开始更新最新数据")
            for item in li:
                cursor.execute(sql, item)
            conn.commit()  # 提交事务 update delete insert操作
            print(f"{time.asctime()}更新最新数据完毕")
        else:
            print(f"{time.asctime()}已是最新数据！")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


def insert_history():
    """
        插入历史数据
    :return:
    """
    cursor = None
    conn = None
    try:
        dic = get_tencent_data()[0]  # 0 是历史数据字典,1 最新详细数据列表
        print(f"{time.asctime()}开始插入历史数据")
        conn, cursor = get_conn()
        sql = "insert into history values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for k, v in dic.items():
            # item 格式 {'2020-01-13': {'confirm': 41, 'suspect': 0, 'heal': 0, 'dead': 1}
            cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
                                    v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
                                    v.get("dead"), v.get("dead_add")])

        conn.commit()  # 提交事务 update delete insert操作
        print(f"{time.asctime()}插入历史数据完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


def update_history():
    """
    更新历史数据
    :return:
    """
    cursor = None
    conn = None
    try:
        dic = get_tencent_data()[0]  #  0 是历史数据字典,1 最新详细数据列表
        print(f"{time.asctime()}开始更新历史数据")
        conn, cursor = get_conn()
        sql = "insert into history values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        sql_query = "select confirm from history where ds=%s"
        for k, v in dic.items():
            # item 格式 {'2020-01-13': {'confirm': 41, 'suspect': 0, 'heal': 0, 'dead': 1}
            if not cursor.execute(sql_query, k):
                cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
                                     v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
                                     v.get("dead"), v.get("dead_add")])
        conn.commit()  # 提交事务 update delete insert操作
        print(f"{time.asctime()}历史数据更新完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)

#爬取微博热搜数据
def get_sina_hot():
    url = 'https://s.weibo.com/top/summary?cate=realtimehot'
    res = requests.get(url)
    html = res.text
    r = BeautifulSoup(html)
    s = r.find_all('a', attrs={'target': '_blank'})
    result = []
    for i in range(len(s) - 10):
        pattern = '>(.*)</a>'
        text = re.search(pattern, str(s[i]))
        result.append(text.group(1) + str(50 - i))
    return result

#更新热搜数据
def update_hotsearch():
    cursor = None
    conn = None
    try:
        context = get_sina_hot()
        print(f"{time.asctime()}开始更新热搜数据")
        conn,cursor = get_conn()
        sql = "insert into hotsearch(dt,content) values(%s,%s)"
        ts = time.strftime("%Y-%m-%d %X")
        for i in context:
            cursor.execute(sql,(ts,i))
        conn.commit()
        print(f"{time.asctime()}热搜数据更新完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn,cursor)




if __name__ == "__main__":
    #  insert_history()
    update_history()
    update_details()
    update_hotsearch()