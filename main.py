from flask import Flask, redirect, render_template, request, send_from_directory, make_response
import os, pymongo, string, random, hashlib

app = Flask("FasmGA-255", template_folder = os.path.abspath("pages"))

database = pymongo.MongoClient(os.getenv("MongoString"))
db = database["fasmga"]
users = db["users"]

def getLang():
    if request.cookies.get("lang"):
        import json
        with open(app.root_path + "/translations/" + request.cookies.get("lang") + ".json", "r") as file:
            translation = json.load(file)
            return translation
    else:
        import json
        with open(app.root_path + "/translations/en.json", "r") as file:
            translation = json.load(file)
            return translation

def newLoginToken():
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(65))
    return result_str

def getError(error):
    translations = getLang()
    return translations["errors"][str(error)]

def validLogin():
    if not request.cookies.get("login_token"):
        return False
    else:
        if not users.find_one({ "login_token": request.cookies.get("login_token") }):
            return False
        else:
            return True

def getUsername():
	key = users.find_one({ "login_token": request.cookies.get("login_token") })
	return key["username"]

@app.route("/", strict_slashes = False)
def main():
    if validLogin() == False:
        return redirect("/login")
    else:
        return render_template("hello.html", lang = getLang(), username = getUsername())

@app.route("/settings", strict_slashes = False)
def settings():
    if validLogin() == False:
        return redirect("/")
    else:
        return render_template("settings.html", lang = getLang())

@app.route("/login", strict_slashes = False)
def login():
		if request.args.get("service"):
			if request.args.get("service") == "255":
				return render_template("login.html", lang = getLang(), service = "255")
			elif request.args.get("service") == "fasmga":
				return render_template("login.html", lang = getLang(), service = "fasmga")
			elif request.args.get("service") == "toolbox":
				return render_template("login.html", lang = getLang(), service = "toolbox")
			else:
				return render_template("login.html", lang = getLang(), service = "")
		else:
			if validLogin() == False:
				return render_template("login.html", lang = getLang(), service = "")
			else:
				return redirect("/")

@app.route("/actions/signup", methods = ["POST"], strict_slashes = False)
def do_signup():
	if not request.form["username"]: return ""
	if not request.form["password"]: return ""
	if users.find_one({ "username": request.form["username"] }):
		return render_template("error.html", code = 403, error = getError(782), lang = getLang())
	else:
		if len(request.form["username"]) > 30: return render_template("error.html", code = 400, error = getError(783), lang = getLang())
		login_token = newLoginToken()
		api_token = newLoginToken()
		while users.find_one({ "login_token": login_token }):
			login_token = newLoginToken()
			api_token = newLoginToken()
		users.insert_one({ "username": request.form["username"], "password": hashlib.sha512(request.form["password"].encode()).hexdigest(), "login_token": hashlib.sha512(login_token.encode()).hexdigest(), "is_banned": False, "api_token": api_token })
		if request.args.get("service"):
			if request.args.get("service") == "255":
				whattodo = redirect("https://255.fasmga.org/login/confirm?user_token=" + login_token)
			elif request.args.get("service") == "fasmga":
				whattodo = redirect("https://www.fasmga.org/login/confirm?user_token=" + login_token)
			elif request.args.get("service") == "toolbox":
				whattodo = redirect("https://toolbox.fasmga.org/login/confirm?user_token=" + login_token)
			else:
				whattodo = redirect("/")
		resp = make_response(whattodo)
		resp.set_cookie("login_token", login_token, 15780000)
		return resp

@app.route("/actions/login", methods = ["POST"], strict_slashes = False)
def do_login():
	if not request.form["username"]: return ""
	if not request.form["password"]: return ""
	if users.find_one({ "username": request.form["username"] }):
		if users.find_one({ "password": hashlib.sha512(request.form["password"].encode()).hexdigest(), "username": request.form["username"] }):
			user = users.find_one({ "password": hashlib.sha512(request.form["password"].encode()).hexdigest(), "username": request.form["username"] })
			whattodo = redirect("/")
			if request.args.get("service"):
				if request.args.get("service") == "255":
					whattodo = redirect("https://255.fasmga.org/login/confirm?user_token=" + user["login_token"])
				elif request.args.get("service") == "fasmga":
					whattodo = redirect("https://www.fasmga.org/login/confirm?user_token=" + user["login_token"])
				elif request.args.get("service") == "toolbox":
					whattodo = redirect("https://toolbox.fasmga.org/login/confirm?user_token=" + user["login_token"])
				else:
					whattodo = redirect("/")
			else:
				whattodo = redirect("/")
			resp = make_response(whattodo)
			if validLogin() == False:
				resp.set_cookie("login_token", user["login_token"], 15780000)
			return resp
		else:
			return render_template("error.html", code = 403, error = getError(781), lang = getLang())
	else:
		return render_template("error.html", code = 403, error = getError(780), lang = getLang())

@app.route("/signup", strict_slashes = False)
def signup():
    if validLogin() == False:
        return render_template("signup.html", lang = getLang())
    else:
        return redirect("/")

@app.route("/logout", methods = ["GET", "POST"], strict_slashes = False)
def logout():
	resp = make_response(redirect("/"))
	resp.set_cookie("login_token", "", 0)
	return resp

@app.route("/favicon.ico", strict_slashes = False)
def favicon():
    return send_from_directory(app.root_path + "/assets", "favicon.ico")

@app.route("/texture.png", strict_slashes = False)
def texture():
    return send_from_directory(app.root_path + "/assets", "texture.png")

@app.errorhandler(400)
def error_400(error):
    if validLogin() == False:
        return render_template("nl_error.html", lang = getLang(), code = "400", error = getError(400))
    else:
        return render_template("error.html", lang = getLang(), code = "400", error = getError(400))

@app.errorhandler(404)
def error_404(error):
    if validLogin() == False:
        return render_template("nl_error.html", lang = getLang(), code = "404", error = getError(404))
    else:
        return render_template("error.html", lang = getLang(), code = "404", error = getError(404))

@app.errorhandler(405)
def error_405(error):
    if validLogin() == False:
        return render_template("nl_error.html", lang = getLang(), code = "405", error = getError(405))
    else:
        return render_template("error.html", lang = getLang(), code = "405", error = getError(405))        

@app.errorhandler(500)
def error_500(error):
    if validLogin() == False:
        return render_template("nl_error.html", lang = getLang(), code = "500", error = getError(500))
    else:
        return render_template("error.html", lang = getLang(), code = "500", error = getError(500))

app.run("0.0.0.0")