"""RespLLM architecture, ICBHI splits, and a real smoke-training run."""
import os
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.respiratory.data.icbhi import (
    class_weights_from_labels,
    discover_cycles,
    parse_annotation_file,
    patient_id_from_filename,
    patient_independent_split,
)
from ml.respiratory.models.respllm import RESPIRATORY_CLASSES, RespLLM, count_parameters
from ml.respiratory.training.train import train_respiratory_model


class TestRespLLM(unittest.TestCase):
    def test_encoder_shapes(self):
        import torch
        model = RespLLM()
        mel = torch.randn(2, 1, 64, 128)
        logits, embedding = model.encode(mel)
        self.assertEqual(tuple(logits.shape), (2, 4))
        self.assertEqual(tuple(embedding.shape), (2, 768))
        self.assertGreater(count_parameters(model), 100_000)
        self.assertLess(count_parameters(model), 5_000_000)

    def test_closed_vocab_generation_stays_in_vocab(self):
        import torch
        model = RespLLM()
        model.eval()
        mel = torch.randn(1, 1, 64, 128)
        with torch.no_grad():
            _, embedding = model.encode(mel)
            tokens = model.generate(embedding, max_len=8)
        self.assertTrue(torch.all((tokens >= 0) & (tokens < model.vocab_size)))

    def test_icbhi_annotation_and_patient_split(self):
        self.assertEqual(patient_id_from_filename("226_1b1_Al_sc_Meditron.wav"), "226")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for patient, label_bits in (("101", (0, 0)), ("102", (1, 0)), ("103", (0, 1)), ("104", (1, 1))):
                wav = root / f"{patient}_1b1_Al_sc_Meditron.wav"
                txt = wav.with_suffix(".txt")
                with wave.open(str(wav), "w") as handle:
                    handle.setnchannels(1)
                    handle.setsampwidth(2)
                    handle.setframerate(16000)
                    handle.writeframes((np.zeros(16000, dtype=np.int16)).tobytes())
                crackle, wheeze = label_bits
                txt.write_text(f"0.1 0.9 {crackle} {wheeze}\n", encoding="utf-8")
            cycles = discover_cycles(root)
            self.assertEqual(len(cycles), 4)
            self.assertEqual(
                sorted(c["label_name"] for c in cycles),
                ["both", "crackle", "normal", "wheeze"],
            )
            train, test, meta = patient_independent_split(cycles, test_ratio=0.5, seed=1)
            self.assertEqual(set(meta["train_patients"]) & set(meta["test_patients"]), set())
            self.assertTrue(train and test)

    def test_class_weights_favor_rare_labels(self):
        weights = class_weights_from_labels([0, 0, 0, 0, 1])
        self.assertGreater(weights[1], weights[0])

    def test_annotation_parser_rejects_short_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "101_1b1_Al_sc.txt"
            path.write_text("1.0 1.0 0 0\n0.0 1.2 1 0\n", encoding="utf-8")
            cycles = parse_annotation_file(path)
            self.assertEqual(len(cycles), 1)
            self.assertEqual(cycles[0]["label_name"], "crackle")

    def test_smoke_training_writes_checkpoint_and_does_not_claim_icbhi(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = train_respiratory_model(
                epochs=2,
                lr=1e-3,
                checkpoint_dir=tmp,
                smoke_test=True,
                resume=False,
                batch_size=8,
            )
            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual(result["dataset_source"], "synthetic_protocol_smoke")
            self.assertFalse(result["metrics_are_icbhi"])
            self.assertTrue(Path(result["checkpoint_file"]).exists())
            self.assertIn("macro_f1", result["final_metrics"])
            self.assertEqual(result["final_metrics"]["class_names"], RESPIRATORY_CLASSES)
            overlap = set(result["split"]["train_patients"]) & set(result["split"]["test_patients"])
            self.assertEqual(overlap, set())


if __name__ == "__main__":
    unittest.main()
