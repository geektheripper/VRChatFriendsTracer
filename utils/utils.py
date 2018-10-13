#coding=utf-8
from requests import RequestException
import logging
import sys
import os
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %I:%M:%S',level=logging.INFO,stream=sys.stdout)
import pickle

def println(obj):
    if isinstance(obj, list):
        for i in obj:
           println(i)
    elif isinstance(obj, dict):
           for k,v in obj.items():
               println("%-50s:%-50s"%(k,v))
    else:
        print(obj)


def resp2json(func):
        def wrapper(*args, retry=3, **kwargs):
            try:
                resp = func(*args, **kwargs)
            except RequestException  as e:
                logging.info(e)
                while (retry > 0):
                    logging.warning("Retry times remain %d" % retry)
                    retry -= 1
                    return wrapper(*args, retry=retry, **kwargs)
            else:
                if resp.status_code == 200:
                    #logging.info(resp.text)
                    pass
                elif resp.status_code == 401:
                    logging.error("HTTP ERROR 401", resp.text)
                    if os.path.exists('session.pkl'):
                        os.remove("session.pkl")
                else:
                    logging.info("CODE", resp.status_code, resp.status_code)
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