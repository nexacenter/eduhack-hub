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

categorymap = {
    "Activity 1.1":"Activity 1.1 - Search for Open Educational Resources (OER)",
    "Activity 1.2":"Activity 1.2 - Modify existing digital content by using Wikis",
    "Activity 1.3":"Activity 1.3 - Create digital educational resources",
    "Activity 1.4":"Activity 1.4 - Curate and organise digital resources",
    "Activity 1.5":"Activity 1.5 - Apply open licenses to your resources",
    "Activity 2.1":"Activity 2.1 - Design your own eLearning intervention",
    "Activity 2.2":"Activity 2.2 - Implement ICT-supported collaborative learning",
    "Activity 2.3":"Activity 2.3 - Guide and support students through e-moderation",
    "Activity 2.4":"Activity 2.4 - Foster knowledge co-creation among students",
    "Activity 2.5":"Activity 2.5 - Create and select video resources for your teaching",
    "Activity 2.6":"Activity 2.6 - Use games to improve learners engagement",
    "Activity 3.1":"Activity 3.1 - Explore digitally supported assessment strategies",
    "Activity 3.2":"Activity 3.2 - Experiment with different technologies for formative assessment",
    "Activity 3.3":"Activity 3.3 - Analyse evidence on learning activity, performance and progress",
    "Activity 3.4":"Activity 3.4 - Use digital technologies to provide targeted feedback to learners",
    "Activity 4.1":"Activity 4.1 - Critically evaluate online tools",
    "Activity 4.2":'Activity 4.2 - Discover the cost of "free" commercial social media platforms',
    "Activity 4.3":"Activity 4.3 - Appreciate opportunities and risks of personalization in learning",
    "Activity 4.4":"Activity 4.4 - Check technical accessibility of platforms and resources",
    "A1.1 Search for Open Educational Resources (OER)":"Activity 1.1 - Search for Open Educational Resources (OER)",
    "A1.2 Modify existing digital content by using Wikis":"Activity 1.2 - Modify existing digital content by using Wikis",
    "A1.3 Create digital educational resources":"Activity 1.3 - Create digital educational resources",
    "A1.4 Curate and organise digital resources":"Activity 1.4 - Curate and organise digital resources",
    "A1.5 Apply open licenses to your resources":"Activity 1.5 - Apply open licenses to your resources",
    "A2.1 Design your own eLearning intervention":"Activity 2.1 - Design your own eLearning intervention",
    "A2.2 Implement ICT-supported collaborative learning":"Activity 2.2 - Implement ICT-supported collaborative learning",
    "A2.3 Guide and support students through e-moderation":"Activity 2.3 - Guide and support students through e-moderation",
    "A2.4 Foster knowledge co-creation among students":"Activity 2.4 - Foster knowledge co-creation among students",
    "A2.5 Create and select video resources for your teaching":"Activity 2.5 - Create and select video resources for your teaching",
    "A2.6 Use games to improve learners engagement":"Activity 2.6 - Use games to improve learners engagement",
    "A3.1 Explore digitally supported assessment strategies":"Activity 3.1 - Explore digitally supported assessment strategies",
    "A3.2 Experiment with different technologies for formative assessment":"Activity 3.2 - Experiment with different technologies for formative assessment",
    "A3.3 Analyse evidence on learning activity, performance and progress":"Activity 3.3 - Analyse evidence on learning activity, performance and progress",
    "A3.4 Use digital technologies to provide targeted feedback to learners":"Activity 3.4 - Use digital technologies to provide targeted feedback to learners",
    "A4.1 Critically evaluate online tools":"Activity 4.1 - Critically evaluate online tools",
    "A4.2 Discover the cost of \"free\" commercial social media platforms":'Activity 4.2 - Discover the cost of "free" commercial social media platforms',
    "A4.3 Appreciate opportunities and risks of personalization in learning":"Activity 4.3 - Appreciate opportunities and risks of personalization in learning",
    "A4.4 Check technical accessibility of platforms and resources":"Activity 4.4 - Check technical accessibility of platforms and resources",
    "Area 1":"Area 1 - Digital Resources",
    "Area 2":"Area 2 - Teaching",
    "Area 3":"Area 3: Assessment",
    "Area 4":"Area 4: Empowering Learners",
    "Digital Resources":"Area 1 - Digital Resources",
    "Teaching":"Area 2 - Teaching",
    "Assessment":"Area 3: Assessment",
    "Empowering students":"Area 4: Empowering Learners",
    "A1 Digital Resources":"Area 1 - Digital Resources",
    "A2 Teaching":"Area 2 - Teaching",
    "A3 Assessment":"Area 3: Assessment",
    "A4 Empowering Learners":"Area 4: Empowering Learners"
}

