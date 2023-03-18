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
token_got = False
# Generate a self-signed SSL/TLS certificate and private key


# Configure Flask to use SSL/TLS
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem", "key.pem")

rest_client = aiobungie.RESTPool(
    "457a0f8c468a45b3926d70b4b14f601c",
    "EV0u7SOIM6qTK39tw9Y6wU3ffGkf5rkqZEytqRXbe8I",
    43401,
)
client = aiobungie.Client("457a0f8c468a45b3926d70b4b14f601c")


@app.route("/")
def index():
    return flask.render_template(
        "first.html",
        auth_link=flask.url_for("login"),
        prof_link=flask.url_for("profile"),
        access_token=token_got,
    )


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
    token_got = True
    return flask.redirect(flask.url_for("profile"))


# function to client fetch character
async def get_character(
    membership_id, membership_type, character_ids, components, num
) -> aiobungie.crate.CharacterComponent:
    return await client.fetch_character(
        membership_id,
        membership_type,
        character_ids[num],
        components=components,
    )


@app.route("/profile")
async def profile():
    if not (flask.session.get("access_token")):
        print("redirected")
        return flask.redirect("/")
    else:
        async with rest_client.acquire() as rest:
            user = await rest.fetch_current_user_memberships(
                flask.session["access_token"]
            )
        membership_id = user.get("destinyMemberships")[0].get("membershipId")
        membership_type = user.get("destinyMemberships")[0].get("membershipType")

        token = flask.session.get("access_token")
        headers = {
            "X-API-Key": "457a0f8c468a45b3926d70b4b14f601c",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        params = {"components": "Characters"}
        request_url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=Characters"
        response = requests.get(request_url, headers=headers)

        # Get character IDs
        character_ids = []
        for character in response.json()["Response"]["characters"]["data"]:
            character_ids.append(character)
        components = [
            aiobungie.ComponentType.CHARACTERS,
            aiobungie.ComponentType.CURRENCY_LOOKUPS,
            aiobungie.ComponentType.CHARACTER_INVENTORY,
            aiobungie.ComponentType.CHARACTER_EQUIPMENT,
        ]

        character1 = await get_character(
            membership_id, membership_type, character_ids, components, 0
        )
        character2 = await get_character(
            membership_id, membership_type, character_ids, components, 1
        )
        character3 = await get_character(
            membership_id, membership_type, character_ids, components, 2
        )
        print(character1.inventory)
        return flask.render_template(
            "profile.html", username=user.get("bungieNetUser").get("uniqueName")
        )


if __name__ == ("__main__"):
    app.run(debug=True, ssl_context=context)
