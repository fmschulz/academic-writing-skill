"""Exercise the scaffold CLI at its file boundary with temporary fixtures."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scaffolds.py"


class ScaffoldCommandsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bank = self.root / "bank.jsonl"
        sentence = "We observed no evidence of contamination."
        self.record = {
            "id": "test-negative-1",
            "family": "negative_evidence",
            "section": "Results",
            "template": "We observed no evidence of {entity}.",
            "slots": {"entity": {"type": "noun_phrase", "max_words": 6}},
            "original_slots": {"entity": "contamination"},
            "source": {
                "paper_id": "test-paper",
                "doi": "10.1234/test",
                "year": 2020,
                "title": "Temporary test fixture",
                "license": "CC-BY-4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "authors": ["Test Author"],
                "path": "source.txt",
                "sentence": sentence,
                "sentence_sha256": hashlib.sha256(sentence.encode()).hexdigest(),
                "text_sha256": hashlib.sha256(sentence.encode()).hexdigest(),
                "start": 0,
                "end": len(sentence),
            },
            "review": {"status": "accepted", "method": "test fixture", "notes": ""},
        }
        self.write_bank()
        (self.root / "source.txt").write_text(sentence, encoding="utf-8")
        (self.root / "draft.md").write_text(
            "\u03b1\r\nOld claim.\r\nEnd.", encoding="utf-8"
        )
        self.requests = [
            {
                "start": 3,
                "end": 13,
                "original": "Old claim.",
                "id": "test-negative-1",
                "slots": {"entity": "viral transfer"},
            }
        ]
        self.write_json("requests.json", self.requests)

    def write_bank(self):
        self.bank.write_text(
            json.dumps(self.record, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def set_frame(self, template, kind, original):
        self.record["template"] = template
        self.record["slots"] = {"entity": {"type": kind, "max_words": 6}}
        self.record["original_slots"] = {"entity": original}
        source = json.loads(json.dumps(self.record["source"]))
        sentence = template.format(entity=original)
        source.update(
            sentence=sentence,
            end=len(sentence),
            sentence_sha256=hashlib.sha256(sentence.encode()).hexdigest(),
        )
        self.record["source"] = source
        self.write_bank()

    def write_json(self, name, payload):
        (self.root / name).write_text(json.dumps(payload), encoding="utf-8")

    def cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--bank", str(self.bank), *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def apply(self):
        return self.cli(
            "apply",
            "--draft",
            "draft.md",
            "--requests",
            "requests.json",
            "--output",
            "out.md",
            "--receipt",
            "receipt.json",
        )

    def write_review(self) -> None:
        """Record a fixture review tied to the current apply receipt."""
        receipt = json.loads((self.root / "receipt.json").read_text(encoding="utf-8"))
        self.write_json(
            "review.json",
            {
                "version": 1,
                "initial": {
                    "sha256": receipt["input_sha256"],
                    "reviewer": "self-review: fixture",
                    "findings": [],
                },
                "final": {
                    "sha256": receipt["output_sha256"],
                    "reviewer": "self-review: fixture",
                    "notes": {
                        "meaning": "Fixture facts preserved.",
                        "readability": "Plain sentence checked.",
                        "flow": "Paragraph checked.",
                        "style": "Genre checked.",
                    },
                    "findings": [],
                },
            },
        )

    def check(self):
        if not (self.root / "review.json").exists():
            self.write_review()
        return self.cli(
            "check",
            "--draft",
            "out.md",
            "--receipt",
            "receipt.json",
            "--review",
            "review.json",
        )

    def test_check_requires_review(self) -> None:
        """A text receipt alone cannot complete the CLI check."""
        self.assertEqual(self.apply().returncode, 0)
        checked = self.cli("check", "--draft", "out.md", "--receipt", "receipt.json")
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn("--review", checked.stderr)

    def test_review_rejects_stale_hashes_and_unresolved_final_findings(self) -> None:
        """Initial and final reviews must match and have resolved dispositions."""
        self.assertEqual(self.apply().returncode, 0)
        for phase in ("initial", "final"):
            with self.subTest(phase=phase):
                self.write_review()
                review = json.loads((self.root / "review.json").read_text())
                review[phase]["sha256"] = "0" * 64
                self.write_json("review.json", review)
                checked = self.check()
                self.assertNotEqual(checked.returncode, 0)
                self.assertIn("review hash mismatch", checked.stderr)
        for disposition in ("open", "fixed"):
            with self.subTest(disposition=disposition):
                self.write_review()
                review = json.loads((self.root / "review.json").read_text())
                review["final"]["findings"] = [
                    {
                        "quote": "Old claim.",
                        "issue": "Unclear scope",
                        "disposition": disposition,
                        "reason": "Requires another review.",
                    }
                ]
                self.write_json("review.json", review)
                checked = self.check()
                self.assertNotEqual(checked.returncode, 0)
                self.assertIn("disposition", checked.stderr)

    def test_review_requires_complete_notes_identity_and_valid_schema(self) -> None:
        """Reject incomplete audit records at the CLI boundary."""
        self.assertEqual(self.apply().returncode, 0)
        cases = [
            (("final", "notes"), None, "notes"),
            (("final", "notes", "flow"), " ", "flow must be a string"),
            (("final", "reviewer"), " ", "reviewer must be a string"),
            (("version",), 2, "review version must be 1"),
            (
                ("initial", "findings"),
                [
                    {
                        "quote": "Old claim.",
                        "issue": "Scope unclear",
                        "disposition": "ignored",
                        "reason": "Invalid status fixture.",
                    }
                ],
                "invalid review finding disposition",
            ),
        ]
        for keys, value, diagnostic in cases:
            with self.subTest(keys=keys):
                self.write_review()
                review = json.loads((self.root / "review.json").read_text())
                field = review
                for key in keys[:-1]:
                    field = field[key]
                if value is None:
                    del field[keys[-1]]
                else:
                    field[keys[-1]] = value
                self.write_json("review.json", review)
                checked = self.check()
                self.assertNotEqual(checked.returncode, 0)
                self.assertIn(diagnostic, checked.stderr)

    def test_reviewed_zero_fit_retains_source_gap_and_detects_tampering(self) -> None:
        """Zero replacements still require review and exact input/output bytes."""
        self.write_json("requests.json", [])
        applied = self.apply()
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.write_review()
        review = json.loads((self.root / "review.json").read_text())
        review["final"]["findings"] = [
            {
                "quote": "Old claim.",
                "issue": "Scope missing",
                "disposition": "residual",
                "reason": "Source lacks scope; disclosed to author.",
            }
        ]
        self.write_json("review.json", review)
        checked = self.check()
        self.assertEqual(checked.returncode, 0, checked.stderr)
        evidence = json.loads(checked.stdout)
        self.assertTrue(evidence["review_record_checked"])
        self.assertEqual(evidence["residual_findings"], 1)
        self.assertEqual(evidence["replacements_checked"], 0)
        self.assertEqual(
            (self.root / "draft.md").read_bytes(), (self.root / "out.md").read_bytes()
        )
        (self.root / "out.md").write_text("Changed.", encoding="utf-8")
        checked = self.check()
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn("output file hash mismatch", checked.stderr)

    def test_apply_check_preserves_literal_text_and_source_receipt(self):
        applied = self.apply()
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(
            (self.root / "out.md").read_bytes(),
            "\u03b1\r\nWe observed no evidence of viral transfer.\r\nEnd.".encode(),
        )
        checked = self.check()
        self.assertEqual(checked.returncode, 0, checked.stderr)
        receipt = json.loads((self.root / "receipt.json").read_text())
        self.assertEqual(receipt["replacements"][0]["source"], self.record["source"])

    def test_check_rejects_word_punctuation_slot_and_bank_drift(self):
        self.assertEqual(self.apply().returncode, 0)
        original = (self.root / "out.md").read_bytes()
        receipt = json.loads((self.root / "receipt.json").read_text(encoding="utf-8"))
        for before, after in [
            (b"observed", b"found"),
            (b"transfer.", b"transfer!"),
            (b"viral", b"bacterial"),
        ]:
            with self.subTest(after=after):
                changed = original.replace(before, after)
                (self.root / "out.md").write_bytes(changed)
                receipt["output_sha256"] = hashlib.sha256(changed).hexdigest()
                self.write_json("receipt.json", receipt)
                checked = self.check()
                self.assertNotEqual(checked.returncode, 0)
                self.assertIn("differ from template", checked.stderr)
        (self.root / "out.md").write_bytes(original)
        receipt["output_sha256"] = hashlib.sha256(original).hexdigest()
        self.write_json("receipt.json", receipt)
        self.record["review"] = {
            "status": "accepted",
            "method": "test fixture",
            "notes": "changed",
        }
        self.write_bank()
        checked = self.check()
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn("bank hash mismatch", checked.stderr)

    def test_render_rejects_missing_extra_and_clause_slots(self):
        for slots, diagnostic in [
            ({}, "missing or extra slots"),
            ({"entity": "transfer", "extra": "x"}, "missing or extra slots"),
            ({"entity": "we found no evidence"}, "possible clause"),
            ({"entity": "transfer because contamination"}, "possible clause"),
            ({"entity": "transfer whereas contamination"}, "possible clause"),
            ({"entity": "transfer although contamination"}, "possible clause"),
            ({"entity": "transfer which increased"}, "possible clause"),
            ({"entity": "transfer; we conclude otherwise"}, "phrase limits"),
            ({"entity": "one two three four five six seven"}, "phrase limits"),
            ({"entity": "transfer\u200b"}, "control or format"),
            ({"entity": "trans\u2028fer"}, "control or format"),
            ({"entity": "transfer while sampling"}, "possible clause"),
            ({"entity": "transfer that increased fitness"}, "possible clause"),
        ]:
            with self.subTest(slots=slots):
                self.write_json("slots.json", slots)
                rendered = self.cli(
                    "render", "--id", "test-negative-1", "--slots", "slots.json"
                )
                self.assertNotEqual(rendered.returncode, 0)
                self.assertIn(diagnostic, rendered.stderr)

    def test_scientific_slot_forms_are_renderable_including_source_values(self):
        for kind, original in [
            ("noun_phrase", "type I interferon"),
            ("noun_phrase", "IS elements"),
            ("noun_phrase", "E. coli"),
            ("noun_phrase", "that process"),
            ("reference", "Smith et al. 2020"),
            ("reference", "Fig. 2"),
            ("number", "1,000"),
            ("number", "50%"),
            ("number", "\u22122"),
        ]:
            with self.subTest(original=original):
                self.set_frame("We examined {entity}.", kind, original)
                self.write_json("slots.json", {"entity": original})
                rendered = self.cli(
                    "render", "--id", "test-negative-1", "--slots", "slots.json"
                )
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                self.assertEqual(rendered.stdout, f"We examined {original}.\n")

    def test_reference_slots_accept_urls_without_loosening_phrase_guards(self):
        self.set_frame("Records can be accessed at {entity}.", "reference", "[18]")
        for address in [
            "https://biocode-arena.newlineages.com",
            "http://example.org:8080/records?method=we&version=2#results",
        ]:
            with self.subTest(address=address):
                self.write_json("slots.json", {"entity": address})
                rendered = self.cli(
                    "render", "--id", "test-negative-1", "--slots", "slots.json"
                )
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                self.assertEqual(
                    rendered.stdout, f"Records can be accessed at {address}.\n"
                )
        for address in [
            "https://example.org and we conclude otherwise",
            "https://example.org/\nResults",
            "https://user:password@example.org",
            "https:///missing-host",
            "https://example.org:invalid",
            "https://example.org/{clause}",
            "https://example.org/records.",
            "https://a.example,https://b.example",
            "https://.",
            "ftp://example.org/records",
        ]:
            with self.subTest(address=address):
                self.write_json("slots.json", {"entity": address})
                rendered = self.cli(
                    "render", "--id", "test-negative-1", "--slots", "slots.json"
                )
                self.assertNotEqual(rendered.returncode, 0)
        self.set_frame("We examined {entity}.", "noun_phrase", "the records")
        self.write_json("slots.json", {"entity": "https://example.org"})
        self.assertNotEqual(
            self.cli(
                "render", "--id", "test-negative-1", "--slots", "slots.json"
            ).returncode,
            0,
        )

    def test_bank_rejects_unrenderable_originals_and_templates_without_fixed_words(
        self,
    ):
        self.set_frame("We examined {entity}.", "number", "many")
        audited = self.cli("audit-bank")
        self.assertNotEqual(audited.returncode, 0)
        self.assertIn("numeric string", audited.stderr)
        self.set_frame("{entity}.", "noun_phrase", "contamination")
        audited = self.cli("audit-bank")
        self.assertNotEqual(audited.returncode, 0)
        self.assertIn("fixed literal words", audited.stderr)

    def test_jsonl_allows_unicode_line_separator_in_metadata(self):
        self.record["review"] = {
            "status": "accepted",
            "method": "test",
            "notes": "a\u2028b",
        }
        self.write_bank()
        audited = self.cli("audit-bank")
        self.assertEqual(audited.returncode, 0, audited.stderr)

    def test_unknown_id_and_output_alias_fail_without_clobber(self):
        self.write_json("slots.json", {"entity": "transfer"})
        rendered = self.cli("render", "--id", "missing", "--slots", "slots.json")
        self.assertNotEqual(rendered.returncode, 0)
        self.assertIn("unknown scaffold ID: missing", rendered.stderr)
        original = (self.root / "draft.md").read_bytes()
        applied = self.cli(
            "apply",
            "--draft",
            "draft.md",
            "--requests",
            "requests.json",
            "--output",
            "draft.md",
            "--receipt",
            "receipt.json",
        )
        self.assertNotEqual(applied.returncode, 0)
        self.assertIn("distinct", applied.stderr)
        self.assertEqual((self.root / "draft.md").read_bytes(), original)

    def test_check_verifies_literals_even_if_output_hash_is_updated(self):
        self.assertEqual(self.apply().returncode, 0)
        changed = (self.root / "out.md").read_bytes().replace(b"observed", b"detected")
        (self.root / "out.md").write_bytes(changed)
        receipt = json.loads((self.root / "receipt.json").read_text(encoding="utf-8"))
        receipt["output_sha256"] = hashlib.sha256(changed).hexdigest()
        self.write_json("receipt.json", receipt)
        checked = self.check()
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn("differ from template", checked.stderr)

    def test_apply_records_shifted_offsets_for_multiple_replacements(self):
        self.requests.append(
            {
                "start": 15,
                "end": 19,
                "original": "End.",
                "id": "test-negative-1",
                "slots": {"entity": "transfer"},
            }
        )
        self.write_json("requests.json", self.requests)
        applied = self.apply()
        self.assertEqual(applied.returncode, 0, applied.stderr)
        checked = self.check()
        self.assertEqual(checked.returncode, 0, checked.stderr)
        receipt = json.loads((self.root / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["replacements"][1]["start"], 47)

    def test_audit_rejects_duplicate_ids_candidate_status_and_undeclared_slots(self):
        with self.bank.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self.record) + "\n")
        audited = self.cli("audit-bank")
        self.assertNotEqual(audited.returncode, 0)
        self.assertIn("duplicate ID", audited.stderr)
        self.record["review"] = {"status": "candidate", "method": "test", "notes": ""}
        self.write_bank()
        audited = self.cli("audit-bank")
        self.assertNotEqual(audited.returncode, 0)
        self.assertIn("review.status=accepted", audited.stderr)
        self.record["review"] = {"status": "accepted", "method": "test", "notes": ""}
        self.record["template"] = "We observed {undeclared}."
        self.write_bank()
        audited = self.cli("audit-bank")
        self.assertNotEqual(audited.returncode, 0)
        self.assertIn("match declared slots", audited.stderr)

    def test_apply_rejects_overlaps_and_changed_original(self):
        self.write_json("requests.json", self.requests * 2)
        self.assertNotEqual(self.apply().returncode, 0)
        self.requests[0]["original"] = "New claim."
        self.write_json("requests.json", self.requests)
        self.assertNotEqual(self.apply().returncode, 0)
        self.assertFalse((self.root / "out.md").exists())

    def test_audit_checks_reconstruction_and_optional_source_bytes(self):
        audited = self.cli("audit-bank", "--corpus-root", str(self.root))
        self.assertEqual(audited.returncode, 0, audited.stderr)
        (self.root / "source.txt").write_text("Changed source", encoding="utf-8")
        audited = self.cli("audit-bank", "--corpus-root", str(self.root))
        self.assertNotEqual(audited.returncode, 0)
        self.assertIn("source file hash mismatch", audited.stderr)
        self.assertEqual(self.cli("audit-bank").returncode, 0)
        self.record["original_slots"] = {"entity": "something else"}
        self.write_bank()
        audited = self.cli("audit-bank")
        self.assertNotEqual(audited.returncode, 0)
        self.assertIn("source reconstruction failed", audited.stderr)

    def add_search_frame(
        self,
        identifier: str,
        template: str,
        originals: dict[str, str],
        *,
        notes: str = "",
    ) -> None:
        """Append a complete JSONL record with exact source reconstruction."""
        record = json.loads(json.dumps(self.record))
        sentence = template.format_map(originals)
        record.update(id=identifier, template=template, original_slots=originals)
        record["slots"] = {
            name: {"type": "noun_phrase", "max_words": 6} for name in originals
        }
        record["review"]["notes"] = notes
        record["source"].update(
            sentence=sentence,
            end=len(sentence),
            sentence_sha256=hashlib.sha256(sentence.encode()).hexdigest(),
        )
        with self.bank.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def test_search_prioritizes_predicates_over_source_topics(self) -> None:
        """One fixed predicate outranks several masked source topic matches."""
        self.add_search_frame(
            "topic", "We studied {entity}.", {"entity": "alpha beta gamma"}
        )
        self.add_search_frame(
            "predicate", "We compared {entity}.", {"entity": "groups"}
        )
        listed = self.cli("list", "--query", "comparing alpha beta gamma")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        page = json.loads(listed.stdout)
        self.assertEqual(page["total"], 2)
        self.assertEqual([row["id"] for row in page["records"]], ["predicate", "topic"])
        evidence = page["records"][0]["search"]
        self.assertEqual(evidence["score"], [1, 0, 1])
        self.assertEqual(evidence["matched_terms"], ["compare"])
        self.assertEqual(evidence["matched_fields"]["fixed"], ["compare"])
        self.assertEqual(
            page["records"][1]["search"]["matched_fields"]["source"],
            ["alpha", "beta", "gamma"],
        )

    def test_search_filters_paginate_and_break_ties_deterministically(self) -> None:
        """Filters precede pagination and equal lexical hits prefer simpler frames."""
        self.add_search_frame("b", "We compared {entity}.", {"entity": "groups"})
        self.add_search_frame("a", "We compared {entity}.", {"entity": "samples"})
        self.add_search_frame(
            "complex",
            "We compared {entity} with {other}.",
            {"entity": "groups", "other": "samples"},
        )
        listed = self.cli(
            "list",
            "--query",
            "compare",
            "--max-slots",
            "1",
            "--max-template-words",
            "3",
            "--limit",
            "1",
            "--offset",
            "1",
        )
        self.assertEqual(listed.returncode, 0, listed.stderr)
        page = json.loads(listed.stdout)
        self.assertEqual(page["total"], 2)
        self.assertEqual([row["id"] for row in page["records"]], ["b"])
        self.assertEqual(
            listed.stdout,
            self.cli(
                "list",
                "--query",
                "compare",
                "--max-slots",
                "1",
                "--max-template-words",
                "3",
                "--limit",
                "1",
                "--offset",
                "1",
            ).stdout,
        )
        self.assertNotEqual(self.cli("list", "--max-slots", "0").returncode, 0)
        self.assertNotEqual(
            self.cli("list", "--max-template-words", "-1").returncode, 0
        )

    def test_search_treats_query_as_data_and_preserves_negation(self) -> None:
        """Regex punctuation cannot match everything or hide a negative predicate."""
        self.assertEqual(
            json.loads(self.cli("list", "--query", ".* [").stdout)["total"], 0
        )
        self.assertEqual(
            json.loads(self.cli("list", "--query", "zzzzunmatched").stdout)["total"], 0
        )
        page = json.loads(
            self.cli("list", "--query", "no evidence $(touch marker)").stdout
        )
        self.assertEqual(page["total"], 1)
        self.assertIn("no", page["query_terms"])
        self.assertFalse((self.root / "marker").exists())

    def test_search_normalizes_procedure_inflections_and_keeps_negation(self) -> None:
        """Infinitive queries find past-tense predicates without losing negation."""
        self.add_search_frame(
            "procedure",
            "We simulated {entity} but did not calibrate {other}.",
            {"entity": "groups", "other": "samples"},
        )
        page = json.loads(self.cli("list", "--query", "simulate calibrated not").stdout)
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["query_terms"], ["calibrate", "not", "simulate"])
        self.assertEqual(
            page["records"][0]["search"]["matched_fields"]["fixed"],
            ["calibrate", "not", "simulate"],
        )

    def test_search_does_not_count_family_as_lexical_evidence(self) -> None:
        """A family label cannot create a match or inflate the fixed-text tier."""
        self.assertEqual(
            json.loads(self.cli("list", "--query", "negative").stdout)["total"], 0
        )
        page = json.loads(self.cli("list", "--query", "evidence").stdout)
        self.assertNotIn("family", page["records"][0]["search"]["matched_fields"])
        self.assertEqual(
            json.loads(self.cli("list", "--family", "negative_evidence").stdout)[
                "total"
            ],
            1,
        )

    def test_search_finds_common_extraction_and_collection_predicates(self) -> None:
        """Infinitive queries find selected cue verbs in their past-tense forms."""
        self.add_search_frame(
            "process", "We collected and extracted {entity}.", {"entity": "samples"}
        )
        self.add_search_frame(
            "identify", "We found and identified {entity}.", {"entity": "targets"}
        )
        self.add_search_frame(
            "obtain",
            "We ran {entity} and obtained {other}.",
            {"entity": "analyses", "other": "results"},
        )
        page = json.loads(
            self.cli(
                "list", "--query", "find identify obtain extract collect run"
            ).stdout
        )
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["records"][0]["search"]["score"][0], 2)

    def test_search_reads_notes_and_source_without_equating_actions(self) -> None:
        """Masked topics and restrictions remain visible as distinct evidence."""
        self.add_search_frame(
            "exposed",
            "We exposed {entity}.",
            {"entity": "cultures"},
            notes="Requires irradiation",
        )
        self.assertEqual(
            json.loads(self.cli("list", "--query", "treated").stdout)["total"], 0
        )
        page = json.loads(self.cli("list", "--query", "irradiation cultures").stdout)
        self.assertEqual(
            page["records"][0]["search"]["matched_fields"],
            {"notes": ["irradiation"], "source": ["cultures"]},
        )
        self.assertEqual(
            json.loads(self.cli("list", "--query", "entity").stdout)["total"], 0
        )

    def test_list_alternatives_and_export_are_deterministic(self):
        source = json.loads(json.dumps(self.record["source"]))
        source["doi"] = "10.1234/test<part>#id"
        self.record["source"] = source
        self.write_bank()
        alternative = dict(self.record, id="test-negative-2")
        with self.bank.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(alternative) + "\n")
            handle.write(json.dumps(dict(self.record, id="test-negative-3")) + "\n")
        listed = self.cli(
            "list",
            "--family",
            "negative_evidence",
            "--section",
            "Results",
            "--exclude",
            "test-negative-1",
            "--limit",
            "1",
            "--offset",
            "1",
        )
        self.assertEqual(listed.returncode, 0, listed.stderr)
        page = json.loads(listed.stdout)
        self.assertEqual(page["total"], 2)
        self.assertEqual([row["id"] for row in page["records"]], ["test-negative-3"])
        self.assertEqual(
            page["records"][0]["slots"],
            {
                "entity": {"type": "noun_phrase", "max_words": 6, "number": "any"},
            },
        )
        self.assertEqual(
            page["records"][0]["source"],
            {
                "doi": "10.1234/test<part>#id",
                "year": 2020,
                "paper_id": "test-paper",
            },
        )
        default_page = json.loads(self.cli("list").stdout)
        self.assertEqual(default_page["limit"], 20)
        self.assertEqual(default_page["offset"], 0)
        self.assertEqual(default_page["records"][0]["id"], "test-negative-1")
        self.assertNotIn("query_terms", default_page)
        self.assertNotIn("search", default_page["records"][0])
        self.assertNotEqual(self.cli("list", "--limit", "0").returncode, 0)
        self.assertNotEqual(self.cli("list", "--offset", "-1").returncode, 0)
        self.assertEqual(
            self.cli("export-mcp", "--output", "export.jsonl").returncode, 0
        )
        exported = (self.root / "export.jsonl").read_bytes()
        self.assertEqual(
            self.cli("export-mcp", "--output", "export.jsonl").returncode, 0
        )
        self.assertEqual(exported, (self.root / "export.jsonl").read_bytes())
        first = json.loads(exported.splitlines()[0])
        self.assertGreater(first["id"], 0)
        self.assertEqual(first["canonical_id"], "test-negative-1")
        self.assertEqual(first["type"], "post")
        self.assertEqual(first["copy_blocks"], [])
        self.assertFalse(first["nsfw"])
        self.assertEqual(first["url"], "https://doi.org/10.1234/test%3Cpart%3E%23id")
        self.assertIn("Test Author", first["text"])
        self.assertIn("Temporary test fixture", first["text"])
        self.assertIn("CC-BY-4.0", first["text"])
        self.assertIn("https://creativecommons.org/licenses/by/4.0/", first["text"])

    def test_exported_text_preserves_frame_id_and_use_restrictions_for_render(self):
        self.record["review"] = {
            "status": "accepted",
            "method": "AI editorial review",
            "notes": "State the search sensitivity; absence is not disproof.",
        }
        self.write_bank()
        listed = self.cli("list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        selected = json.loads(listed.stdout)["records"][0]
        self.assertEqual(
            selected["usage_notes"],
            "State the search sensitivity; absence is not disproof.",
        )
        exported = self.cli("export-mcp", "--output", "export.jsonl")
        self.assertEqual(exported.returncode, 0, exported.stderr)
        exported_text = json.loads(
            (self.root / "export.jsonl").read_text(encoding="utf-8")
        )["text"]
        fields = dict(
            line.split(": ", 1) for line in exported_text.split("\n") if ": " in line
        )
        self.assertEqual(fields["Frame-ID"], "test-negative-1")
        self.assertEqual(fields["Use"], selected["usage_notes"])
        self.write_json("slots.json", {"entity": "viral transfer"})
        rendered = self.cli(
            "render", "--id", fields["Frame-ID"], "--slots", "slots.json"
        )
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(
            rendered.stdout, "We observed no evidence of viral transfer.\n"
        )


if __name__ == "__main__":
    unittest.main()
