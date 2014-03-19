
from flask import g, request, render_template, current_app, make_response, session, Blueprint
from flask.ext.wtf import Form, TextField, TextAreaField, SelectField, SubmitField, RecaptchaField
from flask.ext.wtf import Required, Email
from foofind.utils import nocache
from foofind.services import *

external = Blueprint('external', __name__)

@csrf.exempt
@external.route('/external/contact', methods=['GET', 'POST'], defaults={'lang': "en"})
@nocache
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
@external.route('/external/cookie', defaults={'lang': "en"})
@nocache
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

class ExternalContactForm(Form):
    '''
    Formulario de contacto
    '''
    name = TextField("Your Name:", [Required()])
    email = TextField("Your E-mail:", [Required(), Email("Your email is not valid.")])
    company = TextField("Company:")
    website = TextField("Website:")
    phone = TextField("Phone Number:")
    inquiry = SelectField("Your inquiry type:", default="Support", choices=[("Support","Support"),("Bug Reports","Bug Reports"),("Business Development","Business Development"),("Press","Press"),])
    message = TextAreaField("Your message:", [Required()])
    captcha = RecaptchaField("Please, insert the confirmation code given below on the right input box.")
    submit = SubmitField("Send")
