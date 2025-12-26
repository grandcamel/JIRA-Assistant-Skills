"""
Batch processing utilities for large-scale JIRA operations.

Provides:
- Configurable batch sizes with automatic chunking
- Checkpoint/resume capability for long-running operations
- Progress tracking with callbacks
- Rate limiting between batches
"""

import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from datetime import datetime

T = TypeVar('T')


@dataclass
class BatchProgress:
    """Tracks progress of a batch operation."""
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    current_batch: int = 0
    total_batches: int = 0
    started_at: str = ""
    updated_at: str = ""
    errors: Dict[str, str] = field(default_factory=dict)
    processed_keys: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if processing is complete."""
        return self.processed_items >= self.total_items

    @property
    def percent_complete(self) -> float:
        """Calculate completion percentage."""
        if self.total_items == 0:
            return 100.0
        return (self.processed_items / self.total_items) * 100


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 50
    delay_between_batches: float = 1.0
    delay_between_items: float = 0.1
    max_items: int = 10000
    enable_checkpoints: bool = True
    checkpoint_dir: Optional[str] = None
    operation_id: Optional[str] = None

    def __post_init__(self):
        # Enforce reasonable limits
        self.batch_size = max(1, min(self.batch_size, 500))
        self.delay_between_batches = max(0.0, min(self.delay_between_batches, 60.0))
        self.delay_between_items = max(0.0, min(self.delay_between_items, 10.0))

        # Set default checkpoint directory
        if self.checkpoint_dir is None:
            self.checkpoint_dir = str(Path.home() / ".jira-skills" / "checkpoints")


class CheckpointManager:
    """Manages checkpoints for resumable operations."""

    def __init__(self, checkpoint_dir: str, operation_id: str):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
            operation_id: Unique identifier for this operation
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.operation_id = operation_id
        self.checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint.json"

    def save(self, progress: BatchProgress) -> None:
        """
        Save current progress to checkpoint file.

        Args:
            progress: Current batch progress
        """
        progress.updated_at = datetime.now().isoformat()
        data = asdict(progress)

        # Write to temp file first, then rename for atomicity
        temp_file = self.checkpoint_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        temp_file.rename(self.checkpoint_file)

    def load(self) -> Optional[BatchProgress]:
        """
        Load progress from checkpoint file.

        Returns:
            BatchProgress if checkpoint exists, None otherwise
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file) as f:
                data = json.load(f)
            return BatchProgress(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def clear(self) -> None:
        """Remove checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def exists(self) -> bool:
        """Check if a checkpoint exists."""
        return self.checkpoint_file.exists()


class BatchProcessor(Generic[T]):
    """
    Processes items in batches with checkpoint/resume support.

    Usage:
        processor = BatchProcessor(config, process_fn)
        result = processor.process(items, operation_id="bulk-transition-123")
    """

    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        process_item: Optional[Callable[[T], bool]] = None,
        progress_callback: Optional[Callable[[BatchProgress], None]] = None
    ):
        """
        Initialize batch processor.

        Args:
            config: Batch configuration
            process_item: Function to process each item (returns True on success)
            progress_callback: Optional callback for progress updates
        """
        self.config = config or BatchConfig()
        self.process_item = process_item
        self.progress_callback = progress_callback

    def process(
        self,
        items: List[T],
        get_key: Callable[[T], str],
        resume: bool = True,
        dry_run: bool = False
    ) -> BatchProgress:
        """
        Process items in batches.

        Args:
            items: List of items to process
            get_key: Function to extract unique key from item
            resume: Whether to resume from checkpoint if available
            dry_run: If True, simulate processing without changes

        Returns:
            Final BatchProgress with results
        """
        # Apply max_items limit
        items = items[:self.config.max_items]

        # Initialize progress
        progress = BatchProgress(
            total_items=len(items),
            total_batches=(len(items) + self.config.batch_size - 1) // self.config.batch_size,
            started_at=datetime.now().isoformat()
        )

        # Setup checkpoint manager if enabled
        checkpoint_mgr = None
        if self.config.enable_checkpoints and self.config.operation_id:
            checkpoint_mgr = CheckpointManager(
                self.config.checkpoint_dir,
                self.config.operation_id
            )

            # Try to resume from checkpoint
            if resume and checkpoint_mgr.exists():
                saved_progress = checkpoint_mgr.load()
                if saved_progress and not saved_progress.is_complete:
                    progress = saved_progress
                    # Filter out already processed items
                    processed_set = set(progress.processed_keys)
                    items = [item for item in items if get_key(item) not in processed_set]

        if dry_run:
            progress.total_batches = (len(items) + self.config.batch_size - 1) // self.config.batch_size
            return progress

        # Process in batches
        batches = self._create_batches(items)

        for batch_idx, batch in enumerate(batches):
            progress.current_batch = batch_idx + 1

            for item in batch:
                key = get_key(item)

                try:
                    if self.process_item:
                        success = self.process_item(item)
                        if success:
                            progress.successful_items += 1
                        else:
                            progress.failed_items += 1
                            progress.errors[key] = "Processing returned False"
                except Exception as e:
                    progress.failed_items += 1
                    progress.errors[key] = str(e)

                progress.processed_items += 1
                progress.processed_keys.append(key)

                # Delay between items
                if self.config.delay_between_items > 0:
                    time.sleep(self.config.delay_between_items)

            # Save checkpoint after each batch
            if checkpoint_mgr:
                checkpoint_mgr.save(progress)

            # Notify progress
            if self.progress_callback:
                self.progress_callback(progress)

            # Delay between batches
            if batch_idx < len(batches) - 1 and self.config.delay_between_batches > 0:
                time.sleep(self.config.delay_between_batches)

        # Clear checkpoint on completion
        if checkpoint_mgr and progress.is_complete:
            checkpoint_mgr.clear()

        return progress

    def _create_batches(self, items: List[T]) -> List[List[T]]:
        """Split items into batches."""
        return [
            items[i:i + self.config.batch_size]
            for i in range(0, len(items), self.config.batch_size)
        ]


def get_recommended_batch_size(total_items: int, operation_type: str = "simple") -> int:
    """
    Get recommended batch size based on total items and operation type.

    Args:
        total_items: Total number of items to process
        operation_type: Type of operation (simple, complex, clone)

    Returns:
        Recommended batch size
    """
    # Base batch sizes by operation complexity
    base_sizes = {
        "simple": 100,      # Simple field updates
        "complex": 50,      # Transitions, multi-field updates
        "clone": 25,        # Cloning (creates new issues)
        "transition": 50,   # Status transitions
        "assign": 100,      # Assignments
        "priority": 100     # Priority changes
    }

    base = base_sizes.get(operation_type, 50)

    # Reduce batch size for very large operations
    if total_items > 5000:
        return max(base // 2, 25)
    elif total_items > 1000:
        return max(base * 3 // 4, 25)

    return base


def generate_operation_id(operation_type: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate unique operation ID for checkpointing.

    Args:
        operation_type: Type of operation (e.g., "bulk-transition")
        timestamp: Optional timestamp (default: now)

    Returns:
        Unique operation ID string
    """
    if timestamp is None:
        timestamp = datetime.now()

    return f"{operation_type}-{timestamp.strftime('%Y%m%d-%H%M%S')}"


def list_pending_checkpoints(checkpoint_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all pending checkpoints that can be resumed.

    Args:
        checkpoint_dir: Directory containing checkpoints

    Returns:
        List of checkpoint info dicts
    """
    if checkpoint_dir is None:
        checkpoint_dir = str(Path.home() / ".jira-skills" / "checkpoints")

    checkpoint_path = Path(checkpoint_dir)
    if not checkpoint_path.exists():
        return []

    checkpoints = []
    for file in checkpoint_path.glob("*.checkpoint.json"):
        try:
            with open(file) as f:
                data = json.load(f)
            progress = BatchProgress(**data)
            if not progress.is_complete:
                checkpoints.append({
                    "operation_id": file.stem.replace(".checkpoint", ""),
                    "file": str(file),
                    "progress": progress.percent_complete,
                    "processed": progress.processed_items,
                    "total": progress.total_items,
                    "started_at": progress.started_at,
                    "updated_at": progress.updated_at
                })
        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    return sorted(checkpoints, key=lambda x: x.get("updated_at", ""), reverse=True)
