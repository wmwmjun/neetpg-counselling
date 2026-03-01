"""
Regenerate branchStats.json and instituteStats.json from closingRanks.json.
Run this after any update to closingRanks.json (e.g. after add_round4.py).
"""
import json
from collections import defaultdict

with open('src/data/closingRanks.json') as f:
    data = json.load(f)

ROUNDS = ['2025_R1', '2025_R2', '2025_R3', '2025_R4']


def get_type(course):
    c = course.lower()
    if any(x in c for x in ['anatomy', 'physiology', 'biochemistry', 'community medicine', 'social']):
        return 'Pre-Clinical'
    if any(x in c for x in ['pathology', 'pharmacology', 'microbiology', 'forensic', 'biostatistics']):
        return 'Para-Clinical'
    return 'Clinical'


# --- Branch Stats ---
course_stats = defaultdict(lambda: {'seats': 0, 'ranks': [], 'institutes': set()})

for item in data:
    course = item.get('course', '')
    if not course:
        continue
    all_ranks = [r for rnd in ROUNDS for r in item.get('ranks', {}).get(rnd, [])]
    if all_ranks:
        course_stats[course]['seats'] += len(all_ranks)
        course_stats[course]['ranks'].extend(all_ranks)
        course_stats[course]['institutes'].add(item.get('institute', ''))

branch_results = []
for course, stats in course_stats.items():
    if stats['seats'] < 5:
        continue
    rs = sorted(stats['ranks'])
    branch_results.append({
        'course': course,
        'type': get_type(course),
        'seats': stats['seats'],
        'institutes': len(stats['institutes']),
        'openingRank': rs[0],
        'closingRank': rs[-1],
        'medianRank': rs[len(rs) // 2],
    })

branch_results.sort(key=lambda x: x['openingRank'])
with open('src/data/branchStats.json', 'w') as f:
    json.dump(branch_results, f, indent=2)
print(f"branchStats.json: {len(branch_results)} branches")

# --- Institute Stats ---
inst_stats = defaultdict(lambda: {
    'totalSeats': 0, 'courses': set(), 'state': '',
    'fee': '-', 'stipend': '-', 'bondPenalty': '-', 'bondYears': '-',
    'openingRank': float('inf'), 'closingRank': 0
})

for item in data:
    inst = item.get('institute', '')
    if not inst:
        continue
    all_ranks = [r for rnd in ROUNDS for r in item.get('ranks', {}).get(rnd, [])]
    if all_ranks:
        inst_stats[inst]['totalSeats'] += len(all_ranks)
        inst_stats[inst]['courses'].add(item.get('course', ''))
        inst_stats[inst]['state'] = item.get('state', '')
        for field in ['fee', 'stipend', 'bondPenalty', 'bondYears']:
            if item.get(field, '-') != '-':
                inst_stats[inst][field] = item[field]
        inst_stats[inst]['openingRank'] = min(inst_stats[inst]['openingRank'], min(all_ranks))
        inst_stats[inst]['closingRank'] = max(inst_stats[inst]['closingRank'], max(all_ranks))

inst_results = []
for inst, stats in inst_stats.items():
    if stats['openingRank'] == float('inf'):
        continue
    inst_results.append({
        'institute': inst,
        'state': stats['state'],
        'totalSeats': stats['totalSeats'],
        'courses': len(stats['courses']),
        'fee': stats['fee'],
        'stipend': stats['stipend'],
        'bondPenalty': stats['bondPenalty'],
        'bondYears': stats['bondYears'],
        'openingRank': stats['openingRank'],
        'closingRank': stats['closingRank'],
    })

inst_results.sort(key=lambda x: x['openingRank'])
with open('src/data/instituteStats.json', 'w') as f:
    json.dump(inst_results, f, indent=2)
print(f"instituteStats.json: {len(inst_results)} institutes")
print("Done.")
