from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from flask_graphql import GraphQLView
import graphene
from flask_graphql_auth import GraphQLAuth,create_access_token,create_refresh_token,get_jwt_identity,mutation_jwt_refresh_token_required,query_header_jwt_required
from werkzeug.security import generate_password_hash,check_password_hash
from graphene_sqlalchemy import SQLAlchemyObjectType

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(BASE_DIR,'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'PRABHASH@198435'
app.config['REFRESH_EXP_LENGTH'] = 30
app.config['ACCESS_EXP_LENGTH'] = 10
app.config['JWT_SECRET_KEY'] = 'Bearer'

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

class Mutations(graphene.ObjectType):
    register = Register.Field()
    login = Login.Field()
    refresh = Refresh.Field()

class Query(graphene.ObjectType):
    profile = graphene.Field(UserType)

    @classmethod
    @query_header_jwt_required
    def resolve_profile(cls,root,info,**args):
        current_user = get_jwt_identity()
        return User.query.filter_by(id=current_user).first()


schema  = graphene.Schema(query=Query,mutation = Mutations)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('Flask GraphQL', schema=schema, graphiql=True))


@app.route('/')
def main():
    return "Hello Flask"

if __name__ == "__main__":
    app.run(debug=True,port=5000)