#!/usr/bin/pyhton3
# coding=utf-8

from flask import Flask, Response
from flask import render_template
from flask import request
from pymongo import MongoClient
import json
from meituan_spider import run

app = Flask(__name__)
client = MongoClient(host='mongo')
db = client.meituan
db_meishi = db.meishi
page_size = 10


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/spider')
def spider():
    run()
    return Response(json.dumps('{"code":"OK}').encode('utf-8'), mimetype='application/json; charset=utf-8')


@app.route('/meishi')
def meishi():
    page = int(request.args.get('page', 1))
    skip = (page - 1) * 10
    db_data = db_meishi.find().skip(skip).limit(page_size)
    data = [{
        'title': v.get('title'),
        'address': v.get('address'),
        'phone': v.get('phone'),
        'openTime': v.get('openTime')} for v in db_data]
    total = db_meishi.count()
    resp = {
        'total': total,
        'page': page,
        'size': page_size,
        'data': data
    }
    return Response(json.dumps(resp).encode('utf-8'), mimetype='application/json; charset=utf-8')


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
