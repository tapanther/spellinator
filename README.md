# spellinator

Have you ever wondered how words _could have_ been spelled using different letter combinations for the same sounds? Well wonder no longer! With the Spellinator,
you can find out! 

The program takes a phoneme (sound units) to graphemes (writing units) map to phonetically map a word into possible _pronunciations_, then reverse map those pronunciations into
possible spellings. An optional second phoneme map allows transliteration into a different alphabet, and a grapheme weights file rejects unlikely output combinations (ex: `rrr`
or `thh` that result from phonetic mappings).

```
√ spellinator [spellinator@main] % ./spellinator.py -h
usage: spellinator.py [-h] [-p PHONEMES] [-m PHONEME_MAP] [-c CATEGORIES] [-w WEIGHTS] [-t THRESHOLD] [input]

positional arguments:
  input                 Word to spellinate.

optional arguments:
  -h, --help            show this help message and exit
  -p PHONEMES, --phonemes PHONEMES
                        CSV containing the phonemes and graphemes for the language.
  -m PHONEME_MAP, --phoneme-map PHONEME_MAP
                        Optional output phoneme map for transliterations.
  -c CATEGORIES, --categories CATEGORIES
                        CSV containing graph categories, used to apply weights to output graphs
  -w WEIGHTS, --weights WEIGHTS
                        CSV containing weights for graphemes/categories.
  -t THRESHOLD, --threshold THRESHOLD
                        Threshold to disallow graph.
```
