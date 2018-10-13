#coding=utf-8

from sqlalchemy import Column,Integer,String,DATETIME
from models import Model,CRUD
import datetime


class Log(Model,CRUD):
    def __init__(self,usr_id,name,text,target):
        self.usr_id=usr_id
        self.displayName=name,
        self.text=text
        self.target=target

    __tablename__='log'
    __table_args__ = {
        "mysql_charset" : "utf8mb4"}

    id=Column(Integer,primary_key=True,autoincrement=True)
    usr_id=Column(String(100))
    displayName=Column(String(100))
    text=Column(String(255))
    target=Column(String(255))

    time=Column(DATETIME,default=datetime.datetime.now)




if __name__ == '__main__':
    #create table
    from models import engine
    Model.metadata.create_all(bind=engine)

