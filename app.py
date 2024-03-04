import base64
from flask import Flask, make_response, render_template, g, request, session
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Email, Regexp
from werkzeug.utils import secure_filename

import os, logging

# import requests
from datetime import datetime

# app starts here
app = Flask(__name__)
# loads configuration from config.py
app.config.from_object("config.Config")
# set up flask logging
# TO-do: setup logging, https://flask.palletsprojects.com/en/2.3.x/logging/
# log to file for audit trail
log = app.logger
logging.basicConfig(filename="app.log", level=logging.INFO)
# log rotation

# setup security headers
@app.before_request
def prepare_request():
    g.nonce = base64.b64encode(os.urandom(32)).decode("utf-8")


@app.after_request
def secure_flask(response):
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; img-src 'self' data: https://www.gemadept.com.vn/img/nav/logo.png; script-src 'self' 'nonce-{g.nonce}' https://www.gstatic.com/recaptcha/releases/yiNW3R9jkyLVP5-EEZLDzUtA/recaptcha__en.js https://www.google.com/recaptcha/api.js https://cdnjs.cloudflare.com/ajax/libs/flowbite/2.2.1/flowbite.min.js https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/min/dropzone.min.js https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js https://cdnjs.cloudflare.com/ajax/libs/uuid/8.3.2/uuidv4.min.js; style-src 'self' http://localhost:5000/thianhdep/static/css/global.css http://localhost:5000/thianhdep/static/css/theme.css https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/dropzone.min.css https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css; frame-src 'self' https://www.google.com;"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.set_cookie("username", "flask", secure=True, httponly=True, samesite="Lax")
    # cookie expires after 10 minutes
    response.set_cookie("snakes", "3", max_age=600)
    return response

@app.route("/", methods=["GET"])
def show_upload_form():
    class EntryForm(FlaskForm):
        ma_nhan_vien = StringField("Mã nhân viên", validators=[DataRequired()])
        ho_ten = StringField("Họ tên", validators=[DataRequired()])
        email = StringField("Email", validators=[DataRequired(), Email()])
        phone = StringField(
            "Số điện thoại", validators=[DataRequired(), Regexp(r"^0\d{6,10}$")]
        )
        phong_ban = StringField("Phòng ban", validators=[DataRequired()])
        don_vi = SelectField(
            "Đơn vị",
            choices=[
                ("GMDHO", "Gemadept HO"),
                ("GML", "Gemalink"),
                ("PIP", "Phước Long ICD"),
                ("BDP", "Bình Dương"),
                ("DQP", "Dung Quốc"),
                ("NDV", "Nam Đình Vũ"),
                ("NHI", "Nam Hải ICD"),
                ("H", "Holdings"),
                ("K", "Khác"),
            ],
            validators=[DataRequired()],
        )
        recaptcha = RecaptchaField()

    return render_template("upload.html", form=EntryForm(), nonce=g.nonce)


@app.route("/recaptcha", methods=["GET"])
def return_recaptchakey():
    # Check if the request is coming from localhost
    if (
        request.remote_addr != "127.0.0.1"
    ):  # noted that if you're using a reverse proxy, the remote_addr will be the proxy server's IP; best practice would be configure nginx to check if a request is coming from localhost
        # log
        log.error(f"Unauthorized request to /recaptcha from {request.remote_addr}")
        return "Unauthorized", 401
    return make_response((app.config["RECAPTCHA_PRIVATE_KEY"], 200))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
