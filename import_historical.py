"""
import_historical.py — Import historical rounds from main branch's closingRanks.json

Reads /tmp/main_closingRanks.json (extracted from main branch) and adds
historical round data to our current closingRanks.json.

Historical rounds to import:
  2023_R1, 2023_R2, 2023_R4, 2023_R5
  2024_R1, 2024_R2, 2024_R4, 2024_R5
  2025_R4

Strategy:
  - Valid categories imported as-is (GEN/OBC/EWS/SC/ST/+PwD)
  - "GNYes" → "GEN" (parse artifact fix)
  - Records with bad categories in R2 (All India, DNB Quota, Fresh Allotted...) are skipped
  - Rank format converted from [int] to [[int, category]] (use allotted_cat as candidateCat)
  - Matched records: historical rounds added to existing record
  - Unmatched records: new record created with historical rounds only
"""

import json
from collections import defaultdict

HIST_ROUNDS = [
    '2023_R1', '2023_R2', '2023_R4', '2023_R5',
    '2024_R1', '2024_R2', '2024_R4', '2024_R5',
    '2025_R4',
]

VALID_CATS = {'GEN', 'OBC', 'EWS', 'SC', 'ST', 'OBC-PwD', 'GEN-PwD', 'SC-PwD', 'EWS-PwD', 'ST-PwD'}

CAT_FIX = {
    'GNYes': 'GEN',
}


def fix_category(cat):
    """Return fixed category, or None if invalid/unmappable."""
    if cat in VALID_CATS:
        return cat
    if cat in CAT_FIX:
        return CAT_FIX[cat]
    return None


def main():
    print("Loading current closingRanks.json...")
    with open('src/data/closingRanks.json') as f:
        our_data = json.load(f)
    print(f"  Our records: {len(our_data)}")

    print("Loading main's closingRanks.json...")
    with open('/tmp/main_closingRanks.json') as f:
        main_data = json.load(f)
    print(f"  Main records: {len(main_data)}")

    # Build lookup from our data
    our_lookup = {}
    for item in our_data:
        key = (item['institute'], item['course'], item['quota'], item['category'], item['state'])
        our_lookup[key] = item

    # Process historical rounds
    matched = 0
    new_records = 0
    skipped_bad_cat = 0

    # Collect new records to add (keyed to avoid duplicates)
    new_items = {}  # key -> item

    for hist_item in main_data:
        ranks = hist_item.get('ranks', {})

        for rnd in HIST_ROUNDS:
            if rnd not in ranks or not ranks[rnd]:
                continue

            raw_cat = hist_item.get('category', '')
            fixed_cat = fix_category(raw_cat)
            if fixed_cat is None:
                skipped_bad_cat += 1
                continue

            # Determine the correct key with the fixed category
            key = (
                hist_item['institute'],
                hist_item['course'],
                hist_item['quota'],
                fixed_cat,
                hist_item['state'],
            )

            # Convert ranks from [int] to [[int, fixed_cat]]
            hist_ranks = [[r, fixed_cat] for r in ranks[rnd] if isinstance(r, int)]

            if key in our_lookup:
                # Add to existing record
                existing = our_lookup[key]
                if rnd not in existing['ranks']:
                    existing['ranks'][rnd] = hist_ranks
                    matched += 1
                # else: already has this round (shouldn't happen for historical rounds)
            else:
                # Create new record or merge into new_items
                if key not in new_items:
                    new_items[key] = {
                        'institute': hist_item['institute'],
                        'state':     hist_item['state'],
                        'course':    hist_item['course'],
                        'quota':     hist_item['quota'],
                        'category':  fixed_cat,
                        'fee':       hist_item.get('fee', '-'),
                        'stipend':   hist_item.get('stipend', '-'),
                        'bondPenalty': hist_item.get('bondPenalty', '-'),
                        'bondYears': hist_item.get('bondYears', '-'),
                        'ranks':     {},
                    }
                new_items[key]['ranks'][rnd] = hist_ranks
                new_records += 1

    # Append new records to our data
    max_id = max(item.get('id', 0) for item in our_data) if our_data else 0
    for i, item in enumerate(new_items.values(), start=max_id + 1):
        item['id'] = i
        our_data.append(item)

    print(f"\nResults:")
    print(f"  Historical rounds added to existing records: {matched}")
    print(f"  New records created: {len(new_items)} (from {new_records} round additions)")
    print(f"  Skipped (bad categories): {skipped_bad_cat}")
    print(f"  Total records: {len(our_data)}")

    with open('src/data/closingRanks.json', 'w') as f:
        json.dump(our_data, f, ensure_ascii=False, indent=2)
    print("Saved to src/data/closingRanks.json")


if __name__ == '__main__':
    main()
