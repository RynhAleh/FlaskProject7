import os
import secrets
from flask import Flask, render_template, send_from_directory, request, flash, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from PIL import Image
from cloudipsp import Api, Checkout

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'hard to guess'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)


"""################################# M O D E L S ##################################"""


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    id_creator = db.Column(db.Integer, db.ForeignKey('creator.id'), nullable=False)
    id_category = db.Column(db.Integer, db.ForeignKey('category.id'))
    rating = db.Column(db.Integer)
    cover = db.Column(db.String(50), nullable=False, default='default.jpg')
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    price = db.Column(db.Float)
    in_action = db.Column(db.Boolean, default=False)
    new = db.Column(db.Boolean, default=False)
    in_stock = db.Column(db.Float, default=0)

    def __repr__(self):
        return f'<Product {self.name}>'


class Category(db.Model):
    id = db.Column(db.Integer, unique=True)
    category = db.Column(db.String(20), primary_key=True)
    clr = db.Column(db.String(16))

    def __repr__(self):
        return f'<Category {self.category}>'


class Creator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(30))
    info = db.Column(db.Text)
    address = db.Column(db.Text)

    def __repr__(self):
        return f'<Creator {self.brand}>'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    nickname = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(25), nullable=False)
    discount = db.Column(db.Float)

    def __repr__(self):
        return f'<User {self.nickname}>'


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_product = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Float)
    paid_for = db.Column(db.Boolean, default=False)
    received = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Cart {self.quantity} - {self.id_product}>'


"""################################# F O R M S ##################################"""


class ProductCreate(FlaskForm):
    name = StringField('Наименование товара', validators=[DataRequired(), Length(min=5, max=100)])
    id_creator = SelectField('Производитель', coerce=int, validators=[DataRequired()], choices=[])
    category = SelectField('Категория', validators=[DataRequired()], choices=[], default='--')
    cover = FileField('Фотография товара', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    rating = SelectField('Моя оценка', coerce=int, validators=[NumberRange(min=0, max=5)], choices=[], default=0)
    description = TextAreaField('Краткое описание', validators=[DataRequired(), Length(max=500)])
    notes = TextAreaField('Дополнительная информация', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Добавить')

    @staticmethod
    def validate_name(self, name):
        name = Product.query.filter_by(name=name.data).first()
        if name:
            raise ValidationError('Такой товар уже есть в базе.')

    @staticmethod
    def validate_id_creator(self, id_creator):
        if id_creator.data == 0:
            raise ValidationError('Необходимо указать производителя. Внесите в базу при необходимости.')

    @staticmethod
    def validate_rating(self, rating):
        if rating.data == 0:
            raise ValidationError('Определитесь с оценкой')


class ProductEdit(FlaskForm):
    name = StringField('Наименование товара', validators=[DataRequired(), Length(min=5, max=100)])
    id_creator = SelectField('Производитель', coerce=int, validators=[DataRequired()], choices=[])
    category = SelectField('Категория', validators=[DataRequired()], choices=[])
    cover = FileField('Фотография товара', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    rating = SelectField('Моя оценка', coerce=int, validators=[NumberRange(min=0, max=5)], choices=[])
    description = TextAreaField('Краткое описание', validators=[DataRequired(), Length(max=500)])
    notes = TextAreaField('Дополнительная информация', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Обновить')

    @staticmethod
    def validate_id_creator(self, id_creator):
        if id_creator.data == 0:
            raise ValidationError('Необходимо указать производителя. Внесите в базу при необходимости.')

    @staticmethod
    def validate_rating(self, rating):
        if rating.data == 0:
            raise ValidationError('Определитесь с оценкой')


class Quantity(FlaskForm):
    quantity = IntegerField('Количество', validators=[DataRequired(), NumberRange(min=1)])
    price = DecimalField('Цена', validators=[DataRequired()])
    submit = SubmitField('Добавить в корзину')


"""################################# R O U T E S ##################################"""


@app.route('/payment')
def payment():
    amount = request.args.get('amount', '', type=str)
    if int(amount) == 0:
        return render_template('shop_cart.html')
    api = Api(merchant_id=1396424,
              secret_key='test')
    checkout = Checkout(api=api)
    dt = {
        "currency": "BYN",
        "amount": amount
    }
    url = checkout.url(dt).get('checkout_url')
    return redirect(url)


@app.route('/')
def index():
    category = Category.query.all()
    product = Product.query.all()
    action = Product.query.filter_by(in_action=1).limit(4).all()
    cart_items_count = Cart.query.with_entities(func.sum(Cart.quantity).label('quantity')).filter_by(id_user=1).all()[0][0]
    return render_template('index.html', product=product, action=action, category=category, cart_items_count=cart_items_count)


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/delete/<int:id_product>')
def delete(id_product):
    record = Cart.query.filter(Cart.id_user == 1, Cart.id_product == id_product).first()
    db.session.delete(record)
    db.session.commit()
    return ''


@app.route('/change/<int:id_product>')
def change(id_product):
    q = request.args.get('q', 0, type=int)
    cur_quantity = Cart.query.filter(Cart.id_user == 1, Cart.id_product == id_product).first()
    Cart.query.filter(Cart.id_user == 1, Cart.id_product == id_product).update({'quantity': cur_quantity.quantity + q})
    db.session.commit()
    return ''


@app.route('/<int:id_product>')
def item(id_product):
    prod = Product.query.get_or_404(id_product)
    form = Quantity()
    category = Category.query.filter(Category.id == prod.id_category).first()  # без .first() был бы кортеж, а так - запись БД
    creator = Creator.query.filter(Creator.id == prod.id_creator).first()  # без .first() был бы кортеж, а так - запись БД
    cart_items_count = Cart.query.with_entities(func.sum(Cart.quantity).label('quantity')).filter_by(id_user=1).all()[0][0]
    return render_template('item.html', form=form, product=prod, category=category, creator=creator, cart_items_count=cart_items_count)


@app.route('/add/<int:id_product>')
def add(id_product):
    add_quantity = request.args.get('add_quantity', 0, type=int)
    exist_record = Cart.query.filter(Cart.id_user == 1, Cart.id_product == id_product).first()
    if exist_record:
        Cart.query.filter(Cart.id_user == 1, Cart.id_product == id_product).update({'quantity': exist_record.quantity + add_quantity})
        db.session.commit()
    else:
        new_record = Cart(id_user=1, id_product=id_product, quantity=add_quantity)
        db.session.add(new_record)
        db.session.commit()
    return ''


@app.route('/shop_cart')
def shop_cart():
    cart = db.session.query(Cart, Product, Category).join(Product, Cart.id_product == Product.id).join(Category, Product.id_category == Category.id)
    return render_template('shop_cart.html', cart=cart)


"""#################################  L A U N C H  ##################################"""

if __name__ == '__main__':
    app.run(debug=True)
