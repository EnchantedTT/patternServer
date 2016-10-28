from nltk.corpus import cmudict
from pattern.en import parse, parsetree, wordnet, NOUN

def getHeadFeatures(chunk):
    head = None
    word = str(chunk.words[-1].type)
    if word.startswith('NN'):
        head = chunk.words[-1]
    else:
        head = chunk.head
    if head == None:
        return None, None
    pos = str(head.type)
    isPlural = 'S'
    if pos.startswith('NNPS') or pos.startswith('NNS'):
        isPlural = 'P'
    return head, isPlural