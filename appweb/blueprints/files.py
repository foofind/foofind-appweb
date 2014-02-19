# -*- coding: utf-8 -*-

"""
Controladores de las páginas de búsqueda y de fichero.
"""

import json
from flask import request, render_template, g, current_app, redirect, url_for, jsonify, make_response
from flask.ext.wtf import Form, BooleanField, TextField, TextAreaField, SubmitField, Required, Email, Length
from flask.ext.login import current_user

from base64 import b64decode
from struct import unpack

from foofind.blueprints.files import search_files
from foofind.blueprints.files.helpers import *

from foofind.services import *
from foofind.utils import logging, hex2url, url2mid
from foofind.utils.content_types import *
from foofind.utils.fooprint import Fooprint

files = Fooprint('files', __name__)

def weight_processor(w, ct, r, nr):
    return w if w else -10

def tree_visitor(item):
    if item[0]=="_w" or item[0]=="_u":
        return None
    else:
        return item[1]["_w"]

@files.route('/<lang>', methods=["POST"])
@csrf.exempt
def home():
    '''
    Renderiza la portada de la pestaña find de la aplicación.
    '''
    return render_template('index.html')

@files.route('/<lang>/search', methods=["POST"])
def search():
    '''
    Gestiona las URL de busqueda de archivos para la aplicacion.
    '''
    query=request.form.get("q",None)
    g.filetype=filetype=request.form.get("t",None)

    if query: #si no se ha buscado nada se manda al inicio
        query = query.replace("_"," ")  #para que funcionen la busqueda cuando vienen varias palabras

    filters = {"src":"torrent"}

    ori_query = query

    _in = [i for i, v in enumerate(g.categories) if v[0] == filetype]
    if filetype and _in :
        _id = _in[0]
        if "t" in g.categories[_id][1]:
            filters["type"] = g.categories[_id][1]['t']
        if "q" in g.categories[_id][1]:
            _type = g.categories[_id][1]['q']
            query = "%s (%s)" % (query, _type)

    args = filters.copy()
    args["q"] = ori_query
    if ori_query != query:
        args['type'] = _type
    g.args=args

    sure = False
    total_found=0

    if query:
        search_results = search_files(query, filters, min_results=50, last_items=[], non_group=True, order=("@weight*r", "e DESC, ok DESC, r DESC, fs DESC", "@weight*r"), weight_processor=weight_processor, tree_visitor=tree_visitor)
    else:
        search_results = {"last_items":[], "files":[], "result_number":""}

    return render_template('search.html',
        query=ori_query, filetype=filetype, last_items=search_results["last_items"],
        files=[torrents_data(afile) for afile in search_results["files"]],
        result_number=search_results["result_number"].replace(query, ori_query)
    )

@files.route('/<lang>/searcha',methods=['POST'])
@csrf.exempt
def searcha():
    '''
    Responde las peticiones de busqueda por ajax
    '''

    query=request.form.get("query",None)
    g.filetype=filetype=request.form.get("filetype",None)

    if not query: #si no se ha buscado nada se manda al inicio
        logging.error("Invalid data for AJAX search request.")
        return jsonify({})

    query = query.replace("_"," ") if query is not None else None #para que funcionen la busqueda cuando vienen varias palabras
    filters = {"src":"torrent"}
    ori_query = query

    _in = [i for i, v in enumerate(g.categories) if v[0] == filetype]
    if filetype and _in:
        _id = _in[0]
        if "t" in g.categories[_id][1]:
            filters["type"] = g.categories[_id][1]['t']
        if "q" in g.categories[_id][1]:
            _type = g.categories[_id][1]['q']
            query = "%s (%s)" % (query, _type)

    args = filters.copy()
    args["q"] = ori_query
    if ori_query != query:
        args['type'] = _type
    g.args=args

    last_items = []
    try:
        last_items = b64decode(str(request.form["last_items"]) if "last_items" in request.form else "", "-_")
        if last_items:
            last_items = unpack("%dh"%(len(last_items)/2), last_items)
    except BaseException as e:
        logging.error("Error parsing last_items information from request.")

    sure = False
    total_found=0

    search_results = search_files(query, filters, min_results=0, last_items=last_items, non_group=True, order=("@weight*r", "e DESC, ok DESC, r DESC, fs DESC", "@weight*r"), weight_processor=weight_processor, tree_visitor=tree_visitor)

    response = make_response(render_template('file.html',files=[torrents_data(afile) for afile in search_results["files"]]))
    del search_results["files"]

    response.headers["X-JSON"]=json.dumps(search_results)
    return response

def torrents_data(data):
    valid_torrent = False

    if not data or not "sources" in data["view"]:
        return None, None

    data['view']["torrent_sources"] = {"magnet":None, "sources_list":[]}
    for source, item in data["view"]["sources"].iteritems():
        if source == "tmagnet":
            data['view']["torrent_sources"]["magnet"] = item["urls"][0]
            valid_torrent = True
        elif item["icon"]=="torrent":
            valid_torrent = True
            data['view']["torrent_sources"]["sources_list"].extend(item["urls"])

    # no tiene origenes validos
    if not valid_torrent:
        return None, None

    desc = None
    # organiza mejor la descripcion del fichero
    if "description" in data["view"]["md"]:

        # recupera la descripcion original
        desc = data["view"]["md"]["description"]
        del data["view"]["md"]["description"]

        # inicializa variables
        long_desc = False
        short_desc = None
        acum = []

        # recorre las lineas de la descripcion
        for line in desc.split("\n"):
            # si llega a pasar despues acumular algo, hay que mostrar la desc larga
            if acum:
                long_desc = True

            # ignora lineas con muchos caracteres repetidos
            prev_char = repeat_count = 0
            for char in line:
                if prev_char==char:
                    repeat_count+=1
                else:
                    repeat_count = 0
                if repeat_count>5:
                    line=""
                    break
                prev_char = char

            # si la linea es "corta", la toma como fin de parrafo
            if len(line)<50:
                if acum:
                    if line: acum.append(line)

                    # si el parrafo es mas largo que 110, lo usa
                    paraph = " ".join(acum)
                    acum = [] # antes de seguir reinicia el acum
                    paraph_len = len(paraph)
                    if paraph_len>90:
                        short_desc = paraph
                        if paraph_len>140: # si no es suficientemente larga sigue buscando
                            break
                    continue
            else: # si no, acumula
                acum.append(line)

        # procesa el parrafo final
        if acum:
            paraph = " ".join(acum)
            paraph_len = len(paraph)
            if paraph_len>90:
                short_desc = paraph

        # si hay descripcion corta se muestra y se decide si se debe mostrar la larga tambien
        if short_desc:
            data["view"]["md"]["short_desc"] = short_desc
            long_desc = long_desc or len(short_desc)>400
        else:
            long_desc = True

        if not long_desc and "nfo" in data["file"]["md"]:
            desc = data["file"]["md"]["nfo"]

        data["view"]["md"]["description"] = desc

    # preview
    if "torrent:thumbnail" in data["file"]["md"]:
        data["view"]["thumbnail"] = data["file"]["md"]["torrent:thumbnail"]

    # salud del torrent
    try:
        seeds = int(float(data['view']['md']['seeds'])) if 'seeds' in data['view']['md'] else 0
    except:
        seeds = 0
    try:
        leechs = int(float(data['view']['md']['leechs'])) if 'leechs' in data['view']['md'] else 0
    except:
        leechs = 0

    base_rating = int(2/(leechs+1.)) if seeds==0 else min(10,int(seeds/(leechs+1.)*5))
    data['view']['health'] = int(base_rating/2.5)
    data['view']['rating'] = base_rating/2
    data['view']['seeds'] = seeds
    data['view']['leechs'] = leechs

    return data

@files.route('/<lang>/complaint', methods=['POST'])
def complaint():
    '''
    Procesa los datos del formulario para reportar enlaces.
    '''
    try:
        form = ReportLinkForm(request.form)
        if form.validate():
            urlreported = "/download/"+form.file_id.data+"/"
            pagesdb.create_complaint(dict([("linkreported","-"),("urlreported",urlreported),("ip",request.remote_addr)]+[(field.name,field.data) for field in form]))
            response = make_response("true")
        else:
            response = make_response(repr(form.errors.keys()))
    except BaseException as e:
        logging.error("Error on file complaint.")
        response = make_response("false")

    response.mimetype = "application/json"
    return response

@files.route('/<lang>/vote',methods=['POST'])
def vote():
    '''
    Gestiona las votaciones de archivos
    '''
    ok = False
    try:
        file_id=url2mid(request.form.get("file_id",None))
        server=int(request.form.get("server",0))
        vote=int(request.form.get("vote",0))
        if server>1 and file_id and vote in (0,1):
            file_info = usersdb.set_file_vote(file_id, current_user, g.lang, vote)
            filesdb.update_file({"_id":file_id, "vs":file_info, "s":server}, direct_connection=True)
            ok = True
    except BaseException as e:
        logging.error("Error on vote.")

    response = make_response("true" if ok else "false")
    response.mimetype = "application/json"
    return response

class ReportLinkForm(Form):
    '''
    Formulario para reportar enlaces
    '''
    file_id = TextField(validators=[Required(), Length(16,16)])
    name = TextField(validators=[Required()])
    surname = TextField(validators=[Required()])
    company = TextField()
    email = TextField(validators=[Required(),Email()])
    phonenumber = TextField()
    reason = TextField(validators=[Required()])
    message = TextAreaField(validators=[Required()])
    accept_tos = BooleanField(validators=[Required()])
    submit = SubmitField()
