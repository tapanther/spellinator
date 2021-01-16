#! /usr/bin/env python3
# coding=utf-8

from collections import deque
from pprint import pprint
from time import sleep

import csv
import argparse
import re
import math
import yaml
import random

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
    plist = [sobj[i: i + cols] for i in range(0, len(sobj), cols)]
    if columnwise:
        if not len(plist[-1]) == cols:
            plist[-1].extend([''] * (len(sobj) - len(plist[-1])))
        plist = zip(*plist)
    printer = '\n'.join([
        ''.join([c.ljust(max_len + gap) for c in p])
        for p in plist])
    print(printer)


class SequenceNode:
    target_length = 1

    def __init__(self, gene, remainder, stop_valid: bool = None):
        self.gene = gene
        self.remainder: str = remainder
        self.follow = list()
        self.stop_valid: bool = stop_valid if stop_valid else False
        self.corruption: float = 1.0

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
    gene_type = 'phoneme'

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
    gene_type = 'grapheme'

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
        '-m',
        '--phoneme-map',
        help='Optional output phoneme map for transliterations.'
    )

    parser.add_argument(
        'input',
        nargs='?',
        default='arthur',
        help='Word to spellinate.'
    )

    parser.add_argument(
        '-a',
        '--allow-homographs',
        action='store_true',
        help='Allow homographs that have different pronunciations.'
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

    parser.add_argument(
        '-g',
        '--graph-threshold',
        default=0.25,
        type=float,
        help='Threshold to disallow graph based on weights.'
    )

    parser.add_argument(
        '-l',
        '--length-threshold',
        default=1.10,
        type=float,
        help='Threshold to disallow graph based on length. Values greater than 1.0 allow outputs longer than the '
             'original word by (<threshold> - 1.0) * 100 %%.'
    )

    parser.add_argument(
        '-s',
        '--stack-limit',
        default=1000,
        type=int,
        help='Maximum size of build stack for graph generation. Larger values allow for more results '
             'but also take exponentially longer.'
    )

    args = parser.parse_args()

    return args


def uncsv(string):
    if string:
        clean_set = set("".join(string.split()).split(','))
    else:
        clean_set = set()

    return clean_set


def generate_weights(weight_file):
    weight_dict = dict()
    with open(weight_file) as csvfile:
        reader = csv.reader(csvfile)
        for idx, row in enumerate(reader):
            weight: str
            anywhere: str
            weight, anywhere = row

            weight_val = float(weight)
            anywhere_set = uncsv(anywhere)

            weight_dict[weight_val] = anywhere_set

    return weight_dict


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

    print(f'Generated {len(phoneme_dict)} phonemes and {len(grapheme_dict)} graphemes.')

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
                results.append(SequenceNode(amino, None, True))
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
                        new_word_node = SequenceNode(amino, None, True)
                        word_node.follow.append(new_word_node)

            for mg in middling_genes:
                new_remainder = remaining_word.replace(str(mg), '', 1)
                if remaining_word.startswith(str(mg)) and len(new_remainder) > 0:
                    # print(f'Enqueued {str(mg)}')
                    for amino in mg.middles:
                        new_word_node = SequenceNode(amino, new_remainder)
                        word_node.follow.append(new_word_node)
                        new_word_list.append(new_word_node)

        print(f'Generated {len(results)} {word_list[0].gene.gene_type} patterns so far...', end='\r', flush=True)
        word_list = new_word_list

    print('')
    return results


def translate(start_codon: SequenceNode, weight_dict: dict = None, threshold=0.25):
    proteins = set()
    chains = deque()
    chains.append((start_codon, ""))
    while chains:
        curr: SequenceNode
        path: str
        curr, path = chains.pop()
        path += str(curr)
        # Only allow valid spellings
        if not curr.follow and curr.stop_valid:
            path_weight = 1.0
            if weight_dict:
                for weight_set in sorted(weight_dict.items()):
                    for seq in weight_set[1]:
                        if seq in path:
                            path_weight *= weight_set[0]
            if path_weight > threshold:
                proteins.add(path)

        for follow in curr.follow:
            chains.append((follow, path))

    return proteins


def transcribe(start_codon: SequenceNode, mapping_dict: dict, weight_dict=None,
               allow_homographs: bool = False,
               graph_threshold: float = 0.25, length_threshold: float = 1.10,
               stack_limit: int = 1000):
    rejections = 0
    m_rna = set()
    stack = set()
    stack_limited = False
    starts = tuple(mapping_dict[str(start_codon)].starts)
    for start in random.sample(starts, len(starts)):
        for follow in random.sample(start_codon.follow, len(start_codon.follow)):
            # (new roots, translation, source)
            stack.add((follow, (start,), (start_codon,)))

    while stack:
        curr: SequenceNode
        curr, anticodon, codon = stack.pop()

        if not curr.follow and curr.stop_valid:
            ends = tuple(mapping_dict[str(curr)].ends)
            for end in random.sample(ends, len(ends)):
                new_anticodon = anticodon + (end,)
                new_codon = codon + (curr,)
                add_tuple = (new_anticodon, new_codon) if allow_homographs else new_anticodon
                m_rna.add(add_tuple)
                # if _debug:
                #     print(new_path)

        for follow in random.sample(curr.follow, len(curr.follow)):
            middles = tuple(mapping_dict[str(curr)].middles)
            for middle in random.sample(middles, len(middles)):
                new_anticodon = anticodon + (middle,)
                if (sum(map(len, new_anticodon)) / SequenceNode.target_length) > length_threshold:
                    rejections += 1
                    continue
                graphic = "".join(map(str, new_anticodon[-3:]))
                graph_weight = 1.0
                if weight_dict:
                    for weight_set in sorted(weight_dict.items()):
                        for wseq in weight_set[1]:
                            if wseq in graphic:
                                count = graphic.count(wseq)
                                graph_weight *= weight_set[0] ** count

                if graph_weight >= graph_threshold:
                    new_codon = codon + (curr,)
                    # Limit the stack length
                    if len(stack) < stack_limit:
                        stack.add((follow, new_anticodon, new_codon))
                    else:
                        stack_limited = True
                else:
                    rejections += 1

        print(f'Generated {len(m_rna)} patterns, rejected {rejections}, stack limit {stack_limited}',
              end='\r', flush=True)

    print('')
    return m_rna


def true_translate(phonetic_sequences: list, phoneme_dict: dict, weight_dict: dict = None,
                   allow_homographs: bool = False,
                   graph_threshold: float = 0.25, length_threshold: float = 1.10, stack_limit: int = 1000):
    plist_full = set()
    glist_full = set()
    wrap_pattern = re.compile(r'\.(\S+) ?(\S*)')
    # For each way-tree of how it could be pronounced
    for pseq in phonetic_sequences:
        # Write out the possible phonetics
        phonetic_list = translate(pseq)
        plist_full.union(phonetic_list)
        # list_columns(phonetic_list, 8, True, 2)
        # Generate ways to write the sound-tree
        graphic_sequence = transcribe(pseq, phoneme_dict, weight_dict,
                                      allow_homographs,
                                      graph_threshold, length_threshold, stack_limit)
        for seq in graphic_sequence:
            if allow_homographs:
                phonetic = ''.join(map(str, seq[1]))
                graphic_i = ' '.join(map(str, seq[0]))
            else:
                graphic_i = ' '.join(map(str, seq))
            graphic_o = re.sub(wrap_pattern, r'\2\1', graphic_i)
            graphic = ''.join(graphic_o.split())
            graph_weight = 1.0
            if weight_dict:
                for weight_set in sorted(weight_dict.items()):
                    for wseq in weight_set[1]:
                        if wseq in graphic:
                            count = graphic.count(wseq)
                            graph_weight *= weight_set[0] ** count

            if graph_weight >= graph_threshold:
                if allow_homographs:
                    glist_full.add(f'{phonetic:<{SequenceNode.target_length+2}}' + ' -> ' + graphic)
                else:
                    glist_full.add(graphic)
            # else:
            #     print(f'Rejected: {graphic}')

    return glist_full, plist_full


def main():
    args = parse_args()

    weight_dict = generate_weights(args.weights)

    # pprint(weight_dict)
    # raise NotImplementedError

    phoneme_dict, grapheme_dict = generate_nemes(args.phonemes)

    # pydict = dict()
    # for phon in phoneme_dict.values():
    #     pydict[str(phon)] = {
    #         'starts': list(map(str, phon.starts)),
    #         'middles': list(map(str, phon.middles)),
    #         'ends': list(map(str, phon.ends)),
    #     }
    #
    # with open('phonemes.yml', 'w') as yfile:
    #     yaml.dump(pydict, yfile, allow_unicode=True, sort_keys=False)

    if args.phoneme_map:
        mapped_phoneme_dict, mapped_grapheme_dict = generate_nemes(args.phoneme_map)
    else:
        mapped_phoneme_dict, mapped_grapheme_dict = phoneme_dict, grapheme_dict

    # print(grapheme_dict.keys())
    # print(phoneme_dict.keys())
    #
    # print(mapped_grapheme_dict.keys())
    # print(mapped_phoneme_dict.keys())
    #
    # raise NotImplementedError

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

    # Single word input, toss extra words, lowercase only.
    word = args.input.split()[0].lower()
    SequenceNode.target_length = len(word)
    # Take the word and generate ways it could be pronounced, as a set of trees
    phonetic_sequences = reverse_translate(word, grapheme_dict.values())

    print(f'Generated a total of {len(phonetic_sequences)} sequence starts.', flush=True)

    glist_full, plist_full = true_translate(phonetic_sequences=phonetic_sequences,
                                            phoneme_dict=mapped_phoneme_dict,
                                            allow_homographs=args.allow_homographs,
                                            weight_dict=weight_dict,
                                            graph_threshold=args.graph_threshold,
                                            length_threshold=args.length_threshold,
                                            stack_limit=args.stack_limit)

    if args.allow_homographs:
        columns = 100 // ((2.0 * args.length_threshold) * SequenceNode.target_length + 10)
    else:
        columns = 100 // (SequenceNode.target_length * args.length_threshold + 10)

    list_columns(glist_full, columns, True, 6)

    # list_columns(plist_full, 8, True, 2)

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
