from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")

db = client.SimilarityDB
users = db["users"]
def UserExist(username):
    if users.find({"Username" : username}).count() == 0:
        return False
    else: 
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson ={
                "status" : 301,
                "msg" : "Invalid username"
            }
            return jsonify(retJson)
        
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "username" : username,
            "password" : hashed_pw,
            "Tockens" : 6
        })

        retJson = {
            "status" : 200,
            "msg" : "You successfully signed up to the API"
        }
        return jsonify(retJson)

def verifyPw(username, passsword):
    if not UserExist(username):
        return False
    hashed_pw = users.find({
        "username" : username
    })[0]["password"]

    if bcrypt.hashpw(passsword.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "username" : username
    })[0]["Tokens"]
    return tokens

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        passsword = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "Invalid username"
            }
            return jsonify(retJson)
        
        correct_pw = verifyPw(username, password)

        if not correct_pw:
            retJson = {
                "status" : 302,
                "msg" : "Invalid password"
            }
            return jsonify(retJson)

        num_tokens = countTokens(username)

        if num_tokens <= 0:
            retJson = {
                "status" : 303,
                "msg" : "out of token please refill"
            }
            return jsonify(retJson)

        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)

        #ratio is number between 0 and 1,the closer to 1, 
        # the more similar text1 and text2 are
        ratio = text1.similarity(text2)

        retJson= {
            "status" : 200,
            "similarity" : ratio,
            "msg" : "similarity score calculated"
        }

        current_tokens = countTokens(username)
        users.update({
            "username" : username,
        },{
            "$set" : {
                "Tokens" : current_tokens-1
            }
        })
        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "Invalid username"
            }

        correct_pw = "admin123"

        if not password != correct_pw:
            retJson ={
                "status" : 304,
                "msg" : "Invalid Admin Password"
            }
            return jsonify(retJson)

        current_tokens = countTokens(username)
        users.update({
            "username" : username
        },{
            "$set" : {
                "Tokens" : refill_amount + current_tokens
            }
        })
        retJson = {
            "status" : 200,
            "msg" : "refilled successfully"
        }
        return jsonify(retJson)


api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')
if __name__ == "__main__":
    app.run(host='0.0.0.0')