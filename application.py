#!/usr/bin/env python
#coding: utf-8
from copy import deepcopy
from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import jsonify
from pymongo import Connection
from pymongo.objectid import ObjectId
import re

application = Flask(__name__)

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
DBS_NAME = 'sampledb'
COLLECTION_NAME = 'documentss'

FIELDS=[
    {'name' : 'name',   'label' : u'Name'}, 
    {'name' : 'abbrev', 'label' : u'Abbreviation'}, 
    {'name' : 'attr1',  'label' : u'Attribite1'}, 
    {'name' : 'attr2',  'label' : u'Attribite2'}, 
    {'name' : 'memo',   'label' : u'Memo',        'input_type':'textarea'}, 
]

@application.route("/")
def index():
    connection = Connection(MONGODB_HOST, MONGODB_PORT)
    collection = connection[DBS_NAME][COLLECTION_NAME]
    _id = request.args.get('_id','')
    selected=None
    try:
        selected = collection.find({'_id':ObjectId(_id)}).next()
    except:
        pass
    items = collection.find({'visible':'True'}).sort('name')
    connection.disconnect()
    fields=deepcopy(FIELDS)
    editform=False
    if selected is not None:
        editform=True
        for field in fields:
            try:
                fieldname = field['name']
                field['default_value']=selected[fieldname]
            except:
                field['default_value']=''
    return render_template("index.html",
                        items=items,
                        selected=selected,
                        fields=fields,
                        editform=editform,
                        )

@application.route("/regist", methods = ['POST'])
def regist():
    # TODO: validation
    # TODO: normalization(ex. multibyte -> singlebyte)
    connection = Connection(MONGODB_HOST, MONGODB_PORT)
    collection = connection[DBS_NAME][COLLECTION_NAME]
    data=request.form.copy()
    data.update({'visible':'True'})
    del data['_id']
    _id = request.form['_id']
    if _id is not None and _id != '':
        data.update({'_id':ObjectId(_id)})
    collection.save(data)
    connection.disconnect()
    return redirect('/#%s'%(_id))

@application.route("/delete", methods = ['POST'])
def delete():
    connection = Connection(MONGODB_HOST, MONGODB_PORT)
    collection = connection[DBS_NAME][COLLECTION_NAME]
    data=request.form.copy()
    data.update({'visible':'False'})
    del data['_id']
    _id = request.form['_id']
    if _id is not None and _id != '':
        data.update({'_id':ObjectId(_id)})
        collection.save(data)
    connection.disconnect()
    return redirect('/')

@application.route("/api")
@application.route("/api/")
def api_index():
    return render_template("api_index.html")

@application.route("/api/search")
def api_search():
    connection = Connection(MONGODB_HOST, MONGODB_PORT)
    collection = connection[DBS_NAME][COLLECTION_NAME]
    search_condition=dict()
    for field in deepcopy(FIELDS):
        value=request.args.get(field['name'],'')
        if value != '':
            regex=re.compile(r'.*%s.*'%(value),re.IGNORECASE)
            search_condition[field['name']]=regex
    visible = request.args.get('visible','')
    if visible == '':
        search_condition.update({'visible':'True'})
    else:
        search_condition.update({'visible':visible})
    items = collection.find(search_condition)
    jsondata=list()
    jsondata = items
    connection.disconnect()
    return render_template("multijson.html",jsondata=jsondata)

@application.route("/api/fields")
def apifields():
    jsondata=list()
    for item in deepcopy(FIELDS):
        if item['name'] == "":
            continue
        jsondata.append(item['name'])
    return render_template("singlejson.html",jsondata=jsondata)

@application.route("/api/values")
def api_values():
    connection = Connection(MONGODB_HOST, MONGODB_PORT)
    collection = connection[DBS_NAME][COLLECTION_NAME]
    field = request.args.get('field','')
    items = collection.find({'visible':'True'}).sort(field).distinct(field)
    jsondata=list()
    for item in items:
        if item == '':
            continue
        jsondata.append(item)
    connection.disconnect()
    return render_template("singlejson.html",jsondata=jsondata)

if __name__ == "__main__":
    application.run(host='0.0.0.0',port=5000,debug=True)

