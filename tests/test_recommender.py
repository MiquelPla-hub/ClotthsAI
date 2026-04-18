import pytest
from unittest.mock import MagicMock
from recommender import (
    get_color_group, color_pair_score, style_pair_score,
    score_outfit, get_primary_style, generate_suggestions,
)


def make_item(category, color, style):
    item = MagicMock()
    item.category = category
    item.color_primary = color
    item.style_tags = style
    item.to_dict.return_value = {
        'category': category,
        'color_primary': color,
        'photo_path': 'placeholder.jpg',
        'name': f'{color} {category}',
    }
    return item


def test_get_color_group_neutral():
    assert get_color_group('white') == 'neutral'
    assert get_color_group('black') == 'neutral'
    assert get_color_group('navy') == 'neutral'
    assert get_color_group('grey') == 'neutral'


def test_get_color_group_cool():
    assert get_color_group('blue') == 'cool'
    assert get_color_group('green') == 'cool'


def test_get_color_group_warm():
    assert get_color_group('red') == 'warm'
    assert get_color_group('orange') == 'warm'


def test_get_color_group_unknown_defaults_neutral():
    assert get_color_group('unknown') == 'neutral'


def test_color_pair_score_neutral_with_cool():
    assert color_pair_score('white', 'blue') == 1.0


def test_color_pair_score_neutral_with_warm():
    assert color_pair_score('black', 'red') == 1.0


def test_color_pair_score_neutral_with_earth():
    assert color_pair_score('navy', 'brown') == 1.0


def test_color_pair_score_warm_warm_clashes():
    assert color_pair_score('red', 'orange') == 0.2


def test_color_pair_score_cool_warm_complementary():
    assert color_pair_score('blue', 'orange') == 0.9


def test_color_pair_score_symmetric():
    assert color_pair_score('blue', 'orange') == color_pair_score('orange', 'blue')


def test_style_pair_score_same():
    assert style_pair_score('casual', 'casual') == 1.0
    assert style_pair_score('formal', 'formal') == 1.0


def test_style_pair_score_incompatible():
    assert style_pair_score('formal', 'sporty') == 0.1


def test_style_pair_score_compatible():
    assert style_pair_score('smart-casual', 'formal') == 0.8


def test_style_pair_score_symmetric():
    assert style_pair_score('casual', 'formal') == style_pair_score('formal', 'casual')


def test_score_outfit_all_neutrals_same_style():
    top = make_item('top', 'white', 'casual')
    bottom = make_item('bottom', 'navy', 'casual')
    shoes = make_item('shoes', 'white', 'casual')
    score = score_outfit([top, bottom, shoes])
    assert score >= 0.9


def test_score_outfit_clashing():
    top = make_item('top', 'red', 'formal')
    bottom = make_item('bottom', 'orange', 'sporty')
    shoes = make_item('shoes', 'pink', 'casual')
    score = score_outfit([top, bottom, shoes])
    assert score < 0.5


def test_score_outfit_returns_float_between_0_and_1():
    top = make_item('top', 'blue', 'casual')
    bottom = make_item('bottom', 'black', 'casual')
    shoes = make_item('shoes', 'white', 'casual')
    score = score_outfit([top, bottom, shoes])
    assert 0.0 <= score <= 1.0


def test_generate_suggestions_empty_without_required_categories():
    items = [make_item('top', 'white', 'casual')]
    assert generate_suggestions(items) == []


def test_generate_suggestions_returns_sorted_by_score():
    items = [
        make_item('top', 'white', 'casual'),
        make_item('top', 'red', 'sporty'),
        make_item('bottom', 'navy', 'casual'),
        make_item('shoes', 'white', 'casual'),
    ]
    result = generate_suggestions(items)
    assert len(result) == 2
    assert result[0]['score'] >= result[1]['score']


def test_generate_suggestions_style_filter_excludes_non_matching():
    items = [
        make_item('top', 'white', 'casual'),
        make_item('bottom', 'navy', 'casual'),
        make_item('shoes', 'white', 'casual'),
    ]
    result = generate_suggestions(items, style_filter='formal')
    assert result == []


def test_generate_suggestions_all_filter_returns_all():
    items = [
        make_item('top', 'white', 'casual'),
        make_item('bottom', 'navy', 'casual'),
        make_item('shoes', 'white', 'casual'),
    ]
    result = generate_suggestions(items, style_filter='all')
    assert len(result) == 1


def test_generate_suggestions_limit():
    items = [
        make_item('top', 'white', 'casual'),
        make_item('top', 'grey', 'casual'),
        make_item('top', 'navy', 'casual'),
        make_item('bottom', 'black', 'casual'),
        make_item('shoes', 'white', 'casual'),
    ]
    result = generate_suggestions(items, limit=2)
    assert len(result) == 2
