import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import sys

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type, Authorization"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE"
    )
    return response


db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    all_drinks = Drink.query.order_by(Drink.id).all()

    if len(all_drinks) == 0:
        abort(404)

    drinks_data = [Drink.short(d) for d in all_drinks]

    return jsonify(
        {
            "success": True,
            "drinks": drinks_data
        }
    ), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    all_drinks = Drink.query.order_by(Drink.id).all()

    if len(all_drinks) == 0:
        abort(404)

    drinks_data = [d.long() for d in all_drinks]

    return jsonify(
        {
            "success": True,
            "drinks": drinks_data
        }
    ), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink(jwt):
    body = request.get_json()
    n_title = body.get("title")
    n_recipe = body.get("recipe")
    n_recipe = json.dumps(n_recipe)

    try:
        drink = Drink(title=n_title, recipe=n_recipe)
        drink.insert()

        return jsonify(
            {
                "success": True,
                "drinks": drink.long()
            }
        ), 200
    except:
        print(sys.exc_info())
        abort(422)    
   

@app.route("/drinks/<int:drinkid>", methods=["PATCH"])
@requires_auth('patch:drinks')
def patch_drink(jwt, drinkid):
    body = request.get_json()
    title = body.get("title")
    recipe = body.get("recipe")

    drink = Drink.query.filter(Drink.id == drinkid).one_or_none()

    if drink is None:
        abort(404)

    if title:
        drink.title = title
    if recipe:
        drink.recipe = json.dumps(recipe)

    drink.update()

    return jsonify(
        {
            "success": True,
            "drinks": drink.long()
        }
    ), 200


@app.route("/drinks/<int:drinkid>", methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drink(jwt, drinkid):
    drink = Drink.query.filter(Drink.id == drinkid).one_or_none()
    if drink is None:
        abort(404)

    drink.delete()

    return jsonify(
        {
            "success": True,
            "delete": drinkid
        }
    ), 200


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422



@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "forbidden"
    }), 403 

@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404        


@app.errorhandler(AuthError)
def auth_error(ae):
    return jsonify({
        "success": False,
        "error": ae.status_code,
        "message": ae.error
    }), ae.status_code 
