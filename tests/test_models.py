# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
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

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

######################################################################
#  READ test case
######################################################################

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

######################################################################
#  UPDATE test case
######################################################################

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change it an save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        self.assertEqual(len(Product.all()), 1)
        self.assertEqual(Product.all()[0].id, original_id)
        self.assertEqual(Product.all()[0].description, "testing")

    def test_invalid_id_on_update(self):
        """ Test invalid ID update """
        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)

######################################################################
#  DELETE test case
######################################################################

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

######################################################################
#  LIST ALL test case
######################################################################

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(len(products), 0)
        for _ in range(5):
            product = ProductFactory()
            product.create()
        self.assertEqual(len(product.all()), 5)

######################################################################
#  FIND BY NAME test case
######################################################################

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        first_product = products[0].name
        count = len([product for product in products if product.name == first_product])
        found_products = Product.find_by_name(first_product)
        self.assertEqual(found_products.count(), count)
        for product in found_products:
            self.assertEqual(product.name, first_product)

######################################################################
#  FINAD BY AVAILABILITY test case
######################################################################

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_invalid_boolean_for_available(self):
        """ Test invalid type for boolean [available] """
        product = ProductFactory()
        data = product.serialize()
        data["available"] = "NotBoolean"
        with self.assertRaises(DataValidationError) as message:
            product.deserialize(data)
        self.assertEqual(
            str(message.exception),
            "Invalid type for boolean [available]: <class 'str'>"
        )

    def test_invalid_category(self):
        """ Test invalid category """
        product = ProductFactory()
        data = product.serialize()
        data["category"] = "NON_EXISTENT_CATEGORY"
        with self.assertRaises(DataValidationError) as message:
            product.deserialize(data)
        self.assertEqual(
            str(message.exception),
            "Invalid attribute: NON_EXISTENT_CATEGORY"
        )

    def test_no_data(self):
        """ Test no data """
        product = ProductFactory()
        data = None
        with self.assertRaises(DataValidationError) as message:
            product.deserialize(data)
        self.assertEqual(
            str(message.exception),
            "Invalid product: body of request contained bad or no data 'NoneType' object is not subscriptable"
        )

######################################################################
#  FIND BY CATEGORY test case
######################################################################

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        price = products[0].price
        found = Product.find_by_price(price)
        for product in found:
            self.assertEqual(product.price, price)

    def test_price_conversion_from_string(self):
        """Test case where price is given as a string"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        price_str = str(products[0].price)
        price_decimal = Decimal(products[0].price)
        result = Product.find_by_price(price_str)
        for product in result:
            self.assertEqual(product.price, price_decimal)
