"""
DuplicateDetector service for identifying duplicate and similar video files.

This service implements a two-stage detection approach:
1. Group files by size for performance optimization
2. Compute and compare hashes only for files with matching sizes
"""

from collections import defaultdict
from typing import List
from pathlib import Path
from fuzzywuzzy import fuzz
import re
import time
from datetime import timedelta

from src.models.file import UserFile
from ..models.duplicate_group import DuplicateGroup
from ..models.potential_match_group import PotentialMatchGroup

# Fraction of pairwise comparisons within a same-size group that must
# match the series-detection heuristics before the group is treated as a
# "series-numbered" group for auditing purposes. The intent is to avoid
# false-positives by requiring a majority of filename pairs to exhibit
# sequential/numbering patterns (e.g., Part 1, Part 2). Hashing is still
# performed for all files regardless of this flag so true byte-identical
# duplicates inside a series are still detected.
MAJORITY_SERIES_THRESHOLD = 0.6


class DuplicateDetector:
    """Service for detecting duplicate and potentially similar video files.

    Accepts optional injected collaborators (progress_reporter, logger)
    so callers can supply test doubles or shared instances via an IoC
    container. Backwards-compatible: methods still accept a per-call
    progress_reporter which takes precedence over the injected one.
    """

    def __init__(self, progress_reporter=None, logger=None):
        self._injected_reporter = progress_reporter
        # Prefer injected logger; otherwise obtain from Container so
        # logging configuration (level/handlers) is centralized. Fall
        # back to stdlib logger if container isn't available.
        if logger is not None:
            self._logger = logger
        else:
            try:
                from src.lib.container import Container

                self._logger = Container().logger()
            except Exception:
                import logging as _logging

                self._logger = _logging.getLogger(__name__)

    def find_duplicates(
        self,
        files: List[UserFile],
        progress_reporter=None,
        verbose: bool = False,
        metadata=None,
        db=None,
    ) -> List[DuplicateGroup]:
        """
        Identifies duplicate files using size and hash comparison.

        Uses a two-stage approach:
        1. Group files by size (fast comparison)
        2. Compute hashes only for files with matching sizes

        Args:
            files: List of video files to analyze
            progress_reporter: Optional progress reporter for feedback
            verbose: Enable detailed logging of actions taken

        Returns:
            List of duplicate groups (groups with at least 2 files)

        Contract:
            - MUST group files by size first (performance optimization)
            - MUST compute hashes only for files with matching sizes
            - MUST group files with identical hashes
            - MUST return groups with at least 2 files
            - MUST preserve file order within groups
        """
        if not files:
            return []

        if verbose:
            # Keep concise high-level info via logger
            try:
                self._logger.info(f"Analyzing {len(files)} files for duplicates...")
                cloud_only_count = sum(1 for f in files if f.is_cloud_only)
                local_count = len(files) - cloud_only_count
                self._logger.info(f"  Cloud-only files: {cloud_only_count}")
                self._logger.info(f"  Local files: {local_count}")
                # Provide per-file listing at DEBUG so individual file lines only
                # appear when DEBUG logging is enabled; verbose CLI still shows
                # summaries at INFO level.
                for user_file in files:
                    cloud_status = "CLOUD-ONLY" if user_file.is_cloud_only else "LOCAL"
                    try:
                        size_mb = user_file.size / (1024 * 1024)
                    except Exception:
                        size_mb = 0
                    self._logger.debug(
                        f"  {cloud_status:10} | {size_mb:8.1f} MB | {user_file.path}"
                    )
            except Exception:
                # If logging fails, continue without per-file details
                pass

        # Stage 1: Group files by size for performance optimization
        size_groups = defaultdict(list)
        for file in files:
            size_groups[file.size].append(file)

        # Collect series groups for metadata export (list of group dicts)
        # Note: series-like groups are recorded for auditing but hashing
        # is still performed so true duplicates inside a numbered series
        # are detected correctly.
        skipped_series = 0  # kept for backward-compat checks but not incremented
        series_groups = []
        if verbose:
            groups_with_multiple = sum(
                1 for file_list in size_groups.values() if len(file_list) >= 2
            )
            self._logger.info(f"Found {groups_with_multiple} size groups with potential duplicates")
            # series count will be reported after analysis when known
        # NOTE: Do NOT skip hashing for series-numbered groups.
        # If sizes match, always run the hash. Only treat as series if hashes differ.
        # This is now enforced: we do NOT skip hashing for series-numbered groups.
        # The logic below will always run the hash for size groups with >=2 files,
        # regardless of whether they look like a series.

        # Stage 2: For size groups with multiple files, compute hashes
        duplicate_groups = []
        total_files_to_hash = sum(
            len(file_list) for file_list in size_groups.values() if len(file_list) >= 2
        )
        hashed_files = 0
        skipped_cloud_files = 0
        skipped_error_files = 0
        hash_start = time.time()

        for file_list in size_groups.values():
            if len(file_list) < 2:
                # Skip groups with only one file
                continue

            # Detect if this size group looks like a numbered series (e.g.,
            # 'Show Part 1', 'Show Part 2'). If so, skip hashing for the whole
            # group to avoid false-positive duplicate groups.
            try:
                names = [
                    self._extract_filename_for_comparison(f.path) for f in file_list
                ]
                # Use a majority-rule: compute how many unique filename
                # pairs within the size-group would be excluded from
                # similarity by the sequential/numbering heuristics. Only
                # mark the whole group as a series when the proportion of
                # such pairs >= MAJORITY_SERIES_THRESHOLD. This reduces
                # false positives when a size-group contains mixed content.
                pair_count = 0
                excluded_pairs = 0
                for i in range(len(names)):
                    for j in range(i + 1, len(names)):
                        pair_count += 1
                        if self._should_exclude_from_similarity(names[i], names[j]):
                            excluded_pairs += 1

                is_series_group = False
                if pair_count > 0:
                    proportion = excluded_pairs / pair_count
                    if proportion >= MAJORITY_SERIES_THRESHOLD:
                        is_series_group = True

                # If group appears to be a sequential/series set, record it
                # for audit/export but continue to compute hashes so that
                # any true duplicates within the series are still detected.
                if is_series_group:
                    if verbose:
                        # Log series detection at debug level; keep console output brief
                        self._logger.debug(
                            f"LIKELY SERIES: {[str(f.path) for f in file_list]}"
                        )
                    # Record a serializable representation of the group for export
                    try:
                        series_group = {
                            "file_count": len(file_list),
                            "files": [
                                {
                                    "path": str(f.path),
                                    "size_bytes": f.size,
                                    "size_human": f"{f.size / (1024 * 1024):.1f} MB",
                                }
                                for f in file_list
                            ],
                            "reason": "series-numbered",
                        }
                        series_groups.append(series_group)
                        # Attach group-level entry to metadata if provided
                        if metadata is not None:
                            try:
                                if not hasattr(metadata, "series_groups"):
                                    metadata.series_groups = []
                                # store group-level dicts (not per-file flattened list)
                                metadata.series_groups.append(series_group)
                                # store count of series groups
                                metadata.series_groups_found = (
                                    getattr(metadata, "series_groups_found", 0) + 1
                                )
                            except Exception:
                                pass
                    except Exception:
                        # best-effort: if building the representation fails, continue
                        pass
            except Exception:
                # If group-level detection fails, fall back to hashing normally
                pass

            # Compute hashes for all files in this size group
            hash_groups = defaultdict(list)
            for file in file_list:
                try:
                    # Report progress if reporter available
                    # Prefer a per-call reporter if provided, otherwise use
                    # the injected reporter supplied at construction time.
                    reporter_to_use = (
                        progress_reporter
                        if progress_reporter is not None
                        else getattr(self, "_injected_reporter", None)
                    )
                    if reporter_to_use:
                        try:
                            reporter_to_use.update_progress(
                                hashed_files, f"Computing hash: {file.path.name}"
                            )
                        except Exception:
                            # Guard against reporter failures
                            pass

                    # Skip hash computation for cloud-only files to avoid triggering downloads
                    if hasattr(file, "is_cloud_only") and file.is_cloud_only:
                        if verbose:
                            self._logger.debug(f"SKIPPED (cloud-only): {file.path}")
                        hashed_files += 1
                        skipped_cloud_files += 1
                        continue

                    if verbose:
                        self._logger.debug(f"HASHING: {file.path}")

                    # Compute hash if not already done
                    if hasattr(file, "compute_hash"):
                        file_hash = file.compute_hash()
                        # Persist computed hash to the optional database cache
                        if db is not None:
                                # Use path.stat().st_mtime for mtime numeric value
                                try:
                                    mtime = file.path.stat().st_mtime
                                except Exception:
                                    mtime = None
                                try:
                                    if mtime is not None:
                                        db.set_cached_hash(file.path, file.size, mtime, file_hash)
                                except Exception as e:
                                    # DB persistence is best-effort; do not fail hashing
                                    try:
                                        # Log at debug level; do not raise on DB failures
                                        self._logger.debug(
                                            f"Failed to persist hash for {file.path}: {e}"
                                        )
                                    except Exception:
                                        pass
                    else:
                        file_hash = str(file.path)  # fallback for now
                    hash_groups[file_hash].append(file)
                    hashed_files += 1
                except (OSError, PermissionError) as e:
                    if verbose:
                        try:
                            name = file.path
                        except Exception:
                            name = "<unknown>"
                        self._logger.debug(f"SKIPPED (error): {name} - {e}")
                    # Skip files that can't be read
                    hashed_files += 1
                    skipped_error_files += 1
                    continue

            # Create duplicate groups for hash groups with multiple files
            for file_hash, files_with_same_hash in hash_groups.items():
                if len(files_with_same_hash) >= 2:
                    # Preserve file order within groups
                    duplicate_group = DuplicateGroup(file_hash, files_with_same_hash)
                    duplicate_groups.append(duplicate_group)
                    if verbose:
                        # Announce duplicate groups at INFO (concise)
                        self._logger.info(
                            f"  DUPLICATE GROUP: {len(files_with_same_hash)} files with hash {file_hash[:8]}..."
                        )

        if verbose:
            # Summary via logger
            self._logger.info("Hash computation summary:")
            self._logger.info(
                f"  Files hashed: {hashed_files - skipped_cloud_files - skipped_error_files}"
            )
            self._logger.info(f"  Cloud-only files skipped: {skipped_cloud_files}")
            self._logger.info(f"  Error files skipped: {skipped_error_files}")
            self._logger.info(f"  Duplicate groups found: {len(duplicate_groups)}")
            # Detailed metrics to debug log
            self._logger.debug(
                {
                    "hashed_files": hashed_files,
                    "skipped_cloud": skipped_cloud_files,
                    "skipped_error": skipped_error_files,
                    "duplicate_groups": len(duplicate_groups),
                }
            )

        # Terminal summary: report series groups skipped (brief, even when not verbose)
        if skipped_series:
            series_group_count = getattr(metadata, "series_groups_found", None)
            if series_group_count is None:
                # fallback to local capture
                series_group_count = len(series_groups)
            # Log series summary at info level
            self._logger.info(
                f"Series groups skipped: {series_group_count} groups, {skipped_series} files"
            )

        # Populate metadata if provided
        hash_time = time.time() - hash_start
        try:
            if metadata is not None:
                # files_hashed should reflect actual hashed files (excluding skipped)
                metadata.files_hashed = max(
                    0, hashed_files - skipped_cloud_files - skipped_error_files
                )
                # add to existing timedelta
                if hasattr(metadata, "hash_computation_time"):
                    metadata.hash_computation_time += timedelta(seconds=hash_time)
                else:
                    metadata.hash_computation_time = timedelta(seconds=hash_time)
                # increment error/skip counters
                if hasattr(metadata, "total_files_error"):
                    metadata.total_files_error += skipped_error_files
                if hasattr(metadata, "total_files_skipped"):
                    metadata.total_files_skipped += skipped_cloud_files
        except Exception:
            # Do not let metadata failures break duplicate detection
            pass

        return duplicate_groups

    def find_potential_matches(
        self,
        files: List[UserFile],
        threshold: float = 0.8,
        verbose: bool = False,
    ) -> List[PotentialMatchGroup]:
        """
        Identifies files with similar names that might be duplicates.

        Uses fuzzy string matching on filenames combined with size analysis
        to identify potential duplicates that require manual review.

        Args:
            files: List of video files to analyze
            threshold: Name similarity threshold (0.0-1.0)
            verbose: Enable detailed logging of actions taken

        Returns:
            List of potential match groups

        Contract:
            - MUST use fuzzy string matching on filenames (name similarity)
            - MUST validate with size comparison (file similarity indicators)
            - MUST ignore file extensions in name comparison
            - MUST only group files above threshold name similarity
            - MUST calculate accurate similarity scores
            - MUST handle Unicode filenames correctly
        """
        if not files or threshold < 0.0 or threshold > 1.0:
            return []

        if verbose:
            self._logger.info(
                f"Analyzing {len(files)} files for potential matches (name similarity threshold: {threshold})..."
            )

        potential_groups = []
        processed_files = set()
        excluded_pairs = 0

        for i, file1 in enumerate(files):
            if file1 in processed_files:
                continue

            # Extract filename without extension for comparison
            name1 = self._extract_filename_for_comparison(file1.path)

            # Find all files similar to this one
            similar_files = [file1]
            similarity_scores = {}

            for j, file2 in enumerate(files[i + 1 :], start=i + 1):
                if file2 in processed_files:
                    continue

                name2 = self._extract_filename_for_comparison(file2.path)

                # Check if files should be excluded from similarity matching
                if self._should_exclude_from_similarity(name1, name2):
                    if verbose:
                        # Exclusions between filename pairs are file-level details
                        # and should be emitted at DEBUG level only.
                        self._logger.debug(
                            f"  EXCLUDED (name patterns): '{file1.path.name}' vs '{file2.path.name}' (obvious non-duplicates)"
                        )
                    excluded_pairs += 1
                    continue

                # Calculate name similarity score using fuzzy matching
                name_similarity = fuzz.ratio(name1, name2) / 100.0

                if name_similarity >= threshold:
                    # Check if file sizes are reasonably similar (within 3x of each other)
                    # Different quality encodings of same content shouldn't differ by more than 3x
                    size_ratio = max(file1.size, file2.size) / max(
                        min(file1.size, file2.size), 1
                    )
                    # If filenames look like a numbered series (episode/part/vol/etc.)
                    # and the sizes differ by more than 10%, treat them as distinct
                    # versions and exclude from potential-duplicate groups. This
                    # reduces noisy potential-match results for serialized content.
                    if self._is_series_pair(name1, name2) and size_ratio > 1.1:
                        if verbose:
                            # Series exclusions are file-pair level details; emit
                            # at DEBUG so they only show when --debug is used.
                            self._logger.debug(
                                f"  EXCLUDED (series): '{file1.path.name}' vs '{file2.path.name}' - name similarity: {name_similarity:.2f}, sizes: {file1.size/(1024*1024):.1f}MB vs {file2.size/(1024*1024):.1f}MB (ratio: {size_ratio:.1f}x)"
                            )
                        excluded_pairs += 1
                        continue

                    if size_ratio > 3.0:
                        if verbose:
                            # Size-difference exclusions are file-pair level
                            # details; emit at DEBUG only.
                            self._logger.debug(
                                f"  EXCLUDED (size diff): '{file1.path.name}' vs '{file2.path.name}' - name similarity: {name_similarity:.2f}, sizes: {file1.size/(1024*1024):.1f}MB vs {file2.size/(1024*1024):.1f}MB (ratio: {size_ratio:.1f}x)"
                            )
                        excluded_pairs += 1
                        continue

                    if verbose:
                        # Individual POTENTIAL MATCH lines are file-level
                        # diagnostics; route them to DEBUG so only --debug
                        # shows the full pairwise listing.
                        self._logger.debug(
                            f"  POTENTIAL MATCH: '{file1.path.name}' vs '{file2.path.name}' - name similarity: {name_similarity:.2f}, sizes: {file1.size/(1024*1024):.1f}MB vs {file2.size/(1024*1024):.1f}MB"
                        )
                    similar_files.append(file2)
                    similarity_scores[file2] = name_similarity

            # Create potential match group if we found similar files
            if len(similar_files) >= 2:
                # Set similarity score for the base file
                similarity_scores[file1] = 1.0

                # Use the base filename as the group name
                base_name = self._extract_filename_for_comparison(file1.path)
                potential_group = PotentialMatchGroup(base_name, threshold)

                # Add all similar files to the group
                for file in similar_files:
                    potential_group.add_file(file, similarity_scores[file])

                potential_groups.append(potential_group)

                if verbose:
                    self._logger.info(
                        f"  POTENTIAL GROUP: {len(similar_files)} files similar to '{file1.path.name}'"
                    )

                # Mark all files in this group as processed
                for file in similar_files:
                    processed_files.add(file)

        if verbose:
            self._logger.info("Potential match analysis summary:")
            self._logger.info(f"  Potential groups found: {len(potential_groups)}")
            self._logger.info(f"  Excluded obvious non-duplicates: {excluded_pairs}")

        return potential_groups

    def _is_series_pair(self, name1: str, name2: str) -> bool:
        """
        Heuristic to detect if two filenames are part of the same numbered series
        (episodes/parts/volumes/chapters) but different entries. Returns True
        when a strong sequential/numbering pattern is present and the base
        titles (with numbers removed) are very similar.

        Names passed to this helper are expected to be normalized/lowercased
        by `_extract_filename_for_comparison`.
        """
        # Patterns that commonly indicate series numbering
        series_patterns = [
            r"\bepisode\s*(\d+)\b",
            r"\bep\s*(\d{1,3})\b",
            r"\bpart\s*(\d+)\b",
            r"\bchapter\s*(\d+)\b",
            r"\bvol(?:ume)?\s*(\d+)\b",
            r"\bchapter\s*(\d+)\b",
            r"\b(?:s|season)\s*(\d+)e?(\d+)?\b",
            r"\((\d{1,3})\)\s*$",
            r"(?:\b|_|-)(\d{1,3})$",
        ]

        found_num1 = None
        found_num2 = None
        # Try to find a numeric token for each name using the patterns
        for pat in series_patterns:
            m1 = re.search(pat, name1, flags=re.IGNORECASE)
            m2 = re.search(pat, name2, flags=re.IGNORECASE)
            if m1 and m2:
                # Prefer the captured numeric portion(s)
                found_num1 = m1.group(1) if m1.groups() else m1.group(0)
                found_num2 = m2.group(1) if m2.groups() else m2.group(0)
                # If numbers differ, check base similarity
                if found_num1 != found_num2:
                    base1 = re.sub(pat, "", name1, flags=re.IGNORECASE).strip(" -_\t")
                    base2 = re.sub(pat, "", name2, flags=re.IGNORECASE).strip(" -_\t")
                    try:
                        sim = fuzz.ratio(base1, base2) / 100.0
                    except Exception:
                        sim = 0.0
                    if sim > 0.9:
                        return True

        return False

    def _extract_filename_for_comparison(self, file_path: Path) -> str:
        """
        Extract filename without extension for fuzzy comparison.

        Handles Unicode filenames correctly and normalizes for comparison.

        Args:
            file_path: Path to the file

        Returns:
            Filename without extension, suitable for comparison (lowercase)
        """
        # Get filename without extension
        filename = file_path.stem

        # Normalize whitespace and handle Unicode correctly
        filename = re.sub(r"\s+", " ", filename.strip())

        # Convert to lowercase for case-insensitive comparison
        return filename.lower()

    def _should_exclude_from_similarity(self, name1: str, name2: str) -> bool:
        """
        Check if two filenames should be excluded from similarity matching.

        Only excludes very obvious non-duplicates with high confidence to avoid
        blocking legitimate potential matches.

        Args:
            name1: First filename (already lowercased)
            name2: Second filename (already lowercased)

        Returns:
            True if files should be excluded from similarity matching
        """
        # Only exclude if we have very high confidence they're different
        # Pattern 1: Clear sequential numbering with same base name
        # Only exclude if the base names are very similar AND numbers are clearly different
        sequential_patterns = [
            r"\bpart\s*(\d+)\b",
            r"\bepisode\s*(\d+)\b",
            r"\bvol(?:ume)?\s*(\d+)\b",
        ]

        for pattern in sequential_patterns:
            matches1 = re.findall(pattern, name1, re.IGNORECASE)
            matches2 = re.findall(pattern, name2, re.IGNORECASE)

            if matches1 and matches2 and matches1 != matches2:
                # Remove the sequential parts and check if base names are nearly identical
                base1 = re.sub(pattern, "", name1, flags=re.IGNORECASE).strip()
                base2 = re.sub(pattern, "", name2, flags=re.IGNORECASE).strip()

                # Only exclude if base names are very similar (>90% match)
                base_similarity = fuzz.ratio(base1, base2) / 100.0
                if base_similarity > 0.9:
                    return True  # High confidence these are sequential parts

        # Pattern 2: Identical timestamps with small time differences
        # Only exclude files with identical base names but different precise timestamps
        timestamp_pattern = r"(\d{4}-\d{2}-\d{2}\s+\d{2}[_:]\d{2})"
        times1 = re.findall(timestamp_pattern, name1)
        times2 = re.findall(timestamp_pattern, name2)

        if times1 and times2 and times1 != times2:
            # Remove timestamps and check if base names are identical
            base1 = re.sub(timestamp_pattern, "", name1).strip()
            base2 = re.sub(timestamp_pattern, "", name2).strip()
            if base1 == base2:  # Identical base names, different timestamps
                return True

        # Pattern 3: Parenthesized numeric suffixes often indicate browser copy numbering
        paren_pattern = r"\((\d{1,3})\)\s*$"
        m1 = re.search(paren_pattern, name1)
        m2 = re.search(paren_pattern, name2)
        if m1 and m2 and m1.group(1) != m2.group(1):
            base1 = re.sub(paren_pattern, "", name1).strip()
            base2 = re.sub(paren_pattern, "", name2).strip()
            if fuzz.ratio(base1, base2) / 100.0 > 0.9:
                return True

        # Pattern 4: Generic trailing numeric tokens (e.g., 'Boyfriend 1', 'name - 01')
        trailing_num_pattern = r"(?:\b|_|-|\s)(\d{1,3})$"
        t1 = re.search(trailing_num_pattern, name1)
        t2 = re.search(trailing_num_pattern, name2)
        if t1 and t2 and t1.group(1) != t2.group(1):
            base1 = re.sub(trailing_num_pattern, "", name1).strip(" -_\t")
            base2 = re.sub(trailing_num_pattern, "", name2).strip(" -_\t")
            if fuzz.ratio(base1, base2) / 100.0 > 0.9:
                return True

        return False  # Don't exclude - let fuzzy matching decide
