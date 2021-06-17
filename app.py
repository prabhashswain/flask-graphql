from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import os

from sqlalchemy.orm import backref
from flask_graphql import GraphQLView
import graphene
from flask_graphql_auth import GraphQLAuth,create_access_token,create_refresh_token,get_jwt_identity,mutation_jwt_refresh_token_required,query_header_jwt_required
from werkzeug.security import generate_password_hash,check_password_hash
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy import SQLAlchemyConnectionField

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(BASE_DIR,'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'PRABHASH@198435'
app.config['REFRESH_EXP_LENGTH'] = 30
app.config['ACCESS_EXP_LENGTH'] = 10
app.config['JWT_SECRET_KEY'] = 'Bearer'
CORS(app)
auth = GraphQLAuth(app)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),unique=True,nullable=False)
    email = db.Column(db.String(100),unique=True,nullable=False)
    password = db.Column(db.String(100))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    last_login = db.Column(db.DateTime)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))

    def __str__(self) -> str:
        return self.username

class Category(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    product = db.relationship('Product',
               foreign_keys='Product.category_id',
               backref='product',
               lazy=True)

    def __str__(self) -> str:
        return self.name

class Product(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),unique=True)
    description = db.Column(db.Text())
    price = db.Column(db.Float())
    quantity = db.Column(db.Integer())
    category_id = db.Column(db.Integer,db.ForeignKey('category.id'))





class Register(graphene.Mutation):
    error = graphene.String()
    msg = graphene.String()
    success = graphene.Boolean()
    
    class Arguments:
        email = graphene.String(required=True)
        username = graphene.String(required=True)
        password1 = graphene.String(required=True)
        password2 = graphene.String(required=True)

    @classmethod
    def mutate(cls,root,info,email,username,password1,password2):
        if password1 != password2:
            return Register(error="password does not match")
        try:
            new_user = User(
                email = email,
                username = username,
                password = generate_password_hash(password1,method='sha256')
            )
            db.session.add(new_user)
            db.session.commit()
            return Register(
                msg = "Account Created successfully",
                success = True
            )
        except:
            return Register(error='provide valid data')

class Login(graphene.Mutation):
    access = graphene.String()
    refresh = graphene.String()
    error = graphene.String()

    class Arguments:
        email = graphene.String()
        password = graphene.String()
    
    @classmethod
    def mutate(cls,root,info,email,password):
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password,password):
            return Login(error="Bad username or password")
        return Login(
            access = create_access_token(user.id),
            refresh = create_refresh_token(user.id)
        )

class Refresh(graphene.Mutation):
    class Arguments:
        refresh_token = graphene.String()

    new_token = graphene.String()
    @classmethod
    @mutation_jwt_refresh_token_required
    def mutate(cls,root):
        current_user = get_jwt_identity()
        return Refresh(
            new_token=create_access_token(identity=current_user)
        )

class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)


class profileQuery(graphene.ObjectType):
    profile = graphene.Field(UserType)

    @classmethod
    @query_header_jwt_required
    def resolve_profile(cls,root,info,**args):
        current_user = get_jwt_identity()
        return User.query.filter_by(id=current_user).first()

class CategoryType(SQLAlchemyObjectType):
    pk = graphene.Int(source='id')
    class Meta:
        model = Category
        interfaces = (graphene.relay.Node,)

class ProductType(SQLAlchemyObjectType):
    pk = graphene.Int(source='id')
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)   

class CategoryMutation(graphene.Mutation):
    category = graphene.Field(CategoryType)
    success = graphene.Boolean()
    error = graphene.String()

    class Arguments:
        name = graphene.String()
    
    @classmethod
    def mutate(cls,_,info,name):
        try:
            category = Category(name=name)
            db.session.add(category)
            db.session.commit()
            return CategoryMutation(category=category,success=True)
        except:
            return CategoryMutation(error="something went wrong",success=False)


class ProductMutation(graphene.Mutation):
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    error = graphene.String()

    class Arguments:
        name = graphene.String()
        description = graphene.String() 
        price = graphene.Float()
        quantity = graphene.Int()
        category = graphene.Int()

    @classmethod
    def mutate(cls,_,info,name,description,price,quantity,category):
        product = Product(
            name = name,
            description = description,
            price = price,
            quantity = quantity,
            category_id = category
        )
        db.session.add(product)
        db.session.commit()
        return ProductMutation(product=product,success=True)

class ProductQuery(graphene.ObjectType):
    
    products = SQLAlchemyConnectionField(ProductType.connection,sort=None)
    product = graphene.Field(ProductType,pk=graphene.Int())

    @classmethod
    def resolve_products(cls,_,info):
        return Product.query.all()

    @classmethod
    def resolve_product(cls,_,info,pk):
        return Product.query.get(pk)

class Query(ProductQuery,profileQuery,graphene.ObjectType):
    pass

class Mutations(graphene.ObjectType):
    register = Register.Field()
    login = Login.Field()
    refresh = Refresh.Field()
    category = CategoryMutation.Field()
    product = ProductMutation.Field()

schema  = graphene.Schema(query=Query,mutation = Mutations)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('Flask GraphQL', schema=schema, graphiql=True))


@app.route('/')
def main():
    return "Hello Flask"

if __name__ == "__main__":
    app.run(debug=True,port=5000)