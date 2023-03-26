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
                        "manifest", "C:\\Users\\timk2\\EyesUp-1"
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


@app.route("/weapons")
async def weapons():
    if not (flask.session.get("access_token")):
        return flask.redirect("/")
    components = [
        aiobungie.ComponentType.ITEM_PERKS,
        aiobungie.ComponentType.ITEM_INSTANCES,
    ]
    async with rest_client.acquire() as rest:
        primary_ch_1 = await rest.fetch_item(
            membership_id,
            character1["equipment"]["data"]["items"][0]["itemInstanceId"],
            membership_type,
            components=components,
        )
        secondary_ch_1 = await rest.fetch_item(
            membership_id,
            character1["equipment"]["data"]["items"][1]["itemInstanceId"],
            membership_type,
            components=components,
        )
        heavy_ch_1 = await rest.fetch_item(
            membership_id,
            character1["equipment"]["data"]["items"][2]["itemInstanceId"],
            membership_type,
            components=components,
        )
        weapon1_perk_names = []
        weapon1_perk_images = []
        for perk in primary_ch_1["perks"]["data"]["perks"]:
            try:
                weapon1_perk_names.append(
                    manifest["DestinySandboxPerkDefinition"][str(perk["perkHash"])][
                        "displayProperties"
                    ]["name"]
                )
                weapon1_perk_images.append("https://www.bungie.net" + perk["iconPath"])
            except KeyError:
                pass
        weapon2_perk_names = []
        weapon2_perk_images = []
        for perk in secondary_ch_1["perks"]["data"]["perks"]:
            try:
                weapon2_perk_names.append(
                    manifest["DestinySandboxPerkDefinition"][str(perk["perkHash"])][
                        "displayProperties"
                    ]["name"]
                )
                weapon2_perk_images.append("https://www.bungie.net" + perk["iconPath"])
            except KeyError:
                pass
        weapon3_perk_names = []
        weapon3_perk_images = []
        for perk in heavy_ch_1["perks"]["data"]["perks"]:
            try:
                weapon3_perk_names.append(
                    manifest["DestinySandboxPerkDefinition"][str(perk["perkHash"])][
                        "displayProperties"
                    ]["name"]
                )
                weapon3_perk_images.append("https://www.bungie.net" + perk["iconPath"])
            except KeyError:
                pass
    print(primary_ch_1)
    data = {
        "primary_perk_names": weapon1_perk_names,
        "primary_perk_images": weapon1_perk_images,
        "pr_nm_len": len(weapon1_perk_names),
        "pr_im_len": len(weapon1_perk_images),
    }
    return flask.render_template("weapons.html", **data)


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
    global user
    global membership_id
    global membership_type
    global token
    global character_ids
    global character1
    global character2
    global character3
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
            if len(character_ids) > 1:
                character2 = await rest.fetch_character(
                    membership_id,
                    membership_type,
                    character_ids[1],
                    components,
                    flask.session.get("access_token"),
                )
            if len(character_ids) > 2:
                character3 = await rest.fetch_character(
                    membership_id,
                    membership_type,
                    character_ids[2],
                    components,
                    flask.session.get("access_token"),
                )
            items_1 = character1["inventory"]["data"]["items"]
            item_hashes_1 = [item["itemHash"] for item in items_1]
            items_2 = character2["inventory"]["data"]["items"]
            item_hashes_2 = [item["itemHash"] for item in items_2]
            items_3 = character3["inventory"]["data"]["items"]
            item_hashes_3 = [item["itemHash"] for item in items_3]

            # Get a list of equipped items
            equipped_items_ch1 = []
            equipped_items_ch2 = []
            equipped_items_ch3 = []
            for item in character2["equipment"]["data"]["items"]:
                equipped_items_ch2.append(item["itemHash"])
            for item in character1["equipment"]["data"]["items"]:
                equipped_items_ch1.append(item["itemHash"])
            # Convert eqipped item hashes to item names
            equipped_item_names_ch1 = []
            equipped_item_images_ch1 = []
            equipped_item_names_ch2 = []
            equipped_item_images_ch2 = []
            for item in equipped_items_ch1:
                equipped_item_names_ch1.append(
                    manifest["DestinyInventoryItemDefinition"][str(item)][
                        "displayProperties"
                    ]["name"]
                )
                equipped_item_images_ch1.append(
                    "https://www.bungie.net"
                    + manifest["DestinyInventoryItemDefinition"][str(item)][
                        "displayProperties"
                    ]["icon"]
                )
            print(equipped_item_images_ch1)
            print(equipped_item_names_ch1)
            data = {
                "weapons_link": flask.url_for("weapons"),
                "username": user.get("bungieNetUser").get("uniqueName"),
                "membership_id": membership_id,
                "equipped_items_1": equipped_item_names_ch1,
                "equipped_item_images_1": equipped_item_images_ch1,
            }
            return flask.render_template("profile.html", **data)


if __name__ == ("__main__"):
    app.run(debug=True, ssl_context=context)
