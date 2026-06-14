# ethiviz/utils/batch.py
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator
import numpy as np

@dataclass
class BatchProgress:
    total: int
    completed: int
    failed: int
    checkpoint_path: str | None

    @property
    def fraction_complete(self) -> float:
        return self.completed / self.total if self.total > 0 else 0.0

class BatchProcessor:
    """
    Batch processing with tqdm progress, checkpointing, and parallel execution.

    Checkpointing saves results every `checkpoint_every` items so a crash
    does not lose hours of work. On restart, completed items are skipped.

    Example:
        >>> processor = BatchProcessor(checkpoint_dir="./checkpoints", n_workers=4)
        >>> results = processor.process(
        ...     items=texts,
        ...     fn=analyzer.score_text_single,
        ...     job_id="news_corpus_analysis_20250101",
        ...     checkpoint_every=100,
        ... )
    """
    def __init__(
        self,
        checkpoint_dir: str = "./ethiviz_checkpoints",
        n_workers: int = 1,
        show_progress: bool = True,
    ) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.n_workers = n_workers
        self.show_progress = show_progress

    def process(
        self,
        items: list[Any],
        fn: Callable[[Any], Any],
        job_id: str,
        checkpoint_every: int = 100,
    ) -> list[Any]:
        """
        Process items with fn, checkpointing every checkpoint_every items.
        Resumes from checkpoint if job_id was previously interrupted.
        Returns list of results in same order as items.
        """
        checkpoint_path = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        results: dict[int, Any] = {}

        # Resume from checkpoint if exists
        if checkpoint_path.exists():
            with checkpoint_path.open() as f:
                saved = json.load(f)
            results = {int(k): v for k, v in saved.items()}
            n_resumed = len(results)
        else:
            n_resumed = 0

        pending_indices = [i for i in range(len(items)) if i not in results]

        if self.show_progress:
            try:
                from tqdm import tqdm
                iterator: Any = tqdm(
                    pending_indices,
                    initial=n_resumed,
                    total=len(items),
                    desc=f"EthiViz batch [{job_id}]",
                )
            except ImportError:
                iterator = pending_indices
        else:
            iterator = pending_indices

        if self.n_workers > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                futures = {executor.submit(fn, items[i]): i for i in pending_indices}
                completed_count = 0
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        results[idx] = {"error": str(e)}
                    completed_count += 1
                    if completed_count % checkpoint_every == 0:
                        self._save_checkpoint(checkpoint_path, results)
        else:
            for i, idx in enumerate(iterator):
                try:
                    results[idx] = fn(items[idx])
                except Exception as e:
                    results[idx] = {"error": str(e)}
                if (i + 1) % checkpoint_every == 0:
                    self._save_checkpoint(checkpoint_path, results)

        self._save_checkpoint(checkpoint_path, results)
        return [results.get(i, None) for i in range(len(items))]

    def _save_checkpoint(self, path: Path, results: dict) -> None:
        with path.open("w") as f:
            # Convert results to JSON-safe format
            serializable = {}
            for k, v in results.items():
                try:
                    json.dumps(v)
                    serializable[str(k)] = v
                except (TypeError, ValueError):
                    serializable[str(k)] = str(v)
            json.dump(serializable, f)

    def clear_checkpoint(self, job_id: str) -> None:
        path = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        if path.exists():
            path.unlink()
