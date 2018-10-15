#coding=utf-8
import logging
import sys
import os
import pickle
from models.mysql_model import  StatusText

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %I:%M:%S',level=logging.INFO,stream=sys.stdout)

def resp2json(func):
        def wrapper(*args, retry=3, **kwargs):
            try:
                resp = func(*args, **kwargs)
            except Exception  as e:
                logging.exception(e)
                while (retry > 0):
                    logging.info("Retry times remain %d" % retry)
                    retry -= 1
                    return wrapper(*args, retry=retry, **kwargs)
            else:
                if resp.status_code == 200:
                    pass
                elif resp.status_code == 401:
                    logging.error("HTTP %s %s"%(resp.status_code,resp.text))
                    raise Exception("Unauthorized")
                else:
                    logging.warning("HTTP %s %s"%(resp.status_code,resp.text))
                return resp.json()
        return wrapper

def dump_session(session):
    with open('session.pkl', 'wb') as file:
        pickle.dump(session, file)
        logging.info("Dump session to file")


def load_session():
    if os.path.exists('session.pkl'):
        with open('session.pkl', 'rb') as file:
            session = pickle.load(file)
            logging.info("Load session from session.pkl")
        return session



