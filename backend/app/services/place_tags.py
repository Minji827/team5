"""Join the supplied Busan Taste list conservatively; never use substring matching."""
import csv
import re


def normalized(value):
    return re.sub(r"[^가-힣a-z0-9]", "", str(value).lower())


# Kakao place 13271381 identifies this merchant at 광복로55번길 13 (checked 2026-10-22).
REVIEWED_ALIASES = {"3b26201ba6a956291d968261d80c95a7":
                    ("삼송초밥 부산남포동본점", "광복로55번길 13")}


def busan_taste_matches(frame, reference_path):
    with reference_path.open(encoding="utf-8-sig", newline="") as file:
        reference = list(csv.DictReader(file))
    matches = {}
    for row in frame.to_dict("records"):
        if row["category"] != "식당":
            continue
        district = re.search(r"부산(?:광역시)?\s+([가-힣]+(?:구|군))", row["address"])
        if not district:
            continue
        options = [r for r in reference if r["구군"].strip() == district.group(1)]
        # Do not tag ambiguous duplicate shop names within the district.
        same_name = frame[(frame["name"].map(normalized) == normalized(row["name"]))
                          & frame["address"].str.contains(district.group(1), regex=False)]
        if len(same_name) != 1:
            continue
        exact = [r for r in options if normalized(r["식당명"]) == normalized(row["name"])]
        alias = REVIEWED_ALIASES.get(row["id"])
        if not exact and alias and normalized(alias[1]) in normalized(row["address"]):
            exact = [r for r in options if r["식당명"] == alias[0]]
        if len(exact) == 1:
            matches[row["id"]] = exact[0]["식당명"]
    return matches
