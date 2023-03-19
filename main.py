import flask
import os
import aiobungie
import requests
import oauthlib.oauth2
import requests_oauthlib
import json
import ssl
import asyncio

app = flask.Flask(__name__)
app.secret_key = os.urandom(24)
token_got = False
# Generate a self-signed SSL/TLS certificate and private key
async def manifest_check():
    async with rest_client.acquire() as rest:
        global manifest
        with open("manifest_version.txt", "r+") as file:
            actual_version = await rest.fetch_manifest_version()
            local_version = file.read()
            if (
                os.path.isfile(os.path.join("C://Users/timk2/EyesUp", "manifest.json"))
                and actual_version == local_version
            ):
                print("You fine.")
            else:
                file.close()
                with open("manifest_version.txt", "w") as file:
                    print("you not fine")
                    download_status = "We are downloading shit! Wait a minute."
                    await rest.download_json_manifest(
                        "manifest", "C:\\Users\\timk2\\EyesUp"
                    )
                    # write the manifest version to the file
                    file.write(str(await rest.fetch_manifest_version()))
        with open("manifest.json", "r") as f:
            manifest = json.load(f)


# Configure Flask to use SSL/TLS
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem", "key.pem")

rest_client = aiobungie.RESTPool(
    "457a0f8c468a45b3926d70b4b14f601c",
    "EV0u7SOIM6qTK39tw9Y6wU3ffGkf5rkqZEytqRXbe8I",
    43401,
)
client = aiobungie.Client("457a0f8c468a45b3926d70b4b14f601c")
download_status = ""

asyncio.run(manifest_check())


@app.route("/")
def index():
    return flask.render_template(
        "first.html",
        auth_link=flask.url_for("login"),
        prof_link=flask.url_for("profile"),
        download_status=download_status,
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
            character1 = await rest.fetch_character(
                membership_id,
                membership_type,
                character_ids[0],
                components,
                flask.session.get("access_token"),
            )
            items = character1["inventory"]["data"]["items"]
            item_hashes = [item["itemHash"] for item in items]

            for item in item_hashes:
                print(
                    manifest["DestinyInventoryItemDefinition"][str(item)][
                        "displayProperties"
                    ]["name"]
                )
            # Get a list of equipped items
            equipped_items = []
            for item in character1["equipment"]["data"]["items"]:
                equipped_items.append(item["itemHash"])
            # Convert eqipped item hashes to item names
            equipped_item_names = []
            equipped_item_images = []
            for item in equipped_items:
                equipped_item_names.append(
                    manifest["DestinyInventoryItemDefinition"][str(item)][
                        "displayProperties"
                    ]["name"]
                )
                equipped_item_images.append(
                    "https://www.bungie.net"
                    + manifest["DestinyInventoryItemDefinition"][str(item)][
                        "displayProperties"
                    ]["icon"]
                )
            print(equipped_item_images)
            print(equipped_item_names)
            data = {
                "username": user.get("bungieNetUser").get("uniqueName"),
                "membership_id": membership_id,
                "equipped_items": equipped_item_names,
                "equipped_item_images": equipped_item_images,
            }
            return flask.render_template("profile.html", **data)


if __name__ == ("__main__"):
    app.run(debug=True, ssl_context=context)
