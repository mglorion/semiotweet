# coding:utf-8
from __future__ import print_function

# For data processing
import ast
import pickle
import re
from collections import Counter, defaultdict

import requests
import treetaggerwrapper
from django.core.exceptions import ObjectDoesNotExist
# For LDA models
from gensim import corpora, models
# For requests
from lxml import html

# For the database
from semiotweet.settings import get_env_value
from .models import Tweet, LdaModel

try:
    LOCALTAGDIR = get_env_value("LOCALTAGDIR")
except BaseException as e:
    print(e)


def make_lda_model(user=0):
    """Update LDA model to avoid long processing"""
    Lda = models.ldamodel.LdaModel

    try:
        LdaModel_db = LdaModel.objects.get(user_id=user)
    except ObjectDoesNotExist:
        LdaModel_db = None

    if LdaModel_db is None:  # Make an LDA model with all tweets
        LdaModel_db = LdaModel()  # Creating an object of the class
        if user == 0:  # getting all the tweets for the global model
            allLemmaArray_raw = Tweet.objects.all().values('lemmaArray', 'id')
        else:  # getting all the tweets from a specific user
            allLemmaArray_raw = Tweet.objects.all().filter(user_id=user).values('lemmaArray', 'id')
        allLemmaArray = [ast.literal_eval(t["lemmaArray"]) for t in allLemmaArray_raw]

        # Creating the LDA model
        dictionary = corpora.Dictionary(allLemmaArray)
        corpus = [dictionary.doc2bow(document) for document in allLemmaArray]
        if (user == 0):  # Main part of the creation here
            ldamodel = Lda(corpus, num_topics=20, id2word=dictionary, passes=20)
        else:
            ldamodel = Lda(corpus, num_topics=10, id2word=dictionary, passes=20)

    else:  # Update the LDA model with the latest tweets
        ldamodel = pickle.loads(LdaModel_db.ldamodel)
        lastTweetId = LdaModel_db.tweet_id.id

        if user == 0:
            allLemmaArray_raw = Tweet.objects.all().filter(id__gt=lastTweetId).values('lemmaArray', 'id')
        else:
            allLemmaArray_raw = Tweet.objects.all().filter(user_id=user, id__gt=lastTweetId).values('lemmaArray', 'id')

        if len(allLemmaArray_raw) == 0:
            print('Already up to date...')
            return True

        allLemmaArray = [ast.literal_eval(t["lemmaArray"]) for t in allLemmaArray_raw]

        dictionary = corpora.Dictionary(allLemmaArray)
        corpus = [dictionary.doc2bow(document) for document in allLemmaArray]
        try:
            ldamodel.update(corpus)
        except IndexError:
            print("Model update failed (Gensim error)... Building from scratch again")
            LdaModel_db.delete()
            return make_lda_model(user)

    # Serializing the model & filling the data
    compressedLdaModel = pickle.dumps(ldamodel, protocol=-1)
    lastTweetId = allLemmaArray_raw[len(allLemmaArray_raw) - 1]['id']
    tweet_to_use = Tweet.objects.get(id=lastTweetId)
    LdaModel_db.user_id = user
    LdaModel_db.tweet_id = tweet_to_use
    LdaModel_db.ldamodel = compressedLdaModel

    # Saving the object in DB
    try:
        LdaModel_db.save()
        return True
    except BaseException as e:
        print("makeLdaModel() ; error : ", e)
        return False


def tokenize_and_lemmatize_tweets(listTweets):
    """Tokenize & lemmatize a list of texts"""
    global french_stop_words
    global mention_regex
    global LOCALTAGDIR

    # Setting up TreeTagger
    tagger = treetaggerwrapper.TreeTagger(TAGLANG='fr', TAGDIR=LOCALTAGDIR)

    for t in listTweets:
        text = mention_regex.sub("", t["text"]).lower()
        tags = tagger.tag_text(text)
        tags = treetaggerwrapper.make_tags(tags)
        tokens = []
        lemma = []
        # Filtering
        for tag in tags:
            if hasattr(tag, 'word'):
                if not (len(tag.lemma) < 2 or tag.lemma in french_stop_words):
                    tokens.append(tag.word)
                    lemma.append(tag.lemma)
            else:
                token = tag.what
                if not (len(token) < 2 or token in french_stop_words):
                    if token.startswith("<repurl") or token.startswith("<repdns"):
                        token = token[token.find('"') + 1:token.rfind('"')]
                    else:
                        lemma.append(token)
                    tokens.append(token)

        t["tokenArray"] = tokens
        t["lemmaArray"] = lemma

    return listTweets


def count_words(listTweetText, nbWordsToExtract=20):
    """Takes a list of text and returns the words occurences"""
    wordOccurences = defaultdict(lambda: 0)
    for tokenizedTweet in listTweetText:
        currentOccurences = dict(Counter(tokenizedTweet))
        for k in list(currentOccurences.keys()):
            wordOccurences[k] += currentOccurences[k]

    return dict(Counter(wordOccurences).most_common(nbWordsToExtract))


def to_json_for_graph(dict):
    """Return a list of dict used next for the Bubble Graph"""
    output = []
    for key, val in dict.items():
        output.append({"word": key, "occur": val})

    return output


def get_semantic_field(word):
    """Get the semantic field of the word"""
    page = requests.get('http://www.rimessolides.com/motscles.aspx?m=' + word.lower())
    tree = html.fromstring(page.content)
    aim = "motscles.aspx?m="
    semanticField = tree.xpath('//a[starts-with(@href,"' + aim + '")]/text()')

    return semanticField


# Base word used to build semantic fields
semantic_words = ["france", "état", "sécurité", "peuple", "loi", "travail", "chômage",
                 "liberté", "démocratie", "république", "immigration", "terrorisme",
                 "islam", "laïcité", "europe", "taxe", "impôts", "cannabis", "santé", "éducation"]

# French Stop words (see : http://www.ranks.nl/stopwords/french)
stopwords = ["alors", "au", "aucuns", "aussi", "autre", "avant", "avec", "avoir", "bon",
             "car", "ce", "cela", "ces", "ceux", "chaque", "ci", "comme", "comment", "dans",
             "des", "du", "dedans", "dehors", "depuis", "devrait", "doit", "donc", "dos",
             "début", "elle", "elles", "en", "encore", "essai", "est", "et", "eu", "fait",
             "faites", "fois", "font", "hors", "ici", "il", "ils", "je", "juste", "la", "le",
             "les", "leur", "là", "ma", "maintenant", "mais", "mes", "mine", "moins", "mon",
             "mot", "même", "ni", "nommés", "notre", "nous", "ou", "où", "par", "parce", "pas",
             "peut", "peu", "plupart", "pour", "pourquoi", "quand", "que", "quel", "quelle",
             "quelles", "quels", "qui", "sa", "sans", "ses", "seulement", "si", "sien", "son",
             "sont", "sous", "soyez", "sujet", "sur", "ta", "tandis", "tellement", "tels",
             "tes", "ton", "tous", "tout", "trop", "très", "tu", "voient", "vont", "votre",
             "vous", "vu", "ça", "étaient", "état", "étions", "été", "être"]

# ~ 76 most common words in french (see : https://en.wiktionary.org/wiki/Wiktionary:French_frequency_lists/1-2000)
common_words_wiki = ["de", "la", "le", "et", "les", "des", "en", "un", "du", "une",
                   "que", "est", "pour", "qui", "dans", "a", "par", "plus", "pas",
                   "au", "sur", "ne", "se", "ce", "il", "sont",
                   "ou", "avec", "son", "aux", "d'un", "cette", "d'une",
                   "ont", "ses", "mais", "comme", "on", "tout", "nous", "sa",
                   "fait", "été", "aussi", "leur", "bien", "peut", "ces", "y", "deux",
                   "à", "ans", "l", "encore", "n'est", "marché", "d", "donc",
                     "cours", "qu'il", "moins", "sans", "si", "entre",
                     "faire", "elle", "c'est", "peu", "vous", "prix",
                     "dont", "lui", "également", "effet", "pays", "cas"]

# Snowball stopwords (see : http://snowball.tartarus.org/algorithms/french/stop.txt)
common_words_snowball = ["au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du",
                       "elle", "en", "et", "eux", "il", "je", "la", "le", "leur", "lui",
                       "ma", "mais", "me", "même", "mes", "moi", "mon", "ne", "nos",
                       "notre", "nous", "on", "ou", "par", "pas", "pour", "qu",
                       "que", "qui", "sa", "se", "ses", "son", "sur", "ta", "te",
                       "tes", "toi", "ton", "tu", "un", "une", "vos", "votre",
                         "vous", "c", "d", "j", "l", "à", "m", "n", "s", "t", "y",
                         "été", "étée", "étées", "étés", "étant", "suis", "es", "est",
                         "sommes", "êtes", "sont", "serai", "seras", "sera", "serons",
                         "serez", "seront", "serais", "serait", "serions", "seriez",
                         "seraient", "étais", "était", "étions", "étiez", "étaient",
                         "fus", "fut", "fûmes", "fûtes", "furent", "sois", "soit",
                         "soyons", "soyez", "soient", "fusse", "fusses", "fût",
                         "fussions", "fussiez", "fussent", "ayant", "eu", "eue",
                         "eues", "eus", "ai", "as", "avons", "avez", "ont", "aurai",
                         "auras", "aura", "aurons", "aurez", "auront", "aurais",
                         "aurait", "aurions", "auriez", "auraient", "avais", "avait",
                         "avions", "aviez", "avaient", "eut", "eûmes", "eûtes",
                         "eurent", "aie", "aies", "ait", "ayons", "ayez", "aient",
                         "eusse", "eusses", "eût", "eussions", "eussiez", "eussent",
                         "ceci", "cela", "celà", "cet", "cette", "ici", "ils", "les",
                         "leurs", "quel", "quels", "quelle", "quelles", "sans", "soi"]

# Others common works on Twitter, not so meaningful
common_words_twitter = ["…", "rt", "ils", "faut", "https", "://", "http", "...", "ça",
                      "to", "the", "j'ai", "via", "ça", "000", "veux", "être", "devons",
                      "doit", "j'étais", "suis", "url-remplacée", "dns-remplacé",
                      "@card@", "@ord@", "gt"]

# French stopwords
french_stop_words = set(stopwords).union(set(common_words_wiki))
french_stop_words = french_stop_words.union(set(common_words_snowball))
french_stop_words = french_stop_words.union(set(common_words_twitter))

# Regex to delete user's mention in tweets
mention_regex = re.compile(r"@\w+")

request_to_get_sources = 'SELECT DISTINCT source, COUNT(source) AS nb  FROM api_tweet GROUP BY source ORDER BY nb DESC'

if __name__ == '__main__':
    # print(getSemanticField("médicament"))
    # listTweetText = ["J'aime les barbes à papa #swag",
    # "Mon cheval mange des carottes-cakes en Hiver ! #Yolo #QuelleIdée !",
    # "Quelle idée d'avoir des doigts :'("]
    # res = countWords(listTweetText)
    # for i in res.keys():
    #     print i,res[i]
    pass
