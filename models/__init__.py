#coding=utf-8

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from settings import *
import redis

Model=declarative_base()
engine = create_engine(MYSQL_DB)
db_session = scoped_session(sessionmaker(bind=engine))
Model.query = db_session.query_property()
redispool= redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT)
rserver=redis.Redis(connection_pool=redispool)


class CRUD():
    def save(self):
        if self.id == None:
            db_session.add(self)
        return db_session.commit()

    def destroy(self):
        db_session.delete(self)
        return db_session.commit()
    def set_attrs(self, attrs):
        for key, value in attrs.items():
            if hasattr(self, key):
                setattr(self, key, value)