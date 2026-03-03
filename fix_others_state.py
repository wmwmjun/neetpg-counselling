"""
fix_others_state.py — Fix records with state="Others" by merging into correctly-stated records

Strategy:
  1. Find the correct state for each "Others" record via:
     a. Exact key match (institute, course, quota, category) -> known state
     b. Institute-only match (if the institute exists in only one state)
  2. If a matching record already exists with the correct state -> merge rounds
  3. If no matching record exists -> just update the state
  4. Delete the now-redundant "Others" records
"""

import json
from collections import defaultdict


def merge_ranks(target_ranks, source_ranks):
    """Add rounds from source_ranks to target_ranks if not already present."""
    for rnd, entries in source_ranks.items():
        if rnd not in target_ranks or not target_ranks[rnd]:
            target_ranks[rnd] = entries


def main():
    with open('src/data/closingRanks.json') as f:
        data = json.load(f)

    print(f"Input: {len(data)} records")

    # Build state lookup: (inst, course, quota, cat) -> state
    state_lookup = {}
    # Build institute-only state: inst -> set of states
    inst_states = defaultdict(set)
    for item in data:
        if item['state'] != 'Others':
            key = (item['institute'], item['course'], item['quota'], item['category'])
            state_lookup[key] = item['state']
            inst_states[item['institute']].add(item['state'])

    # Build record lookup by full key for merging
    record_lookup = {}
    for item in data:
        if item['state'] != 'Others':
            key = (item['institute'], item['course'], item['quota'], item['category'], item['state'])
            record_lookup[key] = item

    others_merged = 0
    others_state_fixed = 0
    others_skipped = 0
    to_remove_ids = set()

    for item in data:
        if item['state'] != 'Others':
            continue

        inst, course, quota, cat = item['institute'], item['course'], item['quota'], item['category']

        # Determine correct state
        correct_state = state_lookup.get((inst, course, quota, cat))
        if correct_state is None:
            # Try institute-only
            states = inst_states.get(inst, set())
            if len(states) == 1:
                correct_state = list(states)[0]

        if correct_state is None:
            others_skipped += 1
            continue

        # Check if a correctly-stated record exists
        target_key = (inst, course, quota, cat, correct_state)
        if target_key in record_lookup:
            # Merge ranks into the existing record
            merge_ranks(record_lookup[target_key]['ranks'], item['ranks'])
            to_remove_ids.add(item['id'])
            others_merged += 1
        else:
            # Just fix the state
            item['state'] = correct_state
            # Add to lookup for subsequent iterations
            record_lookup[target_key] = item
            inst_states[inst].add(correct_state)
            others_state_fixed += 1

    # Remove merged Others records
    data = [item for item in data if item['id'] not in to_remove_ids]

    # Reassign IDs sequentially
    for i, item in enumerate(data, start=1):
        item['id'] = i

    print(f"Others records merged into existing: {others_merged}")
    print(f"Others records state updated: {others_state_fixed}")
    print(f"Others records skipped (no state found): {others_skipped}")
    print(f"Output: {len(data)} records")

    with open('src/data/closingRanks.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved.")


if __name__ == '__main__':
    main()
