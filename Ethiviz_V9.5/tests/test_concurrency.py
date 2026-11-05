"""Regression test for Upgrade 47 — Thread-Safe Shared Analyzer State.

The V6 README documented an open race: PlattCalibrator's fit()/calibrate()
methods mutated self._records/self._params without a lock, and _save() wrote
its JSON file with a plain `open(path, "w")`, so a job thread reading
mid-write (or two threads writing the same lens_id's file at once) could see
a torn/corrupted calibration. Upgrade 47 added an RLock around every
mutation/read and made _save() atomic (write-to-tempfile + os.replace).
This test proves both fixes hold under real concurrent load, not just a
single-threaded unit test — nothing in the existing suite exercised
PlattCalibrator across multiple threads before this file.
"""
from __future__ import annotations

import json
import threading

import numpy as np
import pytest

from ethiviz.scoring.calibration import PlattCalibrator
from ethiviz.scoring.drift import DriftMonitor


def _make_scores(n: int, seed: int) -> tuple[list[float], list[int]]:
    rng = np.random.RandomState(seed)
    labels = [0, 1] * (n // 2)
    scores = [
        float(np.clip(rng.normal(0.75 if label else 0.25, 0.1), 0.0, 1.0))
        for label in labels
    ]
    return scores, labels


class TestCalibratorConcurrency:
    def test_concurrent_fit_and_calibrate_no_corruption(self, tmp_path):
        calibrator = PlattCalibrator(calibration_dir=tmp_path)
        lens_id = "western_v1"

        # Seed an initial fit so calibrate() has something to read from the
        # first instant a reader thread starts, mirroring a long-running
        # server where the calibrator was already fitted before traffic
        # arrives.
        scores, labels = _make_scores(20, seed=0)
        calibrator.fit(lens_id, scores, labels, reference_corpus="seed")

        errors: list[BaseException] = []
        stop = threading.Event()

        def writer(seed: int) -> None:
            try:
                s, l = _make_scores(20, seed=seed)
                for _ in range(15):
                    calibrator.fit(lens_id, s, l, reference_corpus=f"writer-{seed}")
            except BaseException as exc:  # noqa: BLE001 - captured for the main thread to re-raise
                errors.append(exc)

        def reader() -> None:
            try:
                while not stop.is_set():
                    value = calibrator.calibrate(0.6, lens_id)
                    assert 0.0 <= value <= 1.0, f"calibrate() returned out-of-range value: {value}"
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        writers = [threading.Thread(target=writer, args=(seed,)) for seed in range(1, 9)]
        readers = [threading.Thread(target=reader) for _ in range(4)]

        for t in readers:
            t.start()
        for t in writers:
            t.start()
        for t in writers:
            t.join()
        stop.set()
        for t in readers:
            t.join()

        assert not errors, f"Concurrent fit()/calibrate() raised: {errors}"

        # The on-disk record must be valid JSON reflecting a single complete
        # write, never a torn write from two threads' os.replace() racing.
        saved_path = tmp_path / f"{lens_id}_calibration.json"
        with saved_path.open() as f:
            payload = json.load(f)
        assert payload["lens_id"] == lens_id
        assert isinstance(payload["platt_a"], float)
        assert isinstance(payload["platt_b"], float)

        # A fresh calibrator loading from the same directory must see the
        # same params fit() last recorded in memory — proves _load_saved()
        # and the in-memory state never diverged under concurrent writes.
        reloaded = PlattCalibrator(calibration_dir=tmp_path)
        assert reloaded._params[lens_id] == calibrator._params[lens_id]

    def test_no_stray_tmp_files_left_behind(self, tmp_path):
        """_save()'s atomic-write tempfile must always be renamed away by
        os.replace(), even under concurrent fits — a leftover *.tmp file
        would mean a writer crashed mid-write or two writers collided on the
        same tempfile name."""
        calibrator = PlattCalibrator(calibration_dir=tmp_path)
        lens_id = "confucian_v2"

        def writer(seed: int) -> None:
            s, l = _make_scores(20, seed=seed)
            for _ in range(10):
                calibrator.fit(lens_id, s, l, reference_corpus=f"writer-{seed}")

        threads = [threading.Thread(target=writer, args=(seed,)) for seed in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        leftover = list(tmp_path.glob("*.tmp"))
        assert not leftover, f"Atomic write left stray tempfiles: {leftover}"


class TestDriftMonitorConcurrency:
    """DriftMonitor already had its lock+atomic-write pattern from V6
    Upgrade 35 — this is a smoke test that concurrent snapshot recording
    still holds now that Upgrade 47 gives PlattCalibrator the same pattern,
    since both are reached from the same shared Analyzer singleton under
    Upgrade 47's threat model (concurrent job threads calling analyze())."""

    def test_concurrent_record_snapshot(self, tmp_path):
        monitor = DriftMonitor(snapshot_dir=tmp_path)
        lens_id = "ubuntu_v1"
        errors: list[BaseException] = []

        def writer(seed: int) -> None:
            try:
                scores = _make_scores(15, seed)[0]
                for _ in range(10):
                    monitor.record_snapshot(lens_id, scores, dataset_source=f"writer-{seed}")
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(seed,)) for seed in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent record_snapshot() raised: {errors}"
