from itertools import product

COLOR_GROUPS = {
    'white': 'neutral', 'black': 'neutral', 'grey': 'neutral',
    'navy': 'neutral', 'beige': 'neutral', 'tan': 'neutral',
    'blue': 'cool', 'green': 'cool', 'purple': 'cool', 'teal': 'cool',
    'red': 'warm', 'orange': 'warm', 'yellow': 'warm', 'pink': 'warm',
    'brown': 'earth', 'olive': 'earth', 'burgundy': 'earth',
}

GROUP_COMPAT = {
    ('neutral', 'neutral'): 1.0,
    ('cool', 'neutral'): 1.0,
    ('neutral', 'warm'): 1.0,
    ('earth', 'neutral'): 1.0,
    ('cool', 'cool'): 0.7,
    ('cool', 'warm'): 0.9,
    ('cool', 'earth'): 0.8,
    ('warm', 'warm'): 0.2,
    ('earth', 'warm'): 0.7,
    ('earth', 'earth'): 0.8,
}

STYLE_COMPAT = {
    ('casual', 'casual'): 1.0,
    ('casual', 'smart-casual'): 0.7,
    ('casual', 'formal'): 0.2,
    ('casual', 'sporty'): 0.6,
    ('smart-casual', 'smart-casual'): 1.0,
    ('formal', 'smart-casual'): 0.8,
    ('smart-casual', 'sporty'): 0.3,
    ('formal', 'formal'): 1.0,
    ('formal', 'sporty'): 0.1,
    ('sporty', 'sporty'): 1.0,
}


def get_color_group(color_name):
    return COLOR_GROUPS.get(color_name.lower(), 'neutral')


def color_pair_score(color_a, color_b):
    key = tuple(sorted([get_color_group(color_a), get_color_group(color_b)]))
    return GROUP_COMPAT.get(key, 0.5)


def style_pair_score(style_a, style_b):
    key = tuple(sorted([style_a.lower(), style_b.lower()]))
    return STYLE_COMPAT.get(key, 0.5)


def score_outfit(items):
    colors = [i.color_primary for i in items]
    styles = []
    for item in items:
        tags = [t.strip() for t in item.style_tags.split(',') if t.strip()]
        if tags:
            styles.append(tags[0])

    color_pairs = [
        (colors[i], colors[j])
        for i in range(len(colors))
        for j in range(i + 1, len(colors))
    ]
    color_score = (
        sum(color_pair_score(a, b) for a, b in color_pairs) / len(color_pairs)
        if color_pairs else 1.0
    )

    style_pairs = [
        (styles[i], styles[j])
        for i in range(len(styles))
        for j in range(i + 1, len(styles))
    ]
    style_score = (
        sum(style_pair_score(a, b) for a, b in style_pairs) / len(style_pairs)
        if style_pairs else 1.0
    )

    return round(color_score * 0.6 + style_score * 0.4, 3)


def get_primary_style(items):
    all_styles = []
    for item in items:
        all_styles.extend([t.strip() for t in item.style_tags.split(',') if t.strip()])
    if not all_styles:
        return 'casual'
    return max(set(all_styles), key=all_styles.count)


def generate_suggestions(items, style_filter=None, limit=20):
    tops = [i for i in items if i.category == 'top']
    bottoms = [i for i in items if i.category == 'bottom']
    shoes_list = [i for i in items if i.category == 'shoes']

    if not tops or not bottoms or not shoes_list:
        return []

    outfits = []
    for top, bottom, shoes in product(tops, bottoms, shoes_list):
        combo = [top, bottom, shoes]
        score = score_outfit(combo)
        primary_style = get_primary_style(combo)

        if style_filter and style_filter.lower() != 'all' and primary_style != style_filter.lower():
            continue

        outfits.append({
            'items': [item.to_dict() for item in combo],
            'score': score,
            'occasion': primary_style,
        })

    outfits.sort(key=lambda x: x['score'], reverse=True)
    return outfits[:limit]
