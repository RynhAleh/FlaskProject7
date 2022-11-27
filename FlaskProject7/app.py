import os
import secrets
from flask import Flask, render_template, send_from_directory, request, flash, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from PIL import Image


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
    creator_id = db.Column(db.String(100), db.ForeignKey('creator.id'), nullable=False)
    category = db.Column(db.String(20), db.ForeignKey('category.category'))
    rating = db.Column(db.Integer)
    cover = db.Column(db.String(50), nullable=False, default='default.jpg')
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Product {self.name}>'


class Category(db.Model):
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


"""################################# F O R M S ##################################"""


class ProductCreate(FlaskForm):
    name = StringField('Наименование товара', validators=[DataRequired(), Length(min=5, max=100)])
    creator_id = SelectField('Производитель', coerce=int, validators=[DataRequired()], choices=[])
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
    def validate_creator_id(self, creator_id):
        if creator_id.data == 0:
            raise ValidationError('Необходимо указать производителя. Внесите в базу при необходимости.')

    @staticmethod
    def validate_rating(self, rating):
        if rating.data == 0:
            raise ValidationError('Определитесь с оценкой')


class ProductEdit(FlaskForm):
    name = StringField('Наименование товара', validators=[DataRequired(), Length(min=5, max=100)])
    creator_id = SelectField('Производитель', coerce=int, validators=[DataRequired()], choices=[])
    category = SelectField('Категория', validators=[DataRequired()], choices=[])
    cover = FileField('Фотография товара', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    rating = SelectField('Моя оценка', coerce=int, validators=[NumberRange(min=0, max=5)], choices=[])
    description = TextAreaField('Краткое описание', validators=[DataRequired(), Length(max=500)])
    notes = TextAreaField('Дополнительная информация', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Обновить')

    @staticmethod
    def validate_creator_id(self, creator_id):
        if creator_id.data == 0:
            raise ValidationError('Необходимо указать производителя. Внесите в базу при необходимости.')

    @staticmethod
    def validate_rating(self, rating):
        if rating.data == 0:
            raise ValidationError('Определитесь с оценкой')


"""################################# R O U T E S ##################################"""


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    flt = request.args.get('flt', '', type=str)
    creator = request.args.get('creator', 0, type=int)
    rtn = request.args.get('rtn', 0, type=int)
    items_per_page: int = 5
    categories = Category.query.all()
    creators = Creator.query.all()
    products = db.session.query(Product, Category)\
        .join(Category, Product.category == Category.category)\
        .filter(Product.rating >= rtn, True if flt == '' else Product.category == flt, True if creator == 0 else Product.creator_id == creator)\
        .order_by(Product.created_at.desc()).paginate(page=page, per_page=items_per_page)
    return render_template('index.html', products=products, categories=categories, creators=creators, page=page, flt=flt, creator=creator, rtn=rtn, view='index')


@app.route('/rows/')
def rows():
    page = request.args.get('page', 1, type=int)
    flt = request.args.get('flt', '', type=str)
    creator = request.args.get('creator', 0, type=int)
    rtn = request.args.get('rtn', 0, type=int)
    items_per_page: int = 13
    categories = Category.query.all()
    creators = Creator.query.all()
    products = db.session.query(Product, Category)\
        .join(Category, Product.category == Category.category)\
        .filter(Product.rating >= rtn, True if flt == '' else Product.category == flt, True if creator == 0 else Product.creator_id == creator)\
        .order_by(Product.created_at.desc()).paginate(page=page, per_page=items_per_page)
    return render_template('rows.html', products=products, categories=categories, creators=creators, flt=flt, creator=creator, page=page, rtn=rtn, view='rows')


@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/<int:product_id>/')
def product(product_id):
    prod = Product.query.get_or_404(product_id)
    flt = request.args.get('flt', '', type=str)
    creator = request.args.get('creator', 0, type=int)
    rtn = request.args.get('rtn', 0, type=int)
    view = request.args.get('view', 'index', type=str)
    page = request.args.get('page', 1, type=int)
    categories = Category.query.all()
    creators = Creator.query.all()

    clr = db.session.query(Category.clr).filter(Category.category == prod.category).first()  # без .first() был бы кортеж, а так - запись БД

    aboutcreator = db.session.query(Creator).filter(Creator.id == prod.creator_id).first()  # без .first() был бы кортеж, а так - запись БД
    return render_template('product.html', categories=categories, creators=creators, page=page, aboutcreator=aboutcreator, clr=clr, product=prod, flt=flt, creator=creator, rtn=rtn, view=view)


def save_picture(cover):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(cover.filename)
    picture_fn = random_hex + f_ext   # присваиваем рандомное имя
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_fn)

    i = Image.open(cover)
    i.thumbnail((440, 680))  # сжимаем файл до нужных размеров
    i.save(picture_path)

    return picture_fn


@app.route('/create/', methods=('GET', 'POST'))
def create():
    form = ProductCreate()
    form.category.choices = [category.category for category in Category.query.all()]
    form.creator_id.choices = [(0, '(выбрать)')]+[(creator.id, creator.brand) for creator in Creator.query.all()]
    form.rating.choices = [(0, '(нет оценки)'), (1, '1-отвратительно'), (2, '2-плохо'), (3, '3-средне'), (4, '4-хорошо'), (5, '5-отлично')]
    flt = request.args.get('flt', '', type=str)
    creator = request.args.get('creator', 0, type=int)
    rtn = request.args.get('rtn', 0, type=int)
    view = request.args.get('view', 'index', type=str)
    categories = Category.query.all()
    creators = Creator.query.all()
    if form.validate_on_submit():  # форма прошла проверку - сохранение введенных данных
        if form.cover.data:
            cover = save_picture(form.cover.data)
        else:
            cover = 'default.jpg'
        name = form.name.data
        creator_id = form.creator_id.data
        category = form.category.data
        rating = form.rating.data
        description = form.description.data
        notes = form.notes.data
        prod = Product(name=name, creator_id=creator_id, category=category, rating=rating, cover=cover, description=description, notes=notes)
        db.session.add(prod)
        db.session.commit()
        return redirect(url_for(view, flt=flt, creator=creator, rtn=rtn, view=view))

    return render_template('create.html', categories=categories, creators=creators, form=form, flt=flt, creator=creator, rtn=rtn, view=view)


@app.route('/<int:product_id>/edit/', methods=('GET', 'POST'))
def edit(product_id):

    prod = Product.query.get_or_404(product_id)
    form = ProductEdit(creator_id=prod.creator_id, category=prod.category, rating=prod.rating)  # Значения полей раскрывающихся списков устанавливаются здесь
    form.creator_id.choices = [(creator.id, creator.brand) for creator in Creator.query.all()]
    form.category.choices = [category.category for category in Category.query.all()]
    form.rating.choices = [(0, '(нет оценки)'), (1, '1-отвратительно'), (2, '2-плохо'), (3, '3-средне'), (4, '4-хорошо'), (5, '5-отлично')]
    page = request.args.get('page', 1, type=int)  # после изменения остаемся на том же листе
    flt = request.args.get('flt', '', type=str)
    creator = request.args.get('creator', 0, type=int)
    rtn = request.args.get('rtn', 0, type=int)
    view = request.args.get('view', 'index', type=str)
    categories = Category.query.all()
    creators = Creator.query.all()

    if request.method == 'GET':  # открытие для редактирования (заполнение формы данными)
        form.name.data = prod.name
        # form.creator_id.data = prod.creator_id
        # form.category.data = prod.genre_id      # здесь бесполезно ставить, только в параметры при присвоении form = BookForm (...) см.выше
        # form.rating.data = prod.rating
        form.cover.data = prod.cover
        form.description.data = prod.description
        form.notes.data = prod.notes

    elif form.validate_on_submit():  # форма прошла проверку - сохранение измененных данных
        if form.cover.data:
            if form.cover.data != prod.cover:
                prod.cover = save_picture(form.cover.data)
        prod.name = form.name.data
        prod.creator_id = form.creator_id.data
        prod.category = form.category.data
        prod.rating = int(form.rating.data)
        prod.description = form.description.data
        prod.notes = form.notes.data
        try:
            db.session.commit()
            return redirect(url_for(view, page=page, flt=flt, creator=creator, rtn=rtn, view=view))
        except IntegrityError:
            db.session.rollback()
            flash('Произошла ошибка: такой товар уже есть в базе', 'error')
            return render_template('edit.html', categories=categories, creators=creators, form=form, page=page, flt=flt, creator=creator, rtn=rtn, view=view)

    return render_template('edit.html', categories=categories, creators=creators, form=form, page=page, flt=flt, creator=creator, rtn=rtn, view=view)


@app.post('/<int:product_id>/delete/')
def delete(product_id):
    flt = request.args.get('flt', '', type=str)
    creator = request.args.get('creator', 0, type=int)
    rtn = request.args.get('rtn', 0, type=int)
    view = request.args.get('view', 'index', type=str)
    prod = Product.query.get_or_404(product_id)
    db.session.delete(prod)
    db.session.commit()
    return redirect(url_for(view, flt=flt, creator=creator, rtn=rtn, view=view))


@app.route('/export/')
def data():
    dt = Product.query.all()
    return jsonify(dt)


"""#################################  L A U N C H  ##################################"""

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
