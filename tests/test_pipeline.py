from src.integration.pipeline import analyze_text, analyze_document, split_sentences

def test_vague_term_flagged_in_demo():
    result = analyze_text("The supplier shall respond soon.")
    assert any(d["label"] == "vague" for d in result["detections"])

def test_attachment_phrase_flagged_in_demo():
    result = analyze_text("The admin monitors the user with the sensor.")
    assert any(d["label"] == "attachment" for d in result["detections"])

def test_document_summary_counts_sentences():
    result = analyze_document("Respond soon. The service returns HTTP 200.")
    assert result["sentence_count"] == 2
    assert 0 <= result["ambiguity_rate"] <= 100

def test_sentence_split_preserves_punctuation():
    assert split_sentences("First sentence. Second sentence!") == ["First sentence.", "Second sentence!"]
