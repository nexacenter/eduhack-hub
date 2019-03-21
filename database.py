import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import config as CONFIG
 
Base = declarative_base()
 
class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    link = Column(String(256), nullable=False)
 
class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, primary_key=True)
    link = Column(String(256), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    title = Column(String(256), nullable=False)
    thumb = Column(String(256), nullable=False) # link to jetpack media thumb
    authorid = Column(Integer, ForeignKey('author.id'))
    author = relationship(Author)
 
class Category(Base):
    __tablename__ = 'category'
    # both tags and categories
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    type = Column(Integer, nullable=False)

class PostHasCategory(Base):
    __tablename__ = 'posthascategory'
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    pid = Column(Integer, ForeignKey('post.id'))
    post = relationship(Post)
    type = Column(String(64), nullable=False)

engine = create_engine(CONFIG.db)
 
if not database_exists(engine.url):
    create_database(engine.url)
    Base.metadata.create_all(engine)
 
Session = sessionmaker(bind=engine)
