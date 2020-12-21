#! /usr/bin/env python3
# coding=utf-8

from collections import deque
from pprint import pprint

import csv
import argparse
import re
import math

_debug = True

def list_columns(obj, cols=4, columnwise=True, gap=4):
    """
    Print the given list in evenly-spaced columns.

    Parameters
    ----------
    obj : list
        The list to be printed.
    cols : int
        The number of columns in which the list should be printed.
    columnwise : bool, default=True
        If True, the items in the list will be printed column-wise.
        If False the items in the list will be printed row-wise.
    gap : int
        The number of spaces that should separate the longest column
        item/s from the next column. This is the effective spacing
        between columns based on the maximum len() of the list items.
    """

    sobj = [str(item) for item in obj]
    if cols > len(sobj): cols = len(sobj)
    max_len = max([len(item) for item in sobj])
    if columnwise: cols = int(math.ceil(float(len(sobj)) / float(cols)))
    plist = [sobj[i: i+cols] for i in range(0, len(sobj), cols)]
    if columnwise:
        if not len(plist[-1]) == cols:
            plist[-1].extend(['']*(len(sobj) - len(plist[-1])))
        plist = zip(*plist)
    printer = '\n'.join([
        ''.join([c.ljust(max_len + gap) for c in p])
        for p in plist])
    print(printer)


class SequenceNode:
    def __init__(self, gene, remainder):
        self.gene = gene
        self.remainder = remainder
        self.follow = list()

    def __repr__(self):
        return str(self.gene)


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

    def __init__(self, name, number, phoneme_dict: dict, grapheme_dict: dict,
                 starts: set = None, middles: set = None, ends: set = None):
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
                graph_obj = grapheme_dict[graph] if graph in grapheme_dict else Graphemes(graph, grapheme_dict)
                g_association = getattr(graph_obj, gtype)
                g_association.add(self)
                setattr(graph_obj, gtype, g_association)
                graphs[gtype].add(graph_obj)

        super().__init__(name, **graphs)

        phoneme_dict[self.name] = self

    def __hash__(self):
        return self.number


class Graphemes(Neme):

    def __init__(self, name, grapheme_dict: dict):
        super().__init__(name)

        self.phonemes = list()

        grapheme_dict[self.name] = self

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

    parser.add_argument(
        '-c',
        '--categories',
        default='categories.csv',
        help='CSV containing graph categories, used to apply weights to output graphs'
    )

    parser.add_argument(
        '-w',
        '--weights',
        default='weights.csv',
        help='CSV containing weights for graphemes/categories.'
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
    phoneme_dict = dict()
    grapheme_dict = dict()

    for number, name, anywhere_set, start_set, middle_set, end_set in csv_readin:
        start_set = anywhere_set | start_set
        middle_set = anywhere_set | middle_set
        end_set = anywhere_set | end_set
        # Create a Phoneme object, which will seed the list
        phone = Phoneme(
            name=name,
            number=number,
            phoneme_dict=phoneme_dict,
            grapheme_dict=grapheme_dict,
            starts=start_set,
            middles=middle_set,
            ends=end_set,
        )

    return phoneme_dict, grapheme_dict


def reverse_translate(rna: str, genes: list):
    results = []

    starting_genes = set((gene for gene in genes if gene.starts))
    middling_genes = set((gene for gene in genes if gene.middles))
    ending_genes = set((gene for gene in genes if gene.ends))

    word_list = []

    for sg in starting_genes:
        if rna == str(sg):
            for amino in sg.starts:
                results.append(SequenceNode(amino, None))
        if rna.startswith(str(sg)):
            for amino in sg.starts:
                word_node = SequenceNode(amino, rna.replace(str(sg), '', 1))
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
                        word_node.follow.append(SequenceNode(amino, None))

            for mg in middling_genes:
                new_remainder = remaining_word.replace(str(mg), '', 1)
                if remaining_word.startswith(str(mg)) and len(new_remainder) > 0:
                    # print(f'Enqueued {str(mg)}')
                    for amino in mg.middles:
                        new_word_node = SequenceNode(amino, new_remainder)
                        word_node.follow.append(new_word_node)
                        new_word_list.append(new_word_node)

        word_list = new_word_list

    return results


def translate(start_codon: SequenceNode):
    spellings = set()
    stack = deque()
    stack.append((start_codon, ""))
    while stack:
        curr, path = stack.pop()
        path += str(curr)
        if not curr.follow:
            spellings.add(path)

        for follow in curr.follow:
            stack.append((follow, path))

    return spellings


def transcribe(start_codon: SequenceNode):
    proteins = list()
    stack = deque()
    for start in start_codon.gene.starts:
        for follow in start_codon.follow:
            stack.append((follow, [start], [start_codon]))

    while stack:
        curr: SequenceNode
        curr, path, gene = stack.pop()

        if not curr.follow:
            for end in curr.gene.ends:
                new_path = path[:]
                new_path.append(end)
                new_gene = gene[:]
                new_gene.append(curr)
                proteins.append((new_path, new_gene))
                # if _debug:
                #     print(new_path)

        for follow in curr.follow:
            for middle in curr.gene.middles:
                new_path = path[:]
                new_path.append(middle)
                new_gene = gene[:]
                new_gene.append(curr)
                stack.append((follow, new_path, new_gene))

    return proteins


def main():
    args = parse_args()

    phoneme_dict, grapheme_dict = generate_nemes(args.phonemes)

    # phone: phoneme
    # for phone in phonemes.values():
    #     print(f'{phone.name}')
    #     print(f'    start: {phone.starts}')
    #     print(f'    middles: {phone.middles}')
    #     print(f'    ends: {phone.ends}')
    #     print('='*40)
    #
    # print('\n'+'-'*40+'\n')
    # graph: graphemes
    # for graph in graphemes.all_graphemes.values():
    #     print(f'{graph.name}')
    #     print(f'    start: {graph.starts}')
    #     print(f'    middles: {graph.middles}')
    #     print(f'    ends: {graph.ends}')
    #     print('=' * 40)

    word = "arthur"
    # Take the word and generate ways it could be pronounced, as a set of trees
    phonetic_sequence = reverse_translate(word, grapheme_dict.values())

    plist_full = []
    # For each way-tree of how it could be pronounced
    for pseq in phonetic_sequence:
        glist_full = []
        # Write out the possible phonetics
        phonetic_list = translate(pseq)
        plist_full.extend(phonetic_list)
        list_columns(phonetic_list, 8, True, 2)
        # Generate ways to write the sound-tree
        graphic_sequence = transcribe(pseq)
        glist_full.extend((''.join(map(str, seq[1])) + ' -> ' + ''.join(map(str, seq[0])) for seq in graphic_sequence))
        list_columns(glist_full, 6, True, 2)

    # list_columns(plist_full, 8, True, 2)




    # print(grapheme_dict.keys())
    # print(phoneme_dict.keys())

    # print('=====spellcheck====')
    # spell_test = translate(phonetic)
    # for spelling in spell_test:
    #     print(spelling)
    # phoword = spell_test.pop()
    # print('====phoword====')
    # print(phoword)
    # phoword = 'ɑ:rθer'
    # reverse_transcriptions = reverse_translate(phoword, Phoneme.all_phonemes.values())
    # graphetic = reverse_transcriptions[0]
    # print('=====spellcheck====')
    # spell_test = translate(graphetic)
    # for spelling in spell_test:
    #     print(spelling)

if __name__ == '__main__':
    main()
