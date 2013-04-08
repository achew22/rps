#! /usr/bin/env python
# BRING IN THE FUTURE
from __future__ import division

import os
import psycopg2
import urlparse
import pprint

from collections import defaultdict
from flask import Flask, Response, render_template, \
                  make_response, send_file, request

# Constants
MARKOV_LENGTH = 5
BASE_URL = "http://rps.labs.andrewzallen.com"

# SQL queries
INIT = """
CREATE TABLE IF NOT EXISTS throws (
    id TEXT NOT NULL,
    count INT,
    PRIMARY KEY(id)
);

DROP FUNCTION IF EXISTS new_throw(TEXT);
CREATE FUNCTION new_throw(key TEXT) RETURNS VOID AS
$$
BEGIN
    LOOP
        -- first try to update the key
        UPDATE throws SET count = count + 1 WHERE id = key;
        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO throws(id,count) VALUES (key, 1);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- Do nothing, and loop to try the UPDATE again.
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql;
"""

NEW_ENTRY = """
SELECT new_throw(%(key)s);
"""

GET_THROWS = """
SELECT id, count FROM throws;
"""

# Ready... go
app = Flask(__name__)

urlparse.uses_netloc.append('postgres')
url = urlparse.urlparse(os.environ['DATABASE_URL'])

conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s " % (url.path[1:], url.username, url.password, url.hostname))
cursor = conn.cursor()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/rps.js')
def application():
    cursor.execute(GET_THROWS)
    results = cursor.fetchall()

    # Step 1: Map everything into subchains of length n
    def mapper(t):
        key = t[0]
        val = t[1]
        r = {}

        # Do the build up to MARKOV_LENGTH
        #There is some worry that this will double count unfairly
        # Omit for now
        #for i in range(1,MARKOV_LENGTH):
        #    r[key[0:i]] = val

        # Handle the subchains that are smaller than MARKOV_LENGTH
        for i in range(len(t[0]) - MARKOV_LENGTH):
            r[key[i:i+MARKOV_LENGTH]] = val
        else: # And if it is too small, just emit it
            r[key] = val

        return r

    def reducer(acc, e):
        for key, value in e.items():
            acc[key] += value

        return acc

    tree = reduce(reducer, map(mapper, results), defaultdict(int))

    # Chain is now a dict that has a count for every time someone
    # has played a move. Use this information to construct the
    # optimal play strategy. In theory bumping MARKOV_LENGTH up
    # will make it more accurate.
    chain = []

    # Recurse through the tree to construct our optimal play strategy
    # This has BAD complexity bounds. It is O(n^3) where n = MARKOV_LENGTH.
    # This is bad for "real time" generation of the tree. More advanced
    # solutions can likely be produced but for 5^3 (125) it isn't worth it.
    def construct_markov():
        def compute_probabilties(path):
            nodes = [tree[path + '0'], tree[path + '1'], tree[path + '2']]
            count = sum(nodes)

            # If there is nothing at this path, return sentinal (-1)
            if count == 0:
                return [-1]

            return [map(lambda n: n / count, nodes)]


        # Breadth first search of tree space
        q = ['']
        output = []
        while len(q):
            p = q[0]

            # Strip the first element from the queue and append
            # entries for this batch
            q = q[1:]

            # We are bigger than we need now
            if len(p) < MARKOV_LENGTH:
                q += [p + '0', p + '1', p + '2']

            #print q
            o = compute_probabilties(p)
            #print p, o
            output += o

        return output

    body = render_template(
        'rps.js',
        baseurl=BASE_URL,
        chain=construct_markov()
    )
    response = make_response(body, 200)
    response.headers['Content-Type'] = "application/javascript"
    return response

@app.route('/feedback.gif')
def feedback(h = ""):
    cursor.execute(NEW_ENTRY, {"key":request.args.get('h','')})
    res = cursor.fetchall() # It won't run it till you try to get data
    #print res
    return send_file('static/blank.gif')

@app.errorhandler(404)
def not_found(f):
    return "Not found: %s" % (f)

@app.errorhandler(500)
def server_error(e):
    return "Server error: %s" % (e)

if __name__ == '__main__':
    # Kind of run the migrations
    #cursor.execute(INIT)

    debug = True
    BASE_URL = "http://localhost:5000"
    app.run(use_debugger=debug, debug=debug,
            use_reloader=debug, host='0.0.0.0')