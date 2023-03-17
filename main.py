import flask
import os
import aiobungie
import requests
import oauthlib.oauth2
import requests_oauthlib
import json

app = flask.Flask(__name__)
app.secret_key = os.urandom(24)

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
    return flask.redirect(oauth_url)


@app.route("/callback")
async def callback():
    code = flask.request.args.get("code")
    async with rest_client.acquire() as rest:
        token = await rest.exchange_code(code)
    flask.session["access_token"] = token["access_token"]
    return flask.redirect(flask.url_for("profile"))


@app.route("/profile")
async def profile():
    async with rest_client.acquire() as rest:
        user = await rest.get_user()
    return flask.render_template("profile.html", user=user)


if __name__ == ("__main__"):
    app.run(debug=True)
