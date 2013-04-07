#! /usr/bin/env python

import os
from flask import Flask, Response, render_template, make_response

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/rps.js')
def application():
    body = render_template('rps.js', chain="[0,1,2,3,1,2,3,1,2,3,1,2,3]")
    response = make_response(body, 200)
    response.headers['Content-Type'] = "application/javascript"
    return response

@app.errorhandler(404)
def not_found(f):
    return "Not found: %s" % (f)

@app.errorhandler(500)
def server_error(e):
    return "Server error: %s" % (e)

if __name__ == '__main__':
    debug = True
    app.run(use_debugger=debug, debug=debug,
            use_reloader=debug, host='0.0.0.0')
