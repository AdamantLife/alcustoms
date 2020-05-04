import re, collections

class SpellingCorrector():
    def __init__(self,sourcewords,alphabet='abcdefghijklmnopqrstuvwxyz'):
        self.NWORDS = self.train(self.words(sourcewords))
        self.alphabet = alphabet

    def words(self,text): return re.findall('[a-z]+', text.lower()) 

    def train(self,features,model=None):
        if not model:
            model = collections.defaultdict(lambda: 1)
        for f in features:
            model[f] += 1
        return model

    def updatetraining(self,features):
        self.NWORDS=self.train(features,model=self.NWORDS)
    
    def edits1(self,word):
       splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
       deletes    = [a + b[1:] for a, b in splits if b]
       transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
       replaces   = [a + c + b[1:] for a, b in splits for c in self.alphabet if b]
       inserts    = [a + c + b     for a, b in splits for c in self.alphabet]
       return set(deletes + transposes + replaces + inserts)

    def known_edits2(self,word):
        return set(e2 for e1 in self.edits1(word) for e2 in self.edits1(e1) if e2 in self.NWORDS)

    def known(self,words): return set(w for w in words if w in self.NWORDS)

    def correct(self,word,mode='single'):
        candidates = self.known([word,])\
                     or self.known(self.edits1(word))\
                     or self.known_edits2(word)\
                     or [word]
        if mode=='single': return max(candidates, key=self.NWORDS.get)
        elif mode=='list': return candidates
        else: raise ValueError("Bad Mode; should be 'single','list'")

if __name__=='__main__':
    with open('big.txt') as f:
        file=f.read()
    corr=SpellingCorrector(file)
    print(corr.correct('korrect'))