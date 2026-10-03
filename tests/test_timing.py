"""Regression tests for reorder mapping, cuts, clipping and caption chronology."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from render import build_pieces
from toolkit import mapped_words
from compose import build_captions
from compose_hf import chunk_captions

class TimingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.job = Path(self.temp.name)
        self.pieces = [
            {'i': 2, 'start': 10.0, 'end': 12.0, 'text': 'Later sentence.'},
            {'i': 1, 'start': 1.0, 'end': 3.0, 'text': 'First sentence.'}]
        self.words = [
            {'seg': 1, 'w': 'First', 'start': 1.2, 'end': 1.5},
            {'seg': 1, 'w': 'sentence.', 'start': 1.6, 'end': 2.0},
            {'seg': 2, 'w': 'Later', 'start': 10.2, 'end': 10.5},
            {'seg': 2, 'w': 'sentence.', 'start': 10.6, 'end': 11.0}]
        self.write()

    def tearDown(self): self.temp.cleanup()

    def write(self):
        for name, value in [('pieces.json', self.pieces), ('words.json', self.words)]:
            (self.job / name).write_text(json.dumps(value), encoding='utf-8')

    def test_reverse_order_maps_to_new_times(self):
        data = mapped_words(self.job)
        self.assertEqual([w['w'] for w in data['words']], ['Later', 'sentence.', 'First', 'sentence.'])
        self.assertAlmostEqual(data['words'][0]['start'], .2)
        self.assertAlmostEqual(data['words'][2]['start'], 2.2)
        self.assertEqual(data['duration'], 4)

    def test_intro_shifts_all_anchors(self):
        data = mapped_words(self.job, 1.5)
        self.assertAlmostEqual(data['words'][0]['start'], 1.7)
        self.assertAlmostEqual(data['words'][2]['start'], 3.7)
        self.assertEqual(data['duration'], 5.5)

    def test_word_clipping_respects_trimmed_piece(self):
        self.words.insert(0, {'seg': 2, 'w': 'Trimmed', 'start': 9, 'end': 10.1})
        self.words.append({'seg': 2, 'w': 'Removed', 'start': 12.1, 'end': 12.3})
        self.write()
        words = mapped_words(self.job)['words']
        self.assertEqual(words[0]['start'], 0)
        self.assertAlmostEqual(words[0]['end'], .1)
        self.assertNotIn('Removed', [w['w'] for w in words])
        for fn in [lambda job: build_captions(job, set()), chunk_captions]:
            groups = fn(self.job)
            self.assertEqual(groups[0]['start'], 0)
            self.assertNotIn('REMOVED', [w.upper() for g in groups for w in g['words']])

    def test_both_caption_styles_are_chronological(self):
        for fn in [lambda job: build_captions(job, set()), chunk_captions]:
            groups = fn(self.job)
            flattened = [w.upper() for g in groups for w in g['words']]
            self.assertEqual(flattened, ['LATER', 'SENTENCE.', 'FIRST', 'SENTENCE.'])
            self.assertAlmostEqual(groups[0]['start'], .2)
            first = next(g for g in groups if g['words'][0].upper() == 'FIRST')
            self.assertAlmostEqual(first['start'], 2.2)
            self.assertTrue(all(g['end'] > g['start'] for g in groups))

    def test_cut_padding_does_not_consume_neighbor_speech(self):
        segs = [{'i': 1, 'start': 1, 'end': 2, 'text': 'one'}, {'i': 2, 'start': 2.1, 'end': 3, 'text': 'two'}]
        pieces = build_pieces(segs, [2, 1], {}, 30, 4)
        self.assertEqual([p['i'] for p in pieces], [2, 1])
        self.assertGreaterEqual(pieces[0]['start'], 2)
        self.assertLessEqual(pieces[1]['end'], 2.1)

    def test_duplicate_or_missing_segment_rejected(self):
        segs = [{'i': 1, 'start': 1, 'end': 2, 'text': 'one'}]
        for order in [[], [1, 1], [3]]:
            with self.assertRaises(ValueError): build_pieces(segs, order, {}, 30, 4)

if __name__ == '__main__': unittest.main()
