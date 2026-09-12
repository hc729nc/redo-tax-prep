"""Maps ComputedReturn line refs to AcroForm field names in the official IRS f1040.pdf
(2025 revision). Every mapping below was verified by cross-referencing each field's
rect position against the actual printed line-number stamp on the form (exact 9.7pt
vertical offset between a field's box and its line-number label, confirmed for every
entry here) - not guessed from field names, which are opaque (f1_NN/f2_NN) on this
form's AcroForm.

Lines intentionally left unmapped (IRA/pension/SS income, capital gains, credits,
estimated payments, etc.) are out of MVP scope - see docs/mvp-scope.md - and are left
blank on the generated PDF rather than guessed at.
"""

FORM_1040_FIELD_MAP: dict[str, str] = {
    "1a": "topmostSubform[0].Page1[0].f1_47[0]",
    "1z": "topmostSubform[0].Page1[0].f1_57[0]",
    "2b": "topmostSubform[0].Page1[0].f1_59[0]",
    "3b": "topmostSubform[0].Page1[0].f1_61[0]",
    "8": "topmostSubform[0].Page1[0].f1_72[0]",
    "9": "topmostSubform[0].Page1[0].f1_73[0]",
    "10": "topmostSubform[0].Page1[0].f1_74[0]",
    "11": "topmostSubform[0].Page1[0].f1_75[0]",  # Line 11a (AGI), page 1
    "11b": "topmostSubform[0].Page2[0].f2_01[0]",  # Line 11b (AGI restated), page 2
    "12": "topmostSubform[0].Page2[0].f2_02[0]",  # Line 12e (standard/itemized deduction)
    "15": "topmostSubform[0].Page2[0].f2_06[0]",
    "16": "topmostSubform[0].Page2[0].f2_08[0]",
    "18": "topmostSubform[0].Page2[0].f2_10[0]",
    "22": "topmostSubform[0].Page2[0].f2_14[0]",
    "23": "topmostSubform[0].Page2[0].f2_15[0]",
    "24": "topmostSubform[0].Page2[0].f2_16[0]",
    "25a": "topmostSubform[0].Page2[0].f2_17[0]",
    "25b": "topmostSubform[0].Page2[0].f2_18[0]",
    "25d": "topmostSubform[0].Page2[0].f2_20[0]",
    "33": "topmostSubform[0].Page2[0].f2_29[0]",
    "34": "topmostSubform[0].Page2[0].f2_30[0]",
    "37": "topmostSubform[0].Page2[0].f2_35[0]",
}

FORM_1040_NAME_SSN_FIELDS = {
    "first_name_and_mi": "topmostSubform[0].Page1[0].f1_14[0]",
    "last_name": "topmostSubform[0].Page1[0].f1_15[0]",
    "ssn": "topmostSubform[0].Page1[0].f1_16[0]",
}

# Filing status is NOT a true PDF radio group on this form - it's five independent
# checkbox fields, each with its own single "on" export value. Verified by the same
# offset method (each checkbox's rect sits exactly 7.7pt above its printed label,
# consistently, for all five). FilingStatus.MARRIED_FILING_JOINTLY maps to the
# second checkbox; "qualifying surviving spouse" (export "5") has no corresponding
# FilingStatus value and is intentionally not in this map.
FILING_STATUS_CHECKBOX_FIELDS: dict[str, tuple[str, str]] = {
    "single": ("topmostSubform[0].Page1[0].Checkbox_ReadOrder[0].c1_8[0]", "/1"),
    "married_filing_jointly": ("topmostSubform[0].Page1[0].Checkbox_ReadOrder[0].c1_8[1]", "/2"),
    "married_filing_separately": ("topmostSubform[0].Page1[0].Checkbox_ReadOrder[0].c1_8[2]", "/3"),
    "head_of_household": ("topmostSubform[0].Page1[0].c1_8[0]", "/4"),
}

# Schedule B (f1040sb.pdf) - only the two totals that flow back to Form 1040 are
# mapped; the itemized payer-list rows are left blank since we don't model
# per-payer breakdowns, only aggregate totals.
SCHEDULE_B_FIELD_MAP = {
    "2": "topmostSubform[0].Page1[0].f1_31[0]",  # Total interest (before exclusions)
    "4": "topmostSubform[0].Page1[0].f1_33[0]",  # Taxable interest -> Form 1040 line 2b
    "6": "topmostSubform[0].Page1[0].f1_64[0]",  # Ordinary dividends -> Form 1040 line 3b
}

# Schedule C (f1040sc.pdf) - field numbering does not match line numbers on this
# form (e.g. line 1 is field f1_10); verified by offset against the printed line
# stamps, same method as the other forms here.
SCHEDULE_C_FIELD_MAP = {
    "1": "topmostSubform[0].Page1[0].f1_10[0]",  # Gross receipts
    "28": "topmostSubform[0].Page1[0].f1_41[0]",  # Total expenses
    "31": "topmostSubform[0].Page1[0].f1_46[0]",  # Net profit or (loss)
}

# Schedule A (f1040sa.pdf) - uses its own top-level name "form1[0]", unlike the
# other forms here ("topmostSubform[0]"); each IRS form PDF has its own internal
# naming. Only the two itemized categories this MVP supports are mapped (mortgage
# interest, cash charitable gifts) - medical, SALT, casualty/theft, and other
# itemized categories are out of scope (see docs/mvp-scope.md).
SCHEDULE_A_FIELD_MAP = {
    "8e": "form1[0].Page1[0].f1_20[0]",  # Total home mortgage interest and points
    "10": "form1[0].Page1[0].f1_22[0]",  # Add lines 8e and 9
    "11": "form1[0].Page1[0].f1_23[0]",  # Gifts by cash or check
    "14": "form1[0].Page1[0].f1_26[0]",  # Add lines 11 through 13
    "17": "form1[0].Page1[0].f1_30[0]",  # Total itemized deductions -> Form 1040 line 12e
}

# Schedule SE (f1040sse.pdf) - simplified single-page 2025 revision. Only the
# lines relevant to a simple Schedule-C-only filer (no farm/church/optional
# method income) are mapped; lines 10/11 (the SS/Medicare sub-split of line 12)
# are left blank since our engine doesn't expose that breakdown separately.
SCHEDULE_SE_FIELD_MAP = {
    "2": "topmostSubform[0].Page1[0].f1_5[0]",  # Net profit from Schedule C
    "3": "topmostSubform[0].Page1[0].f1_6[0]",  # Combine lines 1a, 1b, and 2
    "4a": "topmostSubform[0].Page1[0].f1_7[0]",  # Line 3 x 92.35%
    "4c": "topmostSubform[0].Page1[0].f1_9[0]",  # Combine lines 4a and 4b
    "6": "topmostSubform[0].Page1[0].f1_12[0]",  # Combine lines 4c and 5b
    "12": "topmostSubform[0].Page1[0].f1_21[0]",  # Self-employment tax
    "13": "topmostSubform[0].Page1[0].f1_22[0]",  # Deduction for one-half of SE tax
}
