#!/usr/bin/pyhton3
# coding=utf-8

from flask import Flask, Response
from flask import render_template
from flask import request
from pymongo import MongoClient
from bson.json_util import dumps

app = Flask(__name__)
client = MongoClient()
db = client.meituan
db_meishi = db.meishi
page_size = 10


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/meishi')
def meishi():
    page = int(request.args.get('page', 1))
    skip = (page - 1) * 10
    data = db_meishi.find().skip(skip).limit(page_size)
    total = db_meishi.count()
    resp = {
        'total': total,
        'page': page,
        'size': page_size,
        'data': data
    }
    return Response(dumps(resp).encode('utf-8'), mimetype='application/json; charset=utf-8')

if __name__ == '__main__':
    app.debug = True
    app.run(port=8888)
