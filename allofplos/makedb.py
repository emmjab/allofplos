#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Make a SQLite DB out of articles XML files
"""

from bs4 import BeautifulSoup
import os
import random
import progressbar

from transformations import filename_to_doi
from article_class import Article

from peewee import Model, CharField, ForeignKeyField, TextField, \
    DateTimeField, BooleanField, IntegerField, IntegrityError
from playhouse.sqlite_ext import SqliteExtDatabase
import datetime

corpusdir = 'allofplos_xml'

journal_title_dict = {
'PLoS One':'PLOS ONE',
'PLoS ONE':'PLOS ONE',
'PLOS ONE':'PLOS ONE',
'PLOS Genetics':'PLOS Genetics',
'PLoS Genet':'PLOS Genetics',
'PLoS Genetics':'PLOS Genetics',
'PLoS Neglected Tropical Diseases':'PLOS Neglected Tropical Diseases',
'PLOS Neglected Tropical Diseases':'PLOS Neglected Tropical Diseases',
'PLoS Negl Trop Dis':'PLOS Neglected Tropical Diseases',
'PLoS Biology':'PLOS Biology',
'PLOS Biology':'PLOS Biology',
'PLoS Biol':'PLOS Biology',
'PLOS Clinical Trials': 'PLOS Clinical Trials',
'PLoS Medicine':'PLOS Medicine',
'PLoS Medicin': 'PLOS Medicine',
'PLos Med': 'PLOS Medicine',
'PLoS Med': 'PLOS Medicine',
'PLOS Med': 'PLOS Medicine',
'PLOS Medicine': 'PLOS Medicine',
'PLoS Pathog': 'PLOS Pathogens',
'PLOS Pathog': 'PLOS Pathogens',
'PLOS Pathogens': 'PLOS Pathogens',
'PLoS Pathogens': 'PLOS Pathogens',
'PLoS Computational Biology': 'PLOS Computational Biology',
'PLOS Computational Biology': 'PLOS Computational Biology',
'PLoS Comput Biol': 'PLOS Computational Biology',
'PLOS Comput Biol': 'PLOS Computational Biology',
'PLoS Clinical Trials': 'PLOS Clinical Trials',
}

db = SqliteExtDatabase('my_database.db')

class BaseModel(Model):
    class Meta:
        database = db

class DOI(BaseModel):
    doi = CharField(unique=True)

class Journal(BaseModel):
    journal = CharField(unique=True)

class ArticleType(BaseModel):
    article_type = CharField(unique=True)

class CorrespondingAuthor(BaseModel):
    corr_author_email = CharField(unique=True)
    given_name = TextField()
    surname = TextField()
    group_name = TextField(null=True)

class PLOSArticle(BaseModel):
    article_id = ForeignKeyField(DOI, related_name='articles')
    abstract = TextField()
    title = TextField()
    plostype_id = ForeignKeyField(ArticleType, related_name='arttype')
    journal_id = ForeignKeyField(Journal, related_name='journals')
    created_date = DateTimeField(default=datetime.datetime.now)
    word_count = IntegerField()
    #corr_author = ForeignKeyField(CorrespondingAuthor, related_name='corrauthor')
    #is_published = BooleanField(default=True)

class CoAuthorPLOSArticle(BaseModel):
    corr_author = ForeignKeyField(CorrespondingAuthor)
    article = ForeignKeyField(PLOSArticle)

db.connect()
try:
    db.create_tables([DOI, Journal, PLOSArticle, ArticleType,
                      CoAuthorPLOSArticle, CorrespondingAuthor])
except:
    pass

allfiles = os.listdir(corpusdir)
randomfiles = random.sample(allfiles, 500)
max_value = len(randomfiles)
bar = progressbar.ProgressBar(redirect_stdout=True, max_value=max_value)
for i, file_ in enumerate(randomfiles):
    #print(file_)
    doi = filename_to_doi(file_)
    article = Article(doi)
    #import pdb; pdb.set_trace()
    doi = DOI.create(doi=doi)
    doi.save()
    journal_name = journal_title_dict[article.journal]
    with db.atomic() as atomic:
        try:
            journal = Journal.create(journal = journal_name)
        except IntegrityError:
            db.rollback()
            journal = Journal.get(Journal.journal == journal_name)
    with db.atomic() as atomic:
        try:
            article_type = ArticleType.create(article_type = article.plostype)
        except IntegrityError:
            db.rollback()
            article_type = ArticleType.get(ArticleType.article_type == article.plostype)
    #import pdb; pdb.set_trace()
    p_art = PLOSArticle.create(
        article_id = doi,
        journal_id = journal,
        abstract=article.abstract.replace('\n', '').replace('\t', ''),
        title = article.title.replace('\n', '').replace('\t', ''),
        plostype_id = article_type,
        created_date = article.pubdate,
        word_count=article.word_count)
    p_art.save()
    ###
    #import pdb; pdb.set_trace()
    for auths in article.authors:
        if auths['email']:
            print(auths['email'][0])
            try:
                co_author = CorrespondingAuthor.create(
                    corr_author_email = auths['email'][0],
                    given_name = auths['given_names'],
                    surname = auths['surname'],
                    group_name = auths['group_name']
                    )
                co_author.save()
            except IntegrityError:
                co_author = CorrespondingAuthor.\
                            get(CorrespondingAuthor.corr_author_email == auths['email'][0])
            coauthplosart = CoAuthorPLOSArticle.create(
                    corr_author = co_author,
                    article = p_art
                )
            coauthplosart.save()
    bar.update(i+1)
bar.finish()
