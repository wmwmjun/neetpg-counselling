"""
normalize_data.py
正規化スクリプト: closingRanks.json の course / quota / category を
ユーザー定義の canonical list に統一する。
"""

import json
from collections import Counter

# ---------------------------------------------------------------------------
# 1. コース名マッピング (raw value → canonical)
# ---------------------------------------------------------------------------

# NBE Diploma short codes (AD quota) — quota 判定に使用
NBE_DIPLOMA_SHORT_CODES = {
    'NBDA', 'NBDO', 'NDORT', 'NDDVL',
    'NFLM', 'NDCH', 'NDEM', 'NDGO', 'NDLO', 'NDMR', 'NDTC',
}

COURSE_MAP = {
    # ── (NBEMS) = DNB long form ─────────────────────────────────────────────
    '(NBEMS) ANAESTHESIOLO GY':                            'DNB Anaesthesiology',
    '(NBEMS) ANAESTHESIOLOGY':                             'DNB Anaesthesiology',
    '(NBEMS) Anatomy':                                     'DNB Anatomy',
    '(NBEMS) BIOCHEMISTRY':                                'DNB Biochemistry',
    '(NBEMS) COMMUNITY MEDICINE':                          'DNB Social & Preventive Medicine',
    '(NBEMS) Cardio Vascular and Thoracic Surgery (Direct 6 Years Course)':
                                                           'DNB Cardio Thoracic Surgery (6 years)',
    '(NBEMS) DERMATOLOGY and VENEREOLOGY and LEPROSY':     'DNB Dermatology & Venereology',
    '(NBEMS) Emergency Medicine':                          'DNB Emergency Medicine',
    '(NBEMS) FAMILY MEDICINE':                             'DNB Family Medicine',
    '(NBEMS) FORENSIC MEDICINE':                           'DNB Forensic Medicine',
    '(NBEMS) GENERAL MEDICINE':                            'DNB General Medicine',
    '(NBEMS) GENERAL SURGERY':                             'DNB General Surgery',
    '(NBEMS) Geriatric Medicine':                          'DNB Geriatric Medicine',
    '(NBEMS) Hospital Administration':                     'DNB Health Administration including Hospital Administration',
    '(NBEMS) IMMUNO- HAEMATOLOGY AND BLOOD TRANSFUSION':   'DNB Immuno Hematology & Transfusion Medicine',
    '(NBEMS) MICROBIOLOGY':                                'DNB Microbiology',
    '(NBEMS) NUCLEAR MEDICINE':                            'DNB Nuclear Medicine',
    '(NBEMS) Neuro Surgery (Direct 6 Years Course)':       'DNB Neuro Surgery (6 years)',
    '(NBEMS) OPHTHALMOLOGY':                               'DNB Ophthalmology',
    '(NBEMS) ORTHOPAEDICS':                                'DNB Orthopedics Surgery',
    '(NBEMS) Obstetrics and Gynaecology':                  'DNB Obstetrics & Gynaecology',
    '(NBEMS) Otorhinolaryngology (E.N.T.)':                'DNB ENT',
    '(NBEMS) PAEDIATRICS':                                 'DNB Paediatrics',
    '(NBEMS) PATHOLOGY':                                   'DNB Pathology',
    '(NBEMS) PHARMACOLOGY':                                'DNB Pharmacology',
    '(NBEMS) PHYSICAL MED. and REHABILITATION':            'DNB Physical Medicine & Rehabilitation',
    '(NBEMS) PHYSIOLOGY':                                  'DNB Physiology',
    '(NBEMS) PSYCHIATRY':                                  'DNB Psychiatry',
    '(NBEMS) Paediatric Surgery (Direct 6 Years Course)':  'DNB Paediatric Surgery (6 years)',
    '(NBEMS) Palliative Medicine':                         'DNB Palliative Medicine',
    '(NBEMS) Plastic and Reconstructive Surgery (Direct 6 Years Course)':
                                                           'DNB Plastic Surgery (6 years)',
    '(NBEMS) RADIATION ONCOLOGY':                          'DNB Radio Therapy',
    '(NBEMS) RADIO- DIAGNOSIS':                            'DNB Radio Diagnosis',
    '(NBEMS) Respiratory Medicine':                        'DNB Respiratory Diseases',

    # ── (NBEMS-DIPLOMA) = NBE Diploma long form ─────────────────────────────
    '(NBEMS-DIPLOMA) ANAESTHESIOLO GY':                    'Diploma in Anaesthesia-NBE',
    '(NBEMS-DIPLOMA) ANAESTHESIOLOGY':                     'Diploma in Anaesthesia-NBE',
    '(NBEMS-DIPLOMA) FAMILY MEDICINE':                     'Diploma in Family Medicine-NBE',
    '(NBEMS-DIPLOMA) OPHTHALMOLOGY':                       'Diploma in Ophthalmology-NBE',
    '(NBEMS-DIPLOMA) Obstetrics and Gynaecology':          'Diploma in Obstetrics & Gynaecology-NBE',
    '(NBEMS-DIPLOMA) Otorhinolaryngology (E.N.T.)':        'Diploma in Oto-Rhino-Laryngology-NBE',
    '(NBEMS-DIPLOMA) PAEDIATRICS':                         'Diploma in Child Health-NBE',
    '(NBEMS-DIPLOMA) RADIO- DIAGNOSIS':                    'Diploma in Radio-Diagnosis-NBE',
    '(NBEMS-DIPLOMA) RADIO-DIAGNOSIS':                     'Diploma in Radio-Diagnosis-NBE',
    '(NBEMS-DIPLOMA) Tuberculosis and CHEST DISEASES':     'Diploma in Tuberculosis & Chest Diseases-NBE',

    # ── DNB short codes (AD quota) ───────────────────────────────────────────
    'DANS':   'DNB Anaesthesiology',
    'DBIO':   'DNB Biochemistry',
    'DCOM':   'DNB Social & Preventive Medicine',
    'DCTVS':  'DNB Cardio Thoracic Surgery (6 years)',
    'DDVL':   'DNB Dermatology & Venereology',
    'DEMM':   'DNB Emergency Medicine',
    'DENT':   'DNB ENT',
    'DFLM':   'DNB Family Medicine',
    'DFRM':   'DNB Forensic Medicine',
    'DGRM':   'DNB Geriatric Medicine',
    'DHAD':   'DNB Health Administration including Hospital Administration',
    'DHBT':   'DNB Immuno Hematology & Transfusion Medicine',
    'DIBT':   'DNB Immuno Hematology & Transfusion Medicine',
    'DMED':   'DNB General Medicine',
    'DMIC':   'DNB Microbiology',
    'DMRD':   'DNB Radio Diagnosis',
    'DNRS':   'DNB Neuro Surgery (6 years)',
    'DNUM':   'DNB Nuclear Medicine',
    'DOBG':   'DNB Obstetrics & Gynaecology',
    'DOPH':   'DNB Ophthalmology',
    'DORT':   'DNB Orthopedics Surgery',
    'DPED':   'DNB Paediatrics',
    'DPEDS':  'DNB Paediatric Surgery (6 years)',
    'DPHA':   'DNB Pharmacology',
    'DPHYN':  'DNB Physiology',
    'DPLM':   'DNB Palliative Medicine',
    'DPLS':   'DNB Plastic Surgery (6 years)',
    'DPMR N': 'DNB Physical Medicine & Rehabilitation',
    'DPSY':   'DNB Psychiatry',
    'DPSYN':  'DNB Psychiatry',
    'DPTH':   'DNB Pathology',
    'DRAD':   'DNB Radio Diagnosis',
    'DREP':   'DNB Respiratory Diseases',
    'DRTH':   'DNB Radio Therapy',
    'DSUR':   'DNB General Surgery',

    # ── NBE Diploma short codes (AD quota) ──────────────────────────────────
    'NBDA':  'Diploma in Anaesthesia-NBE',
    'NBDO':  'Diploma in Ophthalmology-NBE',
    'NDCH':  'Diploma in Child Health-NBE',
    'NDEM':  'Diploma in Emergency Medicine-NBE',
    'NDDVL': 'Diploma in Dermatology, Venereology and Leprosy',
    'NDGO':  'Diploma in Obstetrics & Gynaecology-NBE',
    'NDLO':  'Diploma in Oto-Rhino-Laryngology-NBE',
    'NDMR':  'Diploma in Radio-Diagnosis-NBE',
    'NDORT': 'Diploma in Orthopaedics',
    'NDTC':  'Diploma in Tuberculosis & Chest Diseases-NBE',
    'NFLM':  'Diploma in Family Medicine-NBE',

    # ── MD/MS/MCh short codes ────────────────────────────────────────────────
    'ANAT':  'MD Anatomy',
    'ASTH':  'MD Anaesthesiology',
    'BIOC':  'MD Bio-Chemistry',
    'DV-L':  'MD Dermatology, Venereology & Leprosy',
    'E-CC':  'MD Emergency Medicine',
    'EN-T':  'MS ENT',
    'F-ME':  'MD Family Medicine',
    'FMED':  'MD Family Medicine',
    'GERA':  'MD Geriatrics',
    'GMED':  'MD General Medicine',
    'GSUR':  'MS General Surgery',
    'HADM':  'MD Hospital Administration',
    'MICR':  'MD Microbiology',
    'MSTS':  'MS Traumatology and Surgery',
    'N-ME':  'MD Nuclear Medicine',
    'NUSR':  'MCh Neurosurgery (6 years)',
    'OBGY':  'MS Obstetrics & Gynaecology',
    'OPTH':  'MS Ophthalmology',
    'ORTH':  'MS Orthopaedics',
    'P-SM':  'MD Social & Preventive Medicine',
    'PAED':  'MD Paediatrics',
    'PATH':  'MD Pathology',
    'PHAR':  'MD Pharmacology',
    'PHYS':  'MD Physiology',
    'PM-R':  'MD Physical Medicine & Rehabilitation',
    'PMED':  'MD Palliative Medicine',
    'PSYY':  'MD Psychiatry',
    'RADD':  'MD Radio Diagnosis',
    'RADT':  'MD Radiation Oncology',
    'SMED':  'MD Sports Medicine',
    'T-FM':  'MD Tropical Medicine',
    'TBRD':  'MD Tuberculosis & Respiratory Diseases',
    'TMED':  'MD Tropical Medicine',
    'DTCD':  'MD Tuberculosis & Respiratory Diseases',

    # ── Diploma short codes ──────────────────────────────────────────────────
    'D-AN': 'Diploma in Anaesthesia',
    'D-CH': 'Diploma in Child Health',
    'D-CP': 'Diploma in Clinical Pathology',
    'D-GO': 'Diploma in Obstetrics & Gynaecology',
    'D-LO': 'Diploma in Oto-Rhino-Laryngology',
    'D-OP': 'Diploma in Ophthalmology',
    'D-PH': 'Diploma in Public Health',
    'D-RM': 'Diploma in Radiation Medicine',
    'D-SM': 'Diploma in Sports Medicine',
    'DMPH': 'Master of Public Health (Epidemiology)',

    # ── M.D. long form ───────────────────────────────────────────────────────
    'M.D. (AEROSPACE MEDICINE)':                    'MD Aviation Medicine/Aerospace Medicine',
    'M.D. (ANAESTHESIOLO GY)':                      'MD Anaesthesiology',
    'M.D. (ANAESTHESIOLOGY)':                       'MD Anaesthesiology',
    'M.D. (BIOCHEMISTRY)':                          'MD Bio-Chemistry',
    'M.D. (COMMUNITY HEALTH and ADMN.)':            'MD Community Health Administration',
    'M.D. (DERM.,VENE. and LEPROSY)/ (DERMATOLOGY)/( SKIN and VENEREAL DISEASES)/(VENE REOLOGY)':
                                                    'MD Dermatology, Venereology & Leprosy',
    'M.D. (DERM.,VENE. and LEPROSY)/ (DERMATOLOGY)/(SKIN and VENEREAL DISEASES)/(VENEREOL OGY)':
                                                    'MD Dermatology, Venereology & Leprosy',
    'M.D. (DERM.,VENE. and LEPROSY)/ (DERMATOLOGY)/(SKIN and VENEREAL DISEASES)/(VENEREOLOG Y)':
                                                    'MD Dermatology, Venereology & Leprosy',
    'M.D. (Emergency and Critical Care)/M.D. (Emergency Medicine)':
                                                    'MD Emergency Medicine',
    'M.D. (FAMILY MEDICINE)':                       'MD Family Medicine',
    'M.D. (FORENSIC MEDICINE)':                     'MD Forensic Medicine',
    'M.D. (GENERAL MEDICINE)':                      'MD General Medicine',
    'M.D. (Hospital Administration)':               'MD Hospital Administration',
    'M.D. (MICROBIOLOGY)':                          'MD Microbiology',
    'M.D. (Obst. and Gynae)/MS (Obstetrics and Gynaecology)':
                                                    'MS Obstetrics & Gynaecology',
    'M.D. (PAEDIATRICS)':                           'MD Paediatrics',
    'M.D. (PALLIATIVE MEDICINE)':                   'MD Palliative Medicine',
    'M.D. (PATHOLOGY)':                             'MD Pathology',
    'M.D. (PHARMACOLOGY )':                         'MD Pharmacology',
    'M.D. (PHARMACOLOGY)':                          'MD Pharmacology',
    'M.D. (PHYSICAL MED. and REHABILITATION)':      'MD Physical Medicine & Rehabilitation',
    'M.D. (PHYSIOLOGY)':                            'MD Physiology',
    'M.D. (PREVENTIVE and SOCIAL MEDICINE)/ COMMUNITY MEDICINE':
                                                    'MD Social & Preventive Medicine',
    'M.D. (PSYCHIATRY)':                            'MD Psychiatry',
    'M.D. (RADIO- DIAGNOSIS)':                      'MD Radio Diagnosis',
    'M.D. (RADIO-DIAGNOSIS)':                       'MD Radio Diagnosis',
    'M.D. (Radiotherapy/ Radiation Oncology)':      'MD Radiation Oncology',
    'M.D. (TROPICAL MEDICINE)':                     'MD Tropical Medicine',
    'M.D. (Tuberculosis and Respiratory diseases)/Pulmonar y Medicine /M.D. (Respiratory Medicine)':
                                                    'MD Tuberculosis & Respiratory Diseases',
    'M.D. (Tuberculosis and Respiratory diseases)/Pulmonary Medicine /M.D. (Respiratory Medicine)':
                                                    'MD Tuberculosis & Respiratory Diseases',
    'M.D. GERIATRICS':                              'MD Geriatrics',
    'M.D. IN NUCLEAR MEDICINE':                     'MD Nuclear Medicine',
    'M.D. IN TRANSFUSION MEDICINE/ IMMUNO- HAEMATOLOGY and BLOOD TRANSFUSION':
                                                    'MD Immuno Haematology & Blood Transfusion',
    'M.D. Sports Medicine':                         'MD Sports Medicine',
    'M.D.Laboratory Medicine Course':               'MD Lab Medicine',
    'M.P.H. (EPIDEMIOLOGY)':                        'Master of Public Health (Epidemiology)',

    # ── M.S. / M.Ch. long form ───────────────────────────────────────────────
    'M.Ch. (Neuro Surgery)':              'MCh Neurosurgery (6 years)',
    'M.S. ( Traumatology and Surgery )':  'MS Traumatology and Surgery',
    'M.S. (E.N.T.)':                      'MS ENT',
    'M.S. (GENERAL SURGERY)':             'MS General Surgery',
    'M.S. (OPHTHALMOLOG Y)':              'MS Ophthalmology',
    'M.S. (OPHTHALMOLOGY)':               'MS Ophthalmology',
    'M.S. (ORTHOPAEDICS)':                'MS Orthopaedics',
    'MD/MS (Anatomy)':                    'MD Anatomy',

    # ── Diploma long form ────────────────────────────────────────────────────
    'DIP IN RADIATION MEDICINE':          'Diploma in Radiation Medicine',
    'DIP. IN DERM. VENEREOLOGY and LEPROSY/DERMA TOLOGY /VENEREOLOGY and DERMATOLOGY/L EPROSY/VENERE AL DISEASE and LEPROSY':
                                          'Diploma in Dermatology, Venereology and Leprosy',
    'DIP. IN DERM. VENEREOLOGY and LEPROSY/DERMATOLO GY /VENEREOLOGY and DERMATOLOGY/LEPRO SY/VENEREAL DISEASE and LEPROSY':
                                          'Diploma in Dermatology, Venereology and Leprosy',
    'DIP. IN DERM. VENEREOLOGY and LEPROSY/DERMATOLOGY /VENEREOLOGY and DERMATOLOGY/LEPROSY/ VENEREAL DISEASE and LEPROSY':
                                          'Diploma in Dermatology, Venereology and Leprosy',
    'DIP. IN FORENSIC MEDICINE':          'Diploma in Forensic Medicine',
    'DIP. IN MEDICAL RADIO- THERAPY':     'Diploma in Radio Therapy',
    'DIP. IN MEDICAL RADIO-THERAPY':      'Diploma in Radio Therapy',
    'DIP. IN PHY. MEDICINE and REHAB.':   'Diploma in Physical Medicine & Rehabilitation',
    'DIP. IN SPORTS MEDICINE':            'Diploma in Sports Medicine',
    'DIP. IN T.B. and CHEST DISEASES':    'Diploma in Tuberculosis & Chest Diseases',
    'DIP.IN GYNAE. and OBST.':            'Diploma in Obstetrics & Gynaecology',
    'DIP.IN IMMUNO- HAEMATOLOGY and BLOOD TRANSFUSION':
                                          'Diploma in Immuno-Haematology and Blood Transfusion',
    'DIP.IN MEDICAL RADIO- DIAGNOSIS':    'Diploma in Radio-Diagnosis',
    'DIP.IN MEDICAL RADIO-DIAGNOSIS':     'Diploma in Radio-Diagnosis',
    'DIPLOMA IN ANAESTHESIOLO GY':        'Diploma in Anaesthesia',
    'DIPLOMA IN ANAESTHESIOLOGY':         'Diploma in Anaesthesia',
    'DIPLOMA IN BACTERIOLOGY':            'Diploma in Microbiology',
    'DIPLOMA IN CHILD HEALTH/ PAEDIATRICS': 'Diploma in Child Health',
    'DIPLOMA IN CLINICAL PATHOLOGY':      'Diploma in Clinical Pathology',
    'DIPLOMA IN DIABETOLOGY':             'Diploma in Diabetology',
    'DIPLOMA IN HEALTH ADMINISTRATION':   'Diploma in Health Administration',
    'DIPLOMA IN OPHTHALMOLOGY /DOMS':     'Diploma in Ophthalmology',
    'DIPLOMA IN OPHTHALMOLOGY/DOM S':     'Diploma in Ophthalmology',
    'DIPLOMA IN OPHTHALMOLOGY/DOMS':      'Diploma in Ophthalmology',
    'DIPLOMA IN ORTHOPAEDICS':            'Diploma in Orthopaedics',
    'DIPLOMA IN OTO- RHINO- LARYNGOLOGY': 'Diploma in Oto-Rhino-Laryngology',
    'DIPLOMA IN OTO- RHINO-LARYNGOLOGY':  'Diploma in Oto-Rhino-Laryngology',
    'DIPLOMA IN OTO-RHINO- LARYNGOLOGY':  'Diploma in Oto-Rhino-Laryngology',
    'DIPLOMA IN PUBLIC HEALTH':           'Diploma in Public Health',
    'Diploma-Emergency Medicine':         'Diploma in Emergency Medicine-NBE',
    'PG Diploma in Psychological Medicine / Psychiatric Medicine':
                                          'Diploma in Psychological Medicine',
}


# ---------------------------------------------------------------------------
# 2. クオータ名マッピング
#    (course に依存するもの: 'AD' / 'DNB Quota' は後処理で決定)
# ---------------------------------------------------------------------------

QUOTA_MAP_SIMPLE = {
    'AI':                                   'AIQ',
    'All India':                            'AIQ',
    # AM / Armed Forces Medical は normalize_quota() 内で course を見て判定
    # 'AM':                                 'AFMS',
    # 'Armed Forces Medical':               'AFMS',
    'BH':                                   'BHU',
    'Banaras Hindu University':             'BHU',
    'DU':                                   'DU',
    'Delhi University Quota':               'DU',
    'IP':                                   'IP',
    'IP University Quota':                  'IP',
    'JM':                                   'JM',
    'Jain Minority Quota':                  'JM',
    'MM':                                   'MM',
    'Muslim Minority Quota':                'MM',
    'NR':                                   'NRI',
    'Non- Resident Indian':                 'NRI',
    'Non-Resident Indian':                  'NRI',
    'PS':                                   'MNG',
    'Self- Financed Merit Seat':            'MNG',
    'Self-Financed Merit Seat':             'MNG',
    'Self-Financed Merit Seat/(Paid Seat Quota)': 'MNG',
    'Aligarh Muslim University':            'AMU',
    # AD と DNB Quota は normalize_quota() 内で course を見て判定
}


def normalize_quota(raw_quota: str, normalized_course: str) -> str:
    """
    クオータを正規化する。
    'AD' と 'DNB Quota' は正規化後のコース名で DNB/NBE Diploma を判別する。
    """
    if raw_quota in QUOTA_MAP_SIMPLE:
        return QUOTA_MAP_SIMPLE[raw_quota]

    if raw_quota in ('AD', 'DNB Quota'):
        # Diploma コースなら NBE Diploma、それ以外は DNB Post MBBS
        if normalized_course.startswith('Diploma in '):
            return 'NBE Diploma'
        else:
            return 'DNB Post MBBS'

    if raw_quota in ('AM', 'Armed Forces Medical'):
        # DNB コースなら AFMS-DNB、それ以外は AFMS
        if normalized_course.startswith('DNB '):
            return 'AFMS-DNB'
        else:
            return 'AFMS'

    # そのまま返す（未知のクオータ）
    return raw_quota


# ---------------------------------------------------------------------------
# 3. カテゴリ名マッピング
# ---------------------------------------------------------------------------

CATEGORY_MAP = {
    '-':           'GEN',
    'General':     'GEN',
    'General PwD': 'GEN-PwD',
    'Open':        'GEN',
    'Open PwD':    'GEN-PwD',
    'EWS':         'EWS',
    'EWS PwD':     'EWS-PwD',
    'OBC':         'OBC',
    'OBC PwD':     'OBC-PwD',
    'SC':          'SC',
    'SC PwD':      'SC-PwD',
    'ST':          'ST',
    'ST PwD':      'ST-PwD',
}


# ---------------------------------------------------------------------------
# 4. メイン処理
# ---------------------------------------------------------------------------

def main():
    input_path  = 'src/data/closingRanks.json'
    output_path = 'src/data/closingRanks.json'

    with open(input_path, 'r') as f:
        data = json.load(f)

    total = len(data)
    course_unchanged = Counter()
    quota_unchanged  = Counter()
    cat_unchanged    = Counter()

    for record in data:
        raw_course = record.get('course', '')
        raw_quota  = record.get('quota', '')
        raw_cat    = record.get('category', '')

        # --- course ---
        norm_course = COURSE_MAP.get(raw_course)
        if norm_course is None:
            course_unchanged[raw_course] += 1
            norm_course = raw_course  # そのまま使ってquota判定に渡す
        record['course'] = norm_course

        # --- quota (course 正規化後に判定) ---
        norm_quota = normalize_quota(raw_quota, norm_course)
        if norm_quota == raw_quota and raw_quota not in QUOTA_MAP_SIMPLE \
                and raw_quota not in ('AD', 'DNB Quota'):
            quota_unchanged[raw_quota] += 1
        record['quota'] = norm_quota

        # --- category (allotted category) ---
        norm_cat = CATEGORY_MAP.get(raw_cat)
        if norm_cat is None:
            cat_unchanged[raw_cat] += 1
            norm_cat = raw_cat
        record['category'] = norm_cat

        # --- candidate category per rank: [[rank, candidateCat], ...] ---
        for rnd, rank_entries in record.get('ranks', {}).items():
            if not rank_entries:
                continue
            # Support both old format [int] and new format [[int, str]]
            normalized = []
            for entry in rank_entries:
                if isinstance(entry, list) and len(entry) == 2:
                    rk, ccat = entry[0], entry[1]
                    norm_ccat = CATEGORY_MAP.get(ccat, ccat)
                    normalized.append([rk, norm_ccat])
                else:
                    # Old integer format — candidateCategory unknown, use allotted
                    normalized.append([int(entry), norm_cat])
            record['ranks'][rnd] = normalized

    # 保存
    with open(output_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # レポート
    print(f"=== 正規化完了: {total} レコード ===\n")

    if course_unchanged:
        print(f"【コース】未マッピング ({sum(course_unchanged.values())} 件):")
        for k, v in course_unchanged.most_common():
            print(f"  {v:5d}  {repr(k)}")
    else:
        print("【コース】全件マッピング済み ✓")

    if quota_unchanged:
        print(f"\n【クオータ】未マッピング ({sum(quota_unchanged.values())} 件):")
        for k, v in quota_unchanged.most_common():
            print(f"  {v:5d}  {repr(k)}")
    else:
        print("【クオータ】全件マッピング済み ✓")

    if cat_unchanged:
        print(f"\n【カテゴリ】未マッピング ({sum(cat_unchanged.values())} 件):")
        for k, v in cat_unchanged.most_common():
            print(f"  {v:5d}  {repr(k)}")
    else:
        print("【カテゴリ】全件マッピング済み ✓")

    print(f"\n出力: {output_path}")


if __name__ == '__main__':
    main()
