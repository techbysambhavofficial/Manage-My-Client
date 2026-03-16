from flask import Flask, render_template, request, redirect, session, Response
from pymongo import MongoClient
from bson.objectid import ObjectId
import urllib.parse
import csv

from config import MONGO_URI, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client["client_db"]
collection = db["clients"]

users = {
    "admin": "admin123"
}

# DEFAULT MESSAGE
DEFAULT_MESSAGE = """
Hello Sir,

My name is Sambhav. I am a developer and currently building simple student management systems for coaching institutes in Bhubaneswar.

This system helps institutes with:
• Online admission
• Student login portal
• Test series management

I noticed many institutes still manage these manually.

If you allow, I can show a short preview of how it works.
"""

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    total = collection.count_documents({})
    contacted = collection.count_documents({"status":"Contacted"})
    interested = collection.count_documents({"status":"Interested"})
    closed = collection.count_documents({"status":"Deal Closed"})

    return render_template(
        "dashboard.html",
        total=total,
        contacted=contacted,
        interested=interested,
        closed=closed
    )


# VIEW CLIENTS
@app.route("/")
def index():

    if "user" not in session:
        return redirect("/login")

    clients = list(collection.find())

    return render_template("index.html", clients=clients)


# ADD CLIENT
@app.route("/add", methods=["GET","POST"])
def add_client():

    if request.method == "POST":

        data = {
            "name": request.form["name"],
            "business": request.form["business"],
            "phone": request.form["phone"],
            "email": request.form["email"],
            "notes": request.form["notes"],
            "status": request.form["status"]
        }

        collection.insert_one(data)

        return redirect("/")

    return render_template("add_client.html")


# EDIT CLIENT
@app.route("/edit/<id>", methods=["GET","POST"])
def edit_client(id):

    client = collection.find_one({"_id":ObjectId(id)})

    if request.method == "POST":

        collection.update_one(
            {"_id":ObjectId(id)},
            {"$set":{
                "name":request.form["name"],
                "business":request.form["business"],
                "phone":request.form["phone"],
                "email":request.form["email"],
                "notes":request.form["notes"],
                "status":request.form["status"]
            }}
        )

        return redirect("/")

    return render_template("edit_client.html", client=client)


# DELETE CLIENT
@app.route("/delete/<id>")
def delete_client(id):

    collection.delete_one({"_id":ObjectId(id)})

    return redirect("/")


# SEARCH CLIENT
@app.route("/search")
def search():

    query = request.args.get("q")

    results = collection.find({
        "name":{"$regex":query,"$options":"i"}
    })

    return render_template("index.html", clients=results)


# EXPORT CSV
@app.route("/export")
def export():

    clients = collection.find()

    def generate():

        yield "Name,Business,Phone,Email,Status\n"

        for c in clients:
            yield f"{c['name']},{c['business']},{c['phone']},{c['email']},{c['status']}\n"

    return Response(generate(), mimetype="text/csv")


# SEND WHATSAPP MESSAGE
@app.route("/send_whatsapp/<phone>")
def send_whatsapp(phone):

    message = urllib.parse.quote(DEFAULT_MESSAGE)

    whatsapp_url = f"https://wa.me/{phone}?text={message}"

    return redirect(whatsapp_url)


# SEND EMAIL MESSAGE
@app.route("/send_email/<email>")
def send_email(email):

    subject = "Student Management System Demo"
    body = urllib.parse.quote(DEFAULT_MESSAGE)

    subject = urllib.parse.quote(subject)

    mail_url = f"mailto:{email}?subject={subject}&body={body}"

    return redirect(mail_url)


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)