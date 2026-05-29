from collections import Counter
 
LOW_SIMILARITY_THRESHOLD = 0.5
 
def reuse(top_cases: list[dict]) -> dict:
    if not top_cases:
        return {
            "recommendation": "Tidak dapat ditentukan",
            "similarity_score": 0.0,
            "majority_vote": "Tidak dapat ditentukan",
            "vote_detail": {},
            "confidence": 0.0,
            "consistent": False,
            "note": "Tidak ada kasus serupa ditemukan di basis kasus.",
        }
 
    # Rekomendasi utama dari kasus #1
    best_case   = top_cases[0]
    recommendation   = best_case["decision"]
    similarity_score = best_case["similarity"]
 
    # Majority vote dari semua top-N
    decisions = [
        str(c["decision"]).strip()
        for c in top_cases
        if c.get("decision")
    ]
    vote_counter = Counter(decisions)
    majority_vote = vote_counter.most_common(1)[0][0]
    confidence    = vote_counter[majority_vote] / len(decisions)
 
    # Apakah rekomendasi konsisten dengan majority?
    consistent = recommendation == majority_vote
 
    # Catatan untuk pakar
    n = len(top_cases)
    vote_str = ", ".join(f"{k}: {v}" for k, v in vote_counter.items())
 
    if consistent:
        note = (
            f"Rekomendasi konsisten dengan majority vote dari {n} kasus terdekat "
            f"({vote_str}). Similarity kasus terbaik: {similarity_score:.4f}."
        )
    else:
        note = (
            f"Perhatian: Kasus terbaik merekomendasikan '{recommendation}' "
            f"(similarity {similarity_score:.4f}), namun majority vote dari {n} kasus "
            f"menunjukkan '{majority_vote}' ({vote_str}). "
            f"Mohon perhatian pakar untuk memverifikasi keputusan."
        )
 
    if similarity_score < LOW_SIMILARITY_THRESHOLD:
        note += (
            f"Similarity rendah ({similarity_score:.4f} < "
            f"{LOW_SIMILARITY_THRESHOLD}) — "
            f"kemiripan dengan kasus di basis kasus masih rendah, "
            f"keputusan pakar sangat diperlukan."
        )
 
    return {
        "recommendation"  : recommendation,
        "similarity_score": round(similarity_score, 6),
        "majority_vote"   : majority_vote,
        "vote_detail"     : dict(vote_counter),
        "confidence"      : round(confidence, 4),
        "consistent"      : consistent,
        "note"            : note,
    }