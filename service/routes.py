######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product, Category
from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    #
    # Uncomment this line of code once you implement READ A PRODUCT
    #
    location_url = url_for("get_products", product_id=product.id, _external=True)
    # location_url = "/"  # delete once READ is implemented
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################

@app.route("/products", methods=["GET"])
def list_products():
    """Returns a list of Products"""
    app.logger.info("Request to list Products...")

    # Initialize an empty list to hold the products.
    products = []
    # Get the `name` parameter from the request (hint: use `request.args.get()`
    name = request.args.get("name")
    # Get the `category` parameter from the request (hint: use `request.args.get()`
    category = request.args.get("category")
    # Get the `available` parameter from the request (hint: use `request.args.get()`
    available = request.args.get("available")
    # test to see if you received the "name" query parameter
    if name:
        app.logger.info("Find by name: %s", name)
        # If you did, call the Product.find_by_name(name) method
        # to retrieve products that match the specified name
        products = Product.find_by_name(name)

    # test to see if you received the "category" query parameter
    elif category:
        app.logger.info("Find by category: %s", category)
        # If you did, convert the category string retrieved from the query parameters
        # to the corresponding enum value from the Category enumeration
        category_value = getattr(Category, category.upper())
        # call the Product.find_by_category(category_value) method to retrieve products
        # that match the specified category_value
        products = Product.find_by_category(category_value)

    # test to see if you received the "available" query parameter
    elif available:
        app.logger.info("Find by category: %s", category)
        # If you did, convert the available string retrieved from the query parameters to a boolean value
        available_value = available.lower() in ["true", "yes", "1"]
        # call the Product.find_by_availability(available_value) method to retrieve products that
        # match the specified available_value
        products = Product.find_by_availability(available_value)

    else:
        app.logger.info("Find all")
        # If you didn't call list all
        products = Product.all()

    # create a list of serialize() products
    results = [product.serialize() for product in products]
    # log the number of products being returned in the list
    app.logger.info(f"{len(results)} Products returned.")
    # return the list with a return code of status.HTTP_200_OK
    return results, status.HTTP_200_OK

######################################################################
# R E A D   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    """
    Retrieve a single Product
    This endpoint will return a Product based on it's id
    """
    app.logger.info("Request to Retrieve a product with id [%s]", product_id)
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")
    app.logger.info("Returning product: %s", product.name)
    return product.serialize(), status.HTTP_200_OK


######################################################################
# U P D A T E   A   P R O D U C T
######################################################################

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Update an Product
    This endpoint will update a Product based on the body that is posted
    """
    app.logger.info("Request to Update a product with id [%s]", product_id)
    check_content_type("application/json")
    # use the Product.find() method to retrieve the product by the product_id
    product = Product.find(product_id)
    # abort() with a status.HTTP_404_NOT_FOUND if it cannot be found
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")
    # call the deserialize() method on the product passing in request.get_json()
    product.deserialize(request.get_json())
    product.id = product_id
    # call product.update() to update the product with the new data
    product.update()
    # return the serialize() version of the product with a return code of status.HTTP_200_OK
    return product.serialize(), status.HTTP_200_OK

######################################################################
# D E L E T E   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id):
    """
    Delete a Product
    This endpoint will delete a Product based the id specified in the path
    """
    app.logger.info("Request to Delete a product with id [%s]", product_id)
    # use the Product.find() method to retrieve the product by the product_id
    product = Product.find(product_id)
    # if found, call the delete() method on the product
    if product:
        product.delete()
    # return an empty body ("") with a return code of status.HTTP_204_NO_CONTENT
    return "", status.HTTP_204_NO_CONTENT
