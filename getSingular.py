from pattern.en import parse, parsetree, wordnet, NOUN, pluralize, singularize
from pattern.text.tree import Word
import json
import sys

def readNounList(fileName):
    nounList = open(fileName, "r")
    raw = nounList.read().splitlines()
    maps = dict()
    for line in raw:
        data = line.strip().split("\t")
        key = data[0]
        cop = data[1]
        if len(data) != 14:
            print "Read list wrong!"
            sys.exit(0)
        if maps.has_key(key):
            tmp = maps.get(key)
            if cop > tmp:
                maps[key] = data[1:]
            else:
                pass
        else:
            maps[key] = data[1:]
    return maps

NOUNLIST = "NounMap.list"
maps = readNounList(NOUNLIST)
def getCountable(head):
    if head.type.startswith('NNP') and ('-' in head.type):
        if maps.has_key(head.string):
            return maps[head.string][2:]
        elif maps.has_key(head.lemma):
            return maps[head.lemma][2:]
        else:
            return None
    else:
        if maps.has_key(head.lemma):
            return maps[head.lemma][2:]
        else:
            return None

def getNN(chunk):
    return filter(lambda item:item.type.startswith('NN'), chunk.words)

def getNNFeatures(sentence, noun):
    index = noun.index
    b = ['NA', 'NA', 'NA', 'NA']
    a = ['NA', 'NA', 'NA', 'NA']
    words = sentence.words
    for i in range(4):
        if index + 1 + i > len(words) - 1:
            a[i] = ['NA','NA']
        else:
            a[i] = [words[index + 1 + i].string, words[index + 1 + i].type]
        if index - i - 1 < 0:
            b[i] = ['NA','NA']
        else:
            b[i] = [words[index - 1 - i].string, words[index - 1 - i].type]
    return b, a

def getNounFeatures(noun):
    index = noun.index
    pos = noun.type
    
def getWordNet(head, pos=NOUN):
    s = wordnet.synsets(head.string.lower())
    if len(s) != 0:
        a = s[0].lexname.replace("noun.", "")
        if a == None:
            return "NA"
        return a
    else:
        return "NA"

def getCount(noun):
    if noun.type.startswith('NNS'):
        return 'P'
    else: return 'S'

def getChunkFeatures(chunk):
    relation = chunk.role
    if relation == None:
        relation = "NA"
    pdt = "N"
    prp = "N"
    adj = "NA"
    adj_grade = "NA"
    article = "NA"
    for w in chunk.words:
        if w.type == 'JJ':
            adj = w.lemma
            adj_grade = 'N'
        elif w.type == 'JJR':
            adj = w.lemma
            adj_grade = 'C'
        elif w.type == 'JJS':
            adj = w.lemma
            adj_grade = 'S'
        elif w.type == 'PDT':
            pdt = "Y"
        elif w.type == 'PRP$':
            prp = "Y"
        elif w.type == 'DT':
            article = w.string.lower()
    return adj, adj_grade, pdt, prp, relation, article

def getWordNet(head):
    s = wordnet.synsets(head.lemma)
    if len(s) > 0:
        a = s[0].lexname
        if a == None:
            return "O"
        return a.replace("noun.", "")
    else:
        return "O"

def getFeatures(data, outputfile):
    f = open(output_file, "w")
    s = parsetree(data, relations=True, lemmata=True, tagset = None)
    for sentence in s:
        for chunk in sentence.chunks:
            if chunk.type == 'NP':
                nouns = getNN(chunk)
                for noun in nouns:
                    count = getCount(noun) #count equals to 1 means singular, otherwise plural
                    nounType = getCountable(noun)
                    if nounType == None:
                        continue
                    if nounType[0] == 'N' and nounType[1] == 'Y':
                        continue
                    #print getNNFeatures(sentence, noun)
                    bef,aft = getNNFeatures(sentence, noun)
                    bef_word = map(lambda x:x[0], bef)
                    bef_pos = map(lambda x:x[1], bef)
                    aft_word = map(lambda x:x[0], aft)
                    aft_pos = map(lambda x:x[1], aft)
                    role = chunk.role
                    lemma = noun.lemma
                    adj, adj_grade, pdt, prp, relation, article = getChunkFeatures(chunk)
                    wordnet = getWordNet(noun)

                    #features
                    feature = []
                    feature.append(count)
                    feature.append(article)
                    feature.append(noun.lemma)
                    feature.append(wordnet)
                    feature.append(adj)
                    feature.append(adj_grade)
                    feature.append(pdt)
                    feature.append(prp)
                    feature.append(relation)
                    feature.extend(nounType)
                    feature.extend(bef_word)
                    feature.extend(bef_pos)
                    feature.extend(aft_word)
                    feature.extend(aft_pos)

                    features = "\t".join(feature)
                    f.write(features + "\n")
    f.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print 'Usage:input_file output_file'
        exit(-1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    print input_file, output_file
    
    data = ""
    for line in open(input_file, "r"):
        data = data + line.strip() + "\n"

    getFeatures(data, output_file)