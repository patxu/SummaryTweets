from collections import defaultdict, Counter
import argparse
import math
import os
import re
import collections
#import nltk
import pickle
import sys

class tfidf:
	def __init__(self, corpusDirectory):
		"""reads corpus files and adds it to allCorpora"""
		allCorpora = open('pickl/allCorpora')
		allPoSCorpora = open('pickl/allPoSCorpora')

		allPhrases = open('pickl/allPhrases')

		self.allCorpora = pickle.load(allCorpora) #will be a dictionary pointing to the corpus file, each of which is a dictionary of the all the word counts.
		self.allPoSCorpora = pickle.load(allPoSCorpora)
		self.allPhrases = pickle.load(allPhrases)

		allCorpora.close()
		allPoSCorpora.close()
		allPhrases.close()
	
	def getInputText(self, filename):
		"""returns the text within a file for summarizing"""
		try:
			myfile = open(filename, 'r')
			text = ''
			for line in myfile:
				text = text + line
			return text
		except IOError:
			print 'ERROR: Invalid filename'
			return False

	def wordDictionary(self, filename): #deprecated 
		"""returns the file as a dictionary with word counts"""
		wordCount = defaultdict(int)
		words = open(str(filename)).readlines()
		for line in words:
			"""insert a function to clean up lines"""
			line = line.split()
			for word in line:
				wordCount[word] +=1
		if '-' in wordCount:
			print '- in the dictionary'
		else: print '- not in dictionary'
		self.allCorpora[filename] = wordCount #adds the corpus to the corpora dictionary
	
	def taggedWordDictionary(self, filename):
		wordCount = defaultdict(int)
		tagCount = defaultdict(int)
		words = open(str(filename)).readlines()
		for line in words:
			"""insert a function to clean up lines"""
			line = line.split()
			for word in line:
				m = re.match(r"(?P<word>[\w.,!?()-]+)(\/)(?P<tag>[\w.,!?()-]+)", word) 
				if m != None:
					#print m.group('word'), m.group('tag')
					wordCount[m.group('word').lower()] +=1
					tagCount[m.group('tag').lower()] +=1
					#self.testWhatPOS.add(m.group('tag'))
		self.allCorpora[filename] = wordCount #adds the corpus to the corpora dictionary
		self.allPoSCorpora[filename] = tagCount #adds the corpus to the corpora dictionary


	def tf_idf(self, inputText):
		"""returns a tf-idf dictionary for each term in inputText"""

		tfidfDict = {}
		#create a word Dictionary for the input text
		inputWordDictionary = defaultdict(int)
		# inputText = re.sub('([.,!?()])', r' \1 ', inputText) #regex code to add a space between punctuation
		inputText = inputText.split()
		for w in inputText:
			word = w.strip("'.,!?;:'*()")
			inputWordDictionary[word] +=1

		# term frequency * log (# files total / # files with term)
		for w in inputText:
			#print "\n",word
			word = w.strip("'.,!?;:'*()")

			tf = inputWordDictionary[word]
			#print "tf", tf
			numfiles = 0
			for corpus in self.allCorpora:
				if word in self.allCorpora[corpus]:
					numfiles +=1
			if numfiles ==0: #if the word isn't in any of the corpora
				numfiles = .1 #assume it is important -- might change that later: the word is either important or mispelled 
			idf = math.log((len(self.allCorpora)/(numfiles)))

			tfidf = tf * idf
			#print 'tf', tf, "| idf", idf

			tfidfDict[word] = tfidf
		return tfidfDict

	def topSentences(self, inputText, scores):
		"""returns the top Sentences by taking the top 10 percent of words"""
		inputText = re.sub('([.,!?()])', r' \1 ', inputText)
		sentences = re.split('(?<=[.!?-]) +', inputText)
		sentenceList = []

		numWords = int(math.ceil(float(len(scores))/10)) #sets numWords to be the top 10 percent of words
		words = [] #a list of the top words
		for i in range(0, numWords):
			maxWord = max(scores.iterkeys(), key=lambda key: scores[key]) 
			# print maxWord
			k= scores.pop(maxWord)
			words.append((maxWord, k)) 

		#print sorted(words, key=lambda key: words[i])
		for word, val in words:
			for sentence in sentences: 
				wordList = sentence.split()
				if word in wordList and sentence not in sentenceList: #if the word is in the sentence and the sentence is not already in the list
						sentenceList.append(sentence)
		for sentence in sentenceList:
			tokenized = sentence.split()
			tags = nltk.pos_tag(tokenized)
			#print tags

		return sentenceList
		#max(stats.iteritems(), key=operator.itemgetter(1))[0]

	def total_sent_score(self, inputText, scores):

		"""Compute the total tf-idf score of a sentence by summing the scores of each word in each sentence"""
		# inputText = re.sub('([.,!?()])', r' \1 ', inputText) #I took these two lines from topSentences
		#print "\nThe input text is:\n", inputText, "\n"
		sentences = re.split('(?<=[.!?-]) +', inputText)

		#top_sentences = Counter()
		top_sentences = []

		for index, sentence in enumerate(sentences):
			words = sentence.split()
			total_score = 0.0
			num_words = 0.0
			word_list = []
			if len(sentence) > 1: #to avoid single punctuation marks or one-word sentences.
				for w in words:
					if len(w) > 1: #to avoid single punctuation marks.
						word = w.strip("'.,!?;:'*()")
						num_words += 1
						score = scores[word]
						total_score += score
						word_list.append((word, score))

				#if num_words != 0: top_sentences[sentence] = (total_score / num_words, index)
				#if num_words != 0: top_sentences.append((sentence, total_score / num_words, index))
				if num_words != 0: top_sentences.append((word_list, total_score / num_words, index))
				# top_sentences[sentence] = total_score

		"""returns all the sentences with a score and index"""
		return top_sentences 
		#return top_sentences.most_common(num_sentences)

	def compress_sentences(self, sentences_in_lists, out_length):
		"""compresses and returns the sentences within our desired length"""
		sentences = []
		
		"""compression"""
		for sent_list in sentences_in_lists:
			max_changes = len(sent_list[0])/2 #the greatest number of changes we want to make
			bigrams = []
			first = ('', 0)
			second = ('', 0)
			for index, word in enumerate(sent_list[0]):
				first = second
				second = word
				if first[0] == '': continue# or second[0] == '.': continue
				bigrams.append((first[0] + ' ' + second[0], first[1]+second[1], index))
			bigrams.sort(key = lambda x:x[1])
			changes = 0
			new_sent = []
			for bigram in bigrams:
				if changes > max_changes: break
				if self.allPhrases.has_key(bigram[0]):
					#print 'changing', bigram[0], '>>>', self.allPhrases[bigram[0]]
					bigram = (self.allPhrases[bigram[0]], bigram[1], bigram[2])

			seen = [] #list of indices of bigrams changed

			for bigram in bigrams:
				if changes > max_changes: break
				if bigram[0] in self.allPhrases:
					#print 'changing', bigram[0], '>>>', self.allPhrases[bigram[0]]
					bigram = (self.allPhrases[bigram[0]], bigram[1], bigram[2])
					seen.append(bigram[2]) #remember that this bigram was changed
					changes += 1
				new_sent.append(bigram)

			new_sent.sort(key = lambda x:x[2])
			#print new_sent
			sentence = ''
			for i in new_sent:

				if i[2]-1 in seen and not i[2] in seen: continue
				word = i[0].split()
				sentence += word[0] + ' '
			try:
				sentence += new_sent[len(new_sent)-1][0].split()[1]
			except IndexError:
				sentence += '.'
			sentence += '.'

			sentences.append((sentence, sent_list[1], sent_list[2]))

		"""ordering, printing to correct length"""
		output = []
		total_length = 0
		sentences.sort(key = lambda x:x[1], reverse = True)

		for sentence in sentences:
			length = len(sentence[0]) + 1 #+1 for space before sentences
			if total_length + length > out_length:
				break
			total_length += length

			"""insert sentences in the correct order"""
			counter = 0
			for i in range(len(output)): 
				if output[i][2] < sentence[2]:
					counter += 1
			output.insert(counter, sentence)

		"""create the output string"""
		out_string = ''
		for i in output:
			out_string += i[0] + ' '
		return out_string

if __name__=='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', type=str, help='corpus', required=False)
	parser.add_argument('-text', type=str, help='input text', required=True)
	parser.add_argument('-tagged', type=str, help='boolean if corpus is tagged', required=False, default=False)
	parser.add_argument('-textfile', type=str, help='boolean if given input file', required=False)
	parser.add_argument('-length', type=str, help='length of final compression', required=False, default=135) #135 to make room for #CS73 hashtag
	args = parser.parse_args()

	if args.text is None and args.textfile is None:
		print "Either command line text or a text file is required!"
		sys.exit() 

	print "Parsing Corpus..."
	program = tfidf(args.c)
	if args.textfile != None:
		print 'Opening Input Text File...'
		text = program.getInputText(args.textfile)
		args.text = text
		if text == False:
			sys.exit() #stops program
	print "Calculating Score..."

	args.text = args.text.lower() #added to make lowercase

	scores = program.tf_idf(args.text)
	# print scores
	# print'\n'

	#summary = program.topSentences(args.text, scores)
	summary2 = program.total_sent_score(args.text, scores)
	#print summary
<<<<<<< HEAD
	print summary2
	shortened = program.replace_phrases(summary2, scores)
	#output = program.compress_sentences(summary2, args.length)
	#print output
=======
	#print summary2
	output = program.compress_sentences(summary2, args.length)
	print 'The output is'
	print output
	print 'The output text is:'
	print output
>>>>>>> d8671cb5906dcfd04445331b032977365c44d7d1
