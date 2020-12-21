#! /usr/bin/env python3

from collections import deque

import csv
import argparse
import re


class WordNode:
    def __init__(self, gene, remainder):
        self.gene = gene
        self.remainder = remainder
        self.follow = list()

    def __repr__(self):
        return str(self.gene)


def walk_word(word_root: WordNode):
    spellings = set()
    stack = deque()
    stack.append((word_root, ""))
    while stack:
        curr, path = stack.pop()
        path += str(curr)
        if not curr.follow:
            spellings.add(path)

        for follow in curr.follow:
            stack.append((follow, path))

    return spellings


class Neme:
    def __init__(self, name, starts: set = None, middles: set = None, ends: set = None):
        self.name: str = name
        self.starts = starts if starts else set()
        self.middles = middles if middles else set()
        self.ends = ends if ends else set()

    def __repr__(self):
        return self.name

    def __len__(self):
        return len(self.name)


class Phoneme(Neme):
    all_phonemes = dict()

    def __init__(self, name, number, starts: set = None, middles: set = None, ends: set = None):
        self.number = number
        graphs = {
            'starts': set(),
            'middles': set(),
            'ends': set(),
        }

        seeds = {
            'starts': starts,
            'middles': middles,
            'ends': ends,
        }

        for gtype, seed_list in seeds.items():
            for graph in seed_list:
                graph_obj = Graphemes.all_graphemes[graph] if graph in Graphemes.all_graphemes else Graphemes(graph)
                g_association = getattr(graph_obj, gtype)
                g_association.add(self)
                setattr(graph_obj, gtype, g_association)
                graphs[gtype].add(graph_obj)

        super().__init__(name, **graphs)

        Phoneme.all_phonemes[self.name] = self

    def __hash__(self):
        return self.number


class Graphemes(Neme):
    all_graphemes = dict()

    def __init__(self, name):
        super().__init__(name)

        self.phonemes = list()

        Graphemes.all_graphemes[self.name] = self

    def __hash__(self):
        return hash(self.name)


def parse_args():
    """
    Parse command line arguments to a global variable.

    Returns
    -------
    args
        Parsed arguments object from argparse
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-p',
        '--phonemes',
        default='phonemes.csv',
        help='CSV containing the phonemes and graphemes for the language.'
    )

    parser.add_argument(
        '-i',
        '--input',
        default='dict.txt',
        help='Text file containing one word per line to spellinate.'
    )

    args = parser.parse_args()

    return args


def uncsv(string):
    if string:
        clean_set = set("".join(string.split()).split(','))
    else:
        clean_set = set()

    return clean_set


def generate_nemes(neme_file):
    # Quickly read the file in so we can close the filehandle asap
    csv_readin = list()
    with open(neme_file) as csvfile:
        reader = csv.reader(csvfile)
        for idx, row in enumerate(reader):
            name: str
            anywhere: str
            start: str
            middle: str
            end: str
            name, anywhere, start, middle, end = row

            anywhere_set = uncsv(anywhere)
            start_set = uncsv(start)
            middle_set = uncsv(middle)
            end_set = uncsv(end)

            csv_readin.append((idx, name, anywhere_set, start_set, middle_set, end_set))

    # Now work directly off the read-in data
    known_phonemes = dict()

    for number, name, anywhere_set, start_set, middle_set, end_set in csv_readin:
        start_set = anywhere_set | start_set
        middle_set = anywhere_set | middle_set
        end_set = anywhere_set | end_set
        # Create a Phoneme object, which will seed the list
        phone = Phoneme(
            name=name,
            number=number,
            starts=start_set,
            middles=middle_set,
            ends=end_set,
        )
        known_phonemes[number] = phone

    return known_phonemes


def transcribe(word: str, genes: list):
    results = []

    starting_genes = set((gene for gene in genes if gene.starts))
    middling_genes = set((gene for gene in genes if gene.middles))
    ending_genes = set((gene for gene in genes if gene.ends))

    word_list = []

    for sg in starting_genes:
        if word == str(sg):
            for amino in sg.starts:
                results.append(WordNode(amino, None))
        if word.startswith(str(sg)):
            for amino in sg.starts:
                word_node = WordNode(amino, word.replace(str(sg), '', 1))
                # Add to working list
                word_list.append(word_node)
                # Add to results list
                results.append(word_node)

    while word_list:
        # print(f'Working on: {word_list}')
        new_word_list = []
        for word_node in word_list:
            remaining_word = word_node.remainder
            # print(f'{word_node} : {remaining_word}')
            # See if we can finish the word
            for eg in ending_genes:
                new_remainder = remaining_word.replace(str(eg), '', 1)
                if remaining_word.endswith(str(eg)) and len(new_remainder) == 0:
                    # print(f'Finished with {str(eg)}')
                    for amino in eg.ends:
                        word_node.follow.append(WordNode(amino, None))

            for mg in middling_genes:
                new_remainder = remaining_word.replace(str(mg), '', 1)
                if remaining_word.startswith(str(mg)) and len(new_remainder) > 0:
                    # print(f'Enqueued {str(mg)}')
                    for amino in mg.middles:
                        new_word_node = WordNode(amino, new_remainder)
                        word_node.follow.append(new_word_node)
                        new_word_list.append(new_word_node)

        word_list = new_word_list

    return results


def main():
    args = parse_args()

    phonemes = generate_nemes(args.phonemes)

    # phone: Phoneme
    # for phone in phonemes.values():
    #     print(f'{phone.name}')
    #     print(f'    Start: {phone.starts}')
    #     print(f'    Middles: {phone.middles}')
    #     print(f'    Ends: {phone.ends}')
    #     print('='*40)
    #
    # print('\n'+'-'*40+'\n')
    # graph: Graphemes
    # for graph in Graphemes.all_graphemes.values():
    #     print(f'{graph.name}')
    #     print(f'    Start: {graph.starts}')
    #     print(f'    Middles: {graph.middles}')
    #     print(f'    Ends: {graph.ends}')
    #     print('=' * 40)

    word = "arthur"
    transcriptions = transcribe(word, Graphemes.all_graphemes.values())
    phonetic = transcriptions[0]
    print('=====Spellcheck====')
    spell_test = walk_word(phonetic)
    for spelling in spell_test:
        print(spelling)
    phoword = spell_test.pop()
    print('====Phoword====')
    print(phoword)
    phoword = 'ɑ:rθer'
    reverse_transcriptions = transcribe(phoword, Phoneme.all_phonemes.values())
    graphetic = reverse_transcriptions[0]
    print('=====Spellcheck====')
    spell_test = walk_word(graphetic)
    for spelling in spell_test:
        print(spelling)

if __name__ == '__main__':
    main()
