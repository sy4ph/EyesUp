import flask
import os
import aiobungie
import requests
import oauthlib.oauth2
import requests_oauthlib
import json
import ssl

app = flask.Flask(__name__)
app.secret_key = os.urandom(24)

# Generate a self-signed SSL/TLS certificate and private key
openssl_cmd = 'openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"'
os.system(openssl_cmd)

# Configure Flask to use SSL/TLS
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem", "key.pem")

rest_client = aiobungie.RESTPool(
    "457a0f8c468a45b3926d70b4b14f601c",
    "EV0u7SOIM6qTK39tw9Y6wU3ffGkf5rkqZEytqRXbe8I",
    43401,
)


@app.route("/")
def index():
    if not (flask.session.get("access_token")):
        return flask.redirect(flask.url_for("login"))
    else:
        return flask.redirect(flask.url_for("profile"))


@app.route("/login")
async def login():
    async with rest_client.acquire() as rest:
        oauth_url = rest.build_oauth2_url()
        print(flask.url_for("callback", _external=True))
    return flask.redirect(oauth_url)


@app.route("/callback")
async def callback():
    code = flask.request.args.get("code")
    async with rest_client.acquire() as rest:
        token = await rest.fetch_oauth2_tokens(code)
    flask.session["access_token"] = token.access_token
    flask.session["membership_id"] = token.membership_id
    return flask.redirect(flask.url_for("profile"))


@app.route("/profile")
async def profile():
    async with rest_client.acquire() as rest:
        user = await
    return flask.render_template("profile.html", user=user)


if __name__ == ("__main__"):
    app.run(debug=True, ssl_context=context)
