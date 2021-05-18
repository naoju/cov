import pandas as pd
import openpyxl
import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="zx1999818",
    db="cov",
    charset="utf8"
)
mysql_page1 = pd.read_sql("select * from hotsearch",con=conn)
mysql_page2 = pd.read_sql("select * from details",con=conn)
mysql_page3 = pd.read_sql("select * from history",con=conn)
#print(mysql_page)
df1=mysql_page1.iloc[:,:]
df1.to_excel('hotsearch.xlsx',index=False)

df2=mysql_page2.iloc[:,:]
df2.to_excel('details.xlsx',index=False)

df3=mysql_page3.iloc[:,:]
df3.to_excel('history.xlsx',index=False)