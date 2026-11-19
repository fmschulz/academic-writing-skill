"""Check source-preserving extraction with small, explicitly synthetic inputs."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/build_scaffolds.py"
SPEC = importlib.util.spec_from_file_location("build_scaffolds", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def make_paper(
    root: Path, text: str, *, heading: str = "Results", start: int = 0
) -> dict:
    """Write a synthetic canonical source using the one supported manifest schema."""
    (root / "source.txt").write_text(text, encoding="utf-8")
    (root / "sections.json").write_text(
        json.dumps([{"heading": heading, "start": start, "end": len(text)}]),
        encoding="utf-8",
    )
    return {
        "paper_id": "test-only",
        "doi": "",
        "year": 2020,
        "title": "Synthetic verification fixture",
        "license": "test-only",
        "text_path": "source.txt",
        "text_sha256": builder.hashlib.sha256(text.encode()).hexdigest(),
        "sections_path": "sections.json",
        "authors": ["Public Test Author"],
        "license_url": "https://example.test/license",
        "xml_path": "article.xml",
        "xml_sha256": "test-xml-hash",
        "extraction": "Synthetic canonical text for tests only.",
    }


def test_mask_preserves_every_unmasked_character() -> None:
    """Unicode offsets and punctuation survive exact replacement."""
    sentence = "We compared café samples with controls."
    template, originals = builder.mask_spans(
        sentence, [(12, 24, "noun_phrase"), (30, 38, "noun_phrase")]
    )
    assert template == "We compared {phrase_1} with {phrase_2}."
    assert template.format_map(originals) == sentence


@pytest.mark.parametrize(
    ("sentence", "family"),
    [
        (
            "We found no evidence that the difference was caused by the treatment.",
            "negative_evidence",
        ),
        (
            (
                "To assess the difference, we compared the two groups with matched "
                "controls."
            ),
            "purpose",
        ),
        (
            "However, these results differed from those obtained in the earlier study.",
            "contrast",
        ),
        (
            (
                "These results suggest that the response may depend on the initial "
                "conditions."
            ),
            "interpretation",
        ),
        (
            "We used the same procedure to estimate the difference between the groups.",
            "method",
        ),
        (
            "We observed a clear difference between the groups under these conditions.",
            "observation",
        ),
        (
            "This study is limited by the small number of available samples.",
            "limitation",
        ),
    ],
)
def test_classify_uses_visible_cues(sentence: str, family: str) -> None:
    """Classification follows explicit text cues, without invented claims."""
    assert builder.classify(sentence) == family


@pytest.mark.parametrize(
    "sentence",
    [
        (
            "Fig. 2. We observed this difference between groups under all "
            "experimental conditions."
        ),
        "We observed a difference [12] between the groups under these conditions.",
        "We observed <i>differences</i> between the groups under these conditions.",
        "Table 1 presents the differences between all of the groups in this study.",
    ],
)
def test_rejects_artifact_sentences(sentence: str) -> None:
    """Reference and markup remnants do not become candidate frames."""
    assert not builder.is_clean_sentence(sentence)


def test_ambiguous_sentence_has_no_family() -> None:
    """A sentence without a bounded rhetorical cue is not forced into a family."""
    assert (
        builder.classify("The green trees stood beside the quiet river in the morning.")
        == ""
    )


def test_mask_rejects_overlapping_source_spans() -> None:
    """Invalid spans cannot silently corrupt the source sentence."""
    with pytest.raises(ValueError, match="overlap"):
        builder.mask_spans(
            "A simple example.", [(0, 8, "noun_phrase"), (2, 9, "noun_phrase")]
        )


@pytest.fixture(scope="module")
def nlp():
    """Load the pinned small English parser without network access."""
    return builder.spacy.load("en_core_web_sm")


def test_extract_preserves_negative_claim(nlp) -> None:
    """Negation stays literal and every slot is a source substring."""
    sentence = next(
        nlp(
            "We found no evidence that the difference was caused by the treatment."
        ).sents
    )
    candidate = builder.extract_sentence(sentence)
    assert (
        candidate["template"]
        == "We found no evidence that {phrase_1} was caused by {phrase_2}."
    )
    assert (
        candidate["template"].format_map(candidate["original_slots"]) == sentence.text
    )


def test_rejects_citation_digits_attached_to_words() -> None:
    """XML superscript remnants cannot be disguised as noun slots."""
    assert not builder.is_clean_sentence(
        "We found no evidence that the difference arose from organisms24."
    )


def test_rejects_exposed_domain_adjectives(nlp) -> None:
    """An unmasked domain phrase cannot become a general rhetorical frame."""
    sentence = next(
        nlp(
            "However, with bulk metagenomic sequencing, it is more challenging "
            "to assemble low-abundance viruses because the majority of reads "
            "derive from cellular organisms."
        ).sents
    )
    assert builder.extract_sentence(sentence) == {}


def test_build_candidates_reconstructs_source(tmp_path: Path, nlp) -> None:
    """Candidate text, hashes and code-point offsets all refer to the input."""
    text = "We found no evidence that the difference was caused by the treatment."
    paper = make_paper(tmp_path, text)
    candidate = builder.build_candidates(paper, tmp_path, nlp)[0]
    assert candidate["source"]["authors"] == ["Public Test Author"]
    assert candidate["source"]["xml_sha256"] == "test-xml-hash"
    assert "person or agent" in candidate["review"]["notes"]
    source = candidate["source"]
    assert text[source["start"] : source["end"]] == source["sentence"]
    assert candidate["template"].format_map(candidate["original_slots"]) == text
    assert (
        source["sentence_sha256"]
        == builder.hashlib.sha256(source["sentence"].encode()).hexdigest()
    )
    assert source["extraction"] == paper["extraction"]
    assert candidate["review"]["status"] == "candidate"
    assert candidate["section"] == "Results"


def test_source_hash_mismatch_fails(tmp_path: Path, nlp) -> None:
    """Changed source files cannot produce apparently verified candidates."""
    paper = make_paper(tmp_path, "Original text")
    (tmp_path / "source.txt").write_text("Changed text", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        builder.build_candidates(paper, tmp_path, nlp)


def test_build_ignores_paragraph_space_without_changing_offsets(
    tmp_path: Path, nlp
) -> None:
    """Leading whitespace tokens do not hide a valid second paragraph."""
    text = (
        "A brief introduction.\n\n"
        "We found no evidence that the difference was caused by the treatment."
    )
    paper = make_paper(tmp_path, text, start=23)
    candidate = builder.build_candidates(paper, tmp_path, nlp)[0]
    assert candidate["source"]["start"] == 23
    assert candidate["source"]["sentence"].startswith("We found no evidence")


@pytest.mark.parametrize(
    ("sentence", "family"),
    [
        (
            "Our analysis revealed a clear difference between the two groups.",
            "observation",
        ),
        (
            "We analyzed the samples using the same procedure throughout the study.",
            "method",
        ),
        (
            "We aimed to determine whether the response differed between the groups.",
            "purpose",
        ),
        (
            (
                "Taken together, these results suggest a common origin for these "
                "responses."
            ),
            "interpretation",
        ),
        (
            (
                "It remains unclear whether the difference reflects the "
                "underlying conditions."
            ),
            "limitation",
        ),
    ],
)
def test_expanded_cues_are_explicit(sentence: str, family: str) -> None:
    """Additional families still require a visible rhetorical cue."""
    assert builder.classify(sentence) == family


def test_single_slot_retains_substantial_syntax(nlp) -> None:
    """One noun slot can carry a useful fixed rhetorical structure."""
    sentence = next(
        nlp(
            "These results suggest that the response may be more important "
            "than previously thought."
        ).sents
    )
    candidate = builder.extract_sentence(sentence)
    assert len(candidate["slots"]) == 1
    assert (
        candidate["template"].format_map(candidate["original_slots"]) == sentence.text
    )


def test_complex_frame_allows_six_noun_slots(nlp) -> None:
    """Longer source syntax can retain six independently masked noun phrases."""
    sentence = next(
        nlp(
            "We compared the samples with the controls and the references "
            "across the sites during the seasons using the measurements."
        ).sents
    )
    candidate = builder.extract_sentence(sentence)
    assert len(candidate["slots"]) == 6
    assert (
        candidate["template"].format_map(candidate["original_slots"]) == sentence.text
    )


def test_subject_slot_records_fixed_verb_agreement(nlp) -> None:
    """A fixed singular present-tense verb constrains its source subject slot."""
    sentence = next(
        nlp(
            "The response suggests that the treatment may be more important "
            "than previously thought."
        ).sents
    )
    candidate = builder.extract_sentence(sentence)
    assert candidate["slots"]["phrase_1"]["number"] == "singular"
    assert "suggests that" in candidate["template"]


@pytest.mark.parametrize(
    "heading",
    [
        "Reviewer 2",
        "Reviewers' comments",
        "Author reply",
        "Responses",
        "Decision letter",
        "Peer review",
        "eLife digest",
        "Editorial summary",
    ],
)
def test_editorial_sections_are_excluded(tmp_path: Path, nlp, heading: str) -> None:
    """Peer review text cannot be mistaken for research article prose."""
    text = "We found no evidence that the difference was caused by the treatment."
    paper = make_paper(tmp_path, text, heading=heading)
    assert builder.build_candidates(paper, tmp_path, nlp) == []


@pytest.mark.parametrize(
    "sentence",
    [
        (
            "We observed no difference between the groups when we repeated the "
            "experiment under the same conditions."
        ),
        (
            "We observed a possible difference between the groups when we repeated "
            "the experiment under the same conditions."
        ),
    ],
)
def test_noun_mask_cannot_hide_negation_or_hedge(nlp, sentence: str) -> None:
    """Negation and uncertainty inside noun chunks remain outside candidate slots."""
    candidate = builder.extract_sentence(next(nlp(sentence).sents))
    assert candidate
    assert "difference" in candidate["template"]
    assert candidate["template"].format_map(candidate["original_slots"]) == sentence
    assert (
        "no difference" in candidate["template"]
        or "possible difference" in candidate["template"]
    )


@pytest.mark.parametrize(
    ("sentence", "family"),
    [
        ("Samples were treated with controls before analysis.", "method"),
        ("The samples were subjected to the treatment before analysis.", "method"),
        ("The simulations were rerun with the estimates from the controls.", "method"),
        ("Simulations were performed using the estimates from the samples.", "method"),
        ("The samples were not detected in the controls.", "negative_evidence"),
        (
            "No significant differences were observed between the groups.",
            "negative_evidence",
        ),
        (
            "However, no significant difference was found between the groups.",
            "negative_evidence",
        ),
        ("The analysis could not distinguish between the groups.", "limitation"),
    ],
)
def test_short_expansion_frames_preserve_fixed_predicates(
    nlp, sentence: str, family: str
) -> None:
    """Bounded expansion retains complete predicates and exact source rendering."""
    candidate = builder.extract_sentence(next(nlp(sentence).sents))
    assert candidate["family"] == family
    assert candidate["template"].format_map(candidate["original_slots"]) == sentence


@pytest.mark.parametrize(
    "sentence",
    [
        (
            "We observed no viral effect between the groups when we repeated "
            "the experiment."
        ),
        (
            "We observed a possible genomic difference between the groups "
            "under the same conditions."
        ),
    ],
)
def test_protected_topic_chunks_remain_unsafe(nlp, sentence: str) -> None:
    """Retaining generic protected chunks never admits domain modifiers."""
    assert builder.extract_sentence(next(nlp(sentence).sents)) == {}


def test_short_contrast_is_not_admitted(nlp) -> None:
    """The lower expansion floor does not admit generic short contrast padding."""
    assert (
        builder.extract_sentence(
            next(nlp("However, samples differed from controls in the analysis.").sents)
        )
        == {}
    )


def test_relative_pronoun_remains_fixed(nlp) -> None:
    """A relative pronoun supplies clause syntax rather than replaceable content."""
    sentence = next(
        nlp(
            "We used the same procedure, which was applied to the samples under "
            "the same conditions."
        ).sents
    )
    candidate = builder.extract_sentence(sentence)
    assert ", which was applied" in candidate["template"]
    assert "which" not in candidate["original_slots"].values()


def test_fixed_verb_overrides_wrong_noun_morphology(nlp) -> None:
    """Explicit were wins over an intentionally wrong parser noun-number label."""
    document = nlp(
        "Centiles were calculated for the samples under the same conditions "
        "in the study."
    )
    document[0].set_morph("Number=Sing")
    constraints = builder._slot_constraints(
        next(document.sents), 0, len("Centiles"), "noun_phrase"
    )
    assert constraints["number"] == "plural"


@pytest.mark.parametrize(
    "sentence",
    [
        (
            "We observed a clear difference between the groups "
            "as previously described by ."
        ),
        "We observed a clear difference between the groups under these conditions,.",
        "We observed a clear difference between the groups under these conditions—.",
        'We observed a "clear difference between the groups under these conditions.',
    ],
)
def test_rejects_citation_gaps_and_unmatched_quotes(sentence: str) -> None:
    """Broken citation removal and quotation artifacts are not reusable syntax."""
    assert not builder.is_clean_sentence(sentence)


def test_contrast_connective_stays_fixed(nlp) -> None:
    """The connective carries rhetorical function and is not a content noun slot."""
    sentence = next(
        nlp(
            "In contrast, we observed a clear difference between the groups "
            "when we repeated the experiment under the same conditions."
        ).sents
    )
    candidate = builder.extract_sentence(sentence)
    assert candidate["template"].startswith("In contrast, we observed")
    assert "contrast" not in candidate["original_slots"].values()


def test_scope_modifier_cannot_be_masked(nlp) -> None:
    """Quantifier scope is not hidden in a replaceable noun chunk."""
    document = nlp("We compared only the sample with the control.")
    assert builder._noun_spans(next(document.sents)) == []


@pytest.mark.parametrize(
    "sentence",
    [
        (
            "We found several signals in the samples, but none of these signals "
            "was associated with the treatment."
        ),
        (
            "However, virtually none of the samples were analyzed under the same "
            "conditions when we repeated the experiment."
        ),
    ],
)
def test_none_cannot_disappear_inside_a_noun_slot(nlp, sentence: str) -> None:
    """Negative quantifiers remain protected even when parsed as noun heads."""
    assert builder.extract_sentence(next(nlp(sentence).sents)) == {}


@pytest.mark.parametrize("prefix", ["On the one hand,", "First,", "Second,"])
def test_rhetorical_number_words_stay_fixed(nlp, prefix: str) -> None:
    """Ordinal discourse cues are fixed wording, not replaceable numeric values."""
    sentence = next(
        nlp(
            f"{prefix} these results suggest that the response may depend "
            "on the initial conditions."
        ).sents
    )
    candidate = builder.extract_sentence(sentence)
    assert candidate["template"].startswith(prefix)
    assert not any(slot["type"] == "number" for slot in candidate["slots"].values())


def test_multiword_relative_chunk_is_rejected(nlp) -> None:
    """A relative determiner cannot disappear inside a masked noun phrase."""
    sentence = next(
        nlp(
            "We observed a clear difference between the groups, whose members were "
            "sampled under the same conditions."
        ).sents
    )
    assert any(chunk.text == "whose members" for chunk in sentence.noun_chunks)
    assert builder.extract_sentence(sentence) == {}


@pytest.mark.parametrize(
    "sentence",
    [
        "However, few agents have been well characterized in the available studies.",
        "However, there is still a general lack of measurements for the samples.",
        "We observed little variation between the groups under the same conditions.",
    ],
)
def test_negative_quantity_cannot_be_hidden(nlp, sentence: str) -> None:
    """Negative quantity and absence heads cannot become replaceable topic nouns."""
    assert builder.extract_sentence(next(nlp(sentence).sents)) == {}


@pytest.mark.parametrize(
    ("sentence", "connective"),
    [
        (
            (
                "We observed a clear difference in the samples in response to "
                "the treatment."
            ),
            "in response to",
        ),
        (
            (
                "Samples were analyzed using the same procedure with the exception "
                "of the controls."
            ),
            "with the exception of",
        ),
        (
            (
                "Despite the fact that the samples differed, we used the same "
                "procedure for the controls."
            ),
            "the fact that",
        ),
    ],
)
def test_connective_heads_remain_fixed(nlp, sentence: str, connective: str) -> None:
    """A connective must not require one special noun as a slot fill."""
    candidate = builder.extract_sentence(next(nlp(sentence).sents))
    assert candidate
    assert connective in candidate["template"]
    assert candidate["template"].format_map(candidate["original_slots"]) == sentence


@pytest.mark.parametrize(
    "sentence",
    [
        "We observed a higher frequency in the samples than the controls.",
        "We observed a distinct pattern from the controls in the samples.",
        (
            "Reference and Test sequences were obtained in 26/30 and 9/30 samples, "
            "respectively, as well as in the control."
        ),
    ],
)
def test_relations_cannot_depend_on_hidden_modifiers(nlp, sentence: str) -> None:
    """Comparative and paired-list syntax must remain visible in the framework."""
    assert builder.extract_sentence(next(nlp(sentence).sents)) == {}


def test_little_is_rejected_before_fixed_word_floor(nlp) -> None:
    """A short sentence must fail because of hidden quantity, not its word count."""
    parsed = next(nlp("We observed little variation between the groups.").sents)
    assert builder._noun_spans(parsed) == []


@pytest.mark.parametrize(
    "sentence",
    [
        "We observed a higher frequency in the samples than the controls.",
        "We observed a distinct pattern from the controls in the samples.",
        (
            "Reference and Test sequences were obtained in 26/30 and 9/30 samples, "
            "respectively, as well as in the control."
        ),
    ],
)
def test_hidden_relation_fails_literal_guard(nlp, sentence: str) -> None:
    """Exercise the relation guard before independent extraction length filters."""
    parsed = next(nlp(sentence).sents)
    spans = builder._noun_spans(parsed)
    assert spans
    assert not builder._safe_literals(parsed, spans)


def test_complete_fixed_comparison_remains_eligible(nlp) -> None:
    """A fixed higher-than relation must survive the new comparative guard."""
    sentence = (
        "We found that the values were higher than the estimates "
        "under the same conditions."
    )
    candidate = builder.extract_sentence(next(nlp(sentence).sents))
    assert candidate
    assert "higher than" in candidate["template"]
    assert candidate["template"].format_map(candidate["original_slots"]) == sentence


@pytest.mark.parametrize(
    ("sentence", "phrase", "number"),
    [
        (
            "We used the procedure that was applied to all samples.",
            "the procedure",
            "singular",
        ),
        (
            "We used the procedures that were applied to all samples.",
            "the procedures",
            "plural",
        ),
        (
            "However, there are differences between the groups under these conditions.",
            "differences",
            "plural",
        ),
    ],
)
def test_clear_relative_and_existential_agreement(
    nlp, sentence: str, phrase: str, number: str
) -> None:
    """Unambiguous fixed relative/existential verbs constrain the antecedent noun."""
    parsed = next(nlp(sentence).sents)
    start = sentence.index(phrase)
    assert (
        builder._slot_constraints(parsed, start, start + len(phrase), "noun_phrase")[
            "number"
        ]
        == number
    )


def test_multiple_parser_subjects_do_not_produce_number_hints(nlp) -> None:
    """A known ambiguous parse must not constrain the object of after as a subject."""
    sentence = (
        "The branches after the calibration points largely represent host evolution."
    )
    parsed = next(nlp(sentence).sents)
    phrase = "the calibration points"
    start = sentence.index(phrase)
    assert "number" not in builder._slot_constraints(
        parsed, start, start + len(phrase), "noun_phrase"
    )


@pytest.mark.parametrize(
    ("sentence", "phrase"),
    [
        (
            (
                "The levels for each lane, which were estimated with an antibody, "
                "were used as controls."
            ),
            "each lane",
        ),
        (
            (
                "The products contain helices, which suggests that they may "
                "act as controls."
            ),
            "helices",
        ),
    ],
)
def test_ambiguous_relative_antecedent_has_no_number_hint(
    nlp, sentence: str, phrase: str
) -> None:
    """A parenthetical clause may attach to an earlier noun or the entire claim."""
    start = sentence.index(phrase)
    assert "number" not in builder._slot_constraints(
        next(nlp(sentence).sents), start, start + len(phrase), "noun_phrase"
    )


@pytest.mark.parametrize(
    "heading", ["Stable isotope methods", "Preference results", "Author summary"]
)
def test_scientific_section_substrings_are_not_editorial(
    tmp_path: Path, nlp, heading: str
) -> None:
    """Whole words distinguish editorial sections from ordinary scientific headings."""
    paper = make_paper(
        tmp_path,
        "We found no evidence that the difference was caused by the treatment.",
        heading=heading,
    )
    assert len(builder.build_candidates(paper, tmp_path, nlp)) == 1


def test_missing_required_attribution_fails_before_extraction(
    tmp_path: Path, nlp
) -> None:
    """A source without the required public author attribution is incomplete."""
    paper = make_paper(tmp_path, "This text has no recognized cue.")
    del paper["authors"]
    with pytest.raises((KeyError, ValueError), match="authors"):
        builder.build_candidates(paper, tmp_path, nlp)


def test_report_hashes_manifest_bytes_used_for_processing(
    tmp_path: Path, nlp, monkeypatch
) -> None:
    """Concurrent manifest edits cannot replace provenance of the bytes processed."""
    paper = make_paper(tmp_path, "This synthetic sentence has no extraction cue.")
    manifest = tmp_path / "manifest.jsonl"
    original = (json.dumps(paper) + "\n").encode()
    manifest.write_bytes(original)
    output = tmp_path / "candidates.jsonl"

    def mutate_manifest(*_args, **_kwargs) -> list:
        manifest.write_text("changed during processing\n", encoding="utf-8")
        return []

    monkeypatch.setattr(builder, "build_candidates", mutate_manifest)
    monkeypatch.setattr(builder.spacy, "load", lambda _name: nlp)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_scaffolds",
            "--manifest",
            str(manifest),
            "--corpus-root",
            str(tmp_path),
            "--output",
            str(output),
        ],
    )
    assert builder.main() == 0
    report = json.loads(output.with_suffix(".report.json").read_text(encoding="utf-8"))
    assert report["manifest_sha256"] == builder.hashlib.sha256(original).hexdigest()
    assert "accepted" not in report
    assert "accepted" not in report["papers"][0]


def test_modal_have_does_not_impose_plural_agreement(nlp) -> None:
    """A modal perfect carries no subject-number cue on bare have."""
    sentence = next(
        nlp("The organism may have acquired the gene during infection.").sents
    )
    constraints = builder._slot_constraints(
        sentence, 0, len("The organism"), "noun_phrase"
    )
    assert "number" not in constraints
