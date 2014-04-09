#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
from flask import g, request, render_template, current_app, make_response, session, Blueprint, redirect, abort, jsonify
from flask.ext.wtf import Form, BooleanField, TextField, TextAreaField, SubmitField, SelectField, Required, RecaptchaField, Email, Length
from foofind.utils import nocache
from foofind.services import *
from .files import ReportLinkForm
from foofind.blueprints.downloader import update as downloader_update

external = Blueprint('external', __name__)

def restricted_domain(fnc):
    '''
    External views could be restricted to some domains.
    '''
    @functools.wraps(fnc)
    def wrapped(*args, **kwargs):
        if current_app.config["EXTERNAL_DOMAIN"] in request.url_root:
            return fnc(*args, **kwargs)
        abort(404)
    return wrapped

@csrf.exempt
@external.route('/external/contact', methods=['GET', 'POST'], defaults={'lang': "en"})
@nocache
@restricted_domain
def contact():
    '''
    Muestra el formulario de contacto
    '''
    try:
        g.accept_cookies=None
        form = ExternalContactForm(request.form)
        sent = (request.method=='POST' and form.validate() and send_mail("Contact Form",current_app.config["CONTACT_EMAIL"], "pages",form=form))
        return render_template(
            'contact.html',
            form=form, sent=sent
        )
    except:
        return "Service unavailable temporarily."

@csrf.exempt
@external.route('/external/complaint', methods=['GET', 'POST'], defaults={'lang': "en"})
@nocache
@restricted_domain
def complaint():
    '''
    Procesa los datos del formulario para reportar enlaces.
    '''
    sent = False
    g.accept_cookies=None
    form = ExternalReportLinkForm(request.form)
    try:
        if request.method=='POST' and form.validate():
            try:
                urlreported = "/download/"+form.file_id.data+"/"
                pagesdb.create_complaint(dict([("linkreported","-"), ("urlreported",urlreported), ("ip",request.remote_addr)]+[(field.name,field.data) for field in form]))
                sent = True
            except BaseException as e:
                logging.error("Error on file complaint.")

        return render_template('complaint.html', form=form, sent=sent)
    except:
        return "Service unavailable temporarily."

@csrf.exempt
@external.route('/external/cookie', defaults={'lang': "en"})
@nocache
@restricted_domain
def cookie():
    try:
        g.accept_cookies=None
        ip = (request.headers.getlist("X-Forwarded-For") or [request.remote_addr])[0]
        cookieLawApplies = any(lang_code in request.accept_languages.values() for lang_code in current_app.config["SPANISH_LANG_CODES"]) or ip in spanish_ips
    except:
        cookieLawApplies = True

    response = make_response("cookieLawApplies(%s)"%str(cookieLawApplies).lower())
    response.headers['content-type']='application/javascript'
    return response

@csrf.exempt
@external.route('/<lang>/update')
@nocache
@restricted_domain
def update():
    return jsonify({})
    #return downloader_update()

@csrf.exempt
@external.route("/<lang>/downloader/<build>/<instfile>")
@nocache
@restricted_domain
def download(instfile, build):
    return send_instfile(instfile, build)

class ExternalContactForm(Form):
    '''
    Formulario de contacto
    '''
    name = TextField("Your name:", [Required()])
    email = TextField("Your email:", [Required(), Email("Your email is not valid.")])
    company = TextField("Your company:")
    website = TextField("Website:")
    phone = TextField("Your phone number:")
    inquiry = SelectField("Your inquiry type:", default="Support", choices=[("Support","Support"),("Bug Reports","Bug Reports"),("Business Development","Business Development"),("Press","Press"),])
    message = TextAreaField("Your message:", [Required()])
    captcha = RecaptchaField("Please, insert the confirmation code given below on the right input box.")
    submit = SubmitField("Send")

class ExternalReportLinkForm(ReportLinkForm):
    captcha = RecaptchaField("Please, insert the confirmation code given below on the right input box.")
    submit = SubmitField()
