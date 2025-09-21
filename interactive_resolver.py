#!/usr/bin/env python3
"""
Interactive duplicate resolver with UI prompts for human judgment.
Handles safe numbered duplicates automatically, prompts for risky decisions.
"""

import yaml
import re
from pathlib import Path
import sys
from typing import List


def is_auto_generated_name(filename):
    """Check if filename appears to be auto-generated (like Rescued_video_)."""
    stem = Path(filename).stem
    patterns = [
        r"^Rescued_video_.*",
        r"^video_\d+.*",
        r"^download_\d+.*",
        r"^temp_.*",
        r"^\d{4}-\d{2}-\d{2}_.*",  # Date-based names
    ]
    return any(re.match(pattern, stem, re.IGNORECASE) for pattern in patterns)


def is_numbered_duplicate(filename):
    """Check if filename is a numbered browser duplicate."""
    stem = Path(filename).stem
    return bool(re.match(r"^.+ \(\d+\)$", stem))


def is_series_numbered(filename: str) -> bool:
    """Detect filenames that are part of a numbered series (e.g., 'part 1', '01', ' - 1', ' - 01').

    This is different from browser-numbered duplicates like 'name (1)'.
    Series-numbered files should not be auto-deleted even if their content hashes match.
    """
    stem = Path(filename).stem.lower()

    # Common series patterns: 'part 1', 'part01', ' - 1', ' - 01', '01 - ', 'episode 1', trailing digits
    patterns = [
        r"\bpart\s*\d+\b",
        r"\bepisode\s*\d+\b",
        r"\bep\s*\d+\b",
        r"\bvol(?:ume)?\s*\d+\b",
        r"(^|\D)\d{1,3}$",  # trailing number like 'name 1' or 'name 01'
        r"\b\d{1,2}[-_]",  # leading numbers like '01-foo' or '01_foo'
        r"[-_]\d{1,3}$",  # trailing '-1' or '_01'
    ]

    for p in patterns:
        if re.search(p, stem):
            return True
    return False


def get_file_size_mb(size_bytes):
    """Convert bytes to MB string."""
    return f"{size_bytes / 1024 / 1024:.1f} MB"


def show_duplicate_group(group, group_num, total_groups):
    """Display a duplicate group concisely."""
    files = group["files"]

    print(f"\nGroup {group_num}/{total_groups} - {group['space_wasted_human']} waste:")

    # Show all files in the group
    for i, file_info in enumerate(files, 1):
        path = file_info["path"]
        filename = Path(path).name
        size = get_file_size_mb(file_info["size_bytes"])

        markers = []
        if is_auto_generated_name(filename):
            markers.append("AUTO")
        if is_numbered_duplicate(filename):
            markers.append("(N)")

        marker_str = f" [{', '.join(markers)}]" if markers else ""
        print(f"  {i}. {filename} ({size}){marker_str}")

    return files


def show_auto_decision_concise(files):
    """Show concise auto-decision and return recommendation."""
    # Score files based on name quality
    scores = []

    for i, file_info in enumerate(files):
        filename = Path(file_info["path"]).name
        score = 0

        # Penalty for auto-generated names
        if is_auto_generated_name(filename):
            score -= 100

        # Penalty for numbered duplicates
        if is_numbered_duplicate(filename):
            score -= 50

        # Bonus for descriptive length (up to a point)
        name_length = len(Path(filename).stem)
        if 20 <= name_length <= 80:
            score += min(name_length - 20, 20)

        # Bonus for having recognizable words
        descriptive_words = [
            "full",
            "video",
            "hd",
            "compilation",
            "part",
            "scene",
            "episode",
        ]
        stem_lower = Path(filename).stem.lower()
        score += sum(5 for word in descriptive_words if word in stem_lower)

        scores.append((score, i, filename))

    # Sort by score (highest first)
    scores.sort(reverse=True)
    best_index = scores[0][1]

    print(f"Recommend KEEP: #{best_index + 1} {Path(files[best_index]['path']).name}")
    delete_files = [i + 1 for i in range(len(files)) if i != best_index]
    if delete_files:
        print(f"         DELETE: {', '.join(f'#{n}' for n in delete_files)}")

    return best_index


def get_user_choice_simple(files):
    """Get simple user choice with auto-recommendation shown."""
    best_index = show_auto_decision_concise(files)

    while True:
        choice = (
            input(
                "Accept (Y), Keep specific # (k3), Delete specific # (d2), Skip (s), Quit (q): "
            )
            .strip()
            .lower()
        )

        if choice in ["y", "yes", ""]:
            # Accept auto-recommendation
            return "auto", []
        elif choice == "q":
            return "quit", []
        elif choice == "s":
            return "skip", []
        elif choice.startswith("k"):
            try:
                num = int(choice[1:])
                if 1 <= num <= len(files):
                    return "keep", [num]
                else:
                    print(f"Invalid file number. Use 1-{len(files)}")
            except ValueError:
                print("Invalid format. Use: k3")
        elif choice.startswith("d"):
            try:
                num = int(choice[1:])
                if 1 <= num <= len(files):
                    return "delete", [num]
                else:
                    print(f"Invalid file number. Use 1-{len(files)}")
            except ValueError:
                print("Invalid format. Use: d2")
        else:
            print("Invalid choice. Use: y, k#, d#, s, or q")


def show_auto_decision(files):
    """Show what the auto-decision would be and return the recommendation."""
    print(f"\nAUTO-DECISION ANALYSIS:")
    print("=" * 60)

    # Score files based on name quality
    scores = []

    for i, file_info in enumerate(files):
        filename = Path(file_info["path"]).name
        score = 0
        score_reasons = []

        # Penalty for auto-generated names
        if is_auto_generated_name(filename):
            score -= 100
            score_reasons.append("auto-generated (-100)")

        # Penalty for numbered duplicates
        if is_numbered_duplicate(filename):
            score -= 50
            score_reasons.append("numbered duplicate (-50)")

        # Bonus for descriptive length (up to a point)
        name_length = len(Path(filename).stem)
        if 20 <= name_length <= 80:
            length_bonus = min(name_length - 20, 20)
            score += length_bonus
            score_reasons.append(f"good length (+{length_bonus})")

        # Bonus for having recognizable words
        descriptive_words = [
            "full",
            "video",
            "hd",
            "compilation",
            "part",
            "scene",
            "episode",
        ]
        stem_lower = Path(filename).stem.lower()
        word_bonus = sum(5 for word in descriptive_words if word in stem_lower)
        if word_bonus > 0:
            score += word_bonus
            score_reasons.append(f"descriptive words (+{word_bonus})")

        scores.append((score, i, filename, score_reasons))

    # Sort by score (highest first)
    scores.sort(reverse=True)

    # Show all files with their scores
    # Determine the best index (highest score) explicitly to avoid
    # referencing an undefined variable in case sorting reorders entries.
    best_index = scores[0][1]
    for rank, (score, i, filename, reasons) in enumerate(scores, 1):
        status = "KEEP" if rank == 1 else "DELETE"
        size_mb = get_file_size_mb(files[i]["size_bytes"])
        print(f"  {rank}. [{status:6}] {filename} ({size_mb})")
        print(
            f"      Score: {score:+3d} - {', '.join(reasons) if reasons else 'no bonuses/penalties'}"
        )
    print(f"RECOMMENDATION: Keep file #{best_index + 1} (highest score: {scores[0][0]})")

    return best_index


def auto_decide_best_file(files):
    """Execute the auto-decision after showing the analysis."""
    best_index = show_auto_decision(files)

    # Return indices of files to delete (all except the best one)
    return [i + 1 for i in range(len(files)) if i != best_index]


def main():
    if len(sys.argv) != 2:
        print("Usage: python interactive_resolver.py <scan_results.yaml>")
        sys.exit(1)

    scan_file = sys.argv[1]

    with open(scan_file, "r", encoding="utf-8") as f:
        scan_data = yaml.safe_load(f)

    duplicate_groups = scan_data["duplicate_groups"]

    print(f"Found {len(duplicate_groups)} duplicate groups to review")
    print("This tool will help you decide which files to keep/delete.")

    deletion_paths = []
    total_space_freed = 0

    for group_num, group in enumerate(duplicate_groups, 1):
        files = show_duplicate_group(group, group_num, len(duplicate_groups))

        # Check if this is a "safe" group (all numbered duplicates)
        all_numbered = all(is_numbered_duplicate(f["path"]) for f in files)
        has_base_file = any(not is_numbered_duplicate(f["path"]) for f in files)

        if all_numbered or (
            has_base_file and any(is_numbered_duplicate(f["path"]) for f in files)
        ):
            print("\n[SAFE GROUP: Numbered browser duplicates detected]")
            # Auto-delete numbered duplicates, keep base file or lowest number
            files_to_delete = []
            if has_base_file:
                # Delete all numbered files
                files_to_delete = [
                    i + 1
                    for i, f in enumerate(files)
                    if is_numbered_duplicate(f["path"])
                ]
            else:
                # All numbered, keep the lowest number
                def get_number(path):
                    match = re.search(r"\((\d+)\)", Path(path).stem)
                    return int(match.group(1)) if match else 0

                sorted_indices = sorted(
                    range(len(files)),
                    key=lambda i: get_number(files[i]["path"]),
                )
                files_to_delete = [
                    i + 1 for i in sorted_indices[1:]
                ]  # Keep first, delete rest

            action = "auto_safe"
        else:
            action, files_to_delete = get_user_choice_simple(files)

        if action == "quit":
            break
        elif action == "skip":
            continue
        elif action == "auto":
            # Auto-recommendation already calculated in get_user_choice_simple
            best_index = show_auto_decision_concise(files)
            files_to_delete = [i + 1 for i in range(len(files)) if i != best_index]
            action = "delete"
        elif action == "auto_safe":
            pass  # files_to_delete already set
        elif action == "keep":
            # Convert "keep" to "delete" (delete all others)
            files_to_delete = [
                i + 1 for i in range(len(files)) if (i + 1) not in files_to_delete
            ]
            action = "delete"

        if action in ["delete", "auto_safe"] and files_to_delete:
            space_freed = 0
            print("\nFiles to delete:")
            for file_num in files_to_delete:
                file_info = files[file_num - 1]
                filepath = file_info["path"]
                size_mb = get_file_size_mb(file_info["size_bytes"])
                print(f"  - {Path(filepath).name} ({size_mb})")

                # Record path for cross-platform deletion script
                deletion_paths.append(filepath)
                space_freed += file_info["size_bytes"]

            total_space_freed += space_freed
            print(f"Space freed: {get_file_size_mb(space_freed)}")

    # Generate final, cross-platform Python deletion script
    if deletion_paths:
        script_filename = "interactive_deletions.py"
        with open(script_filename, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("from pathlib import Path\n\n")
            f.write("# Files to delete (review before running)\n")
            f.write("FILES = [\n")
            for p in deletion_paths:
                # Use raw string literal to preserve backslashes on Windows
                f.write(f"    r'''{p}''',\n")
            f.write("]\n\n")
            f.write("def main():\n")
            f.write("    for p in FILES:\n")
            f.write("        try:\n")
            f.write("            Path(p).unlink()\n")
            f.write("            print('Deleted', p)\n")
            f.write("        except Exception as e:\n")
            f.write("            print('Failed to delete', p, '->', e)\n\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    main()\n\n")
            f.write(
                f"# Summary: {len(deletion_paths)} files, {get_file_size_mb(total_space_freed)} freed\n"
            )

        print(f"\n{'='*80}")
        print(f"Deletion script saved to: {script_filename}")
        print(f"Total files to delete: {len(deletion_paths)}")
        print(f"Total space to free: {get_file_size_mb(total_space_freed)}")
        print(f"Run with: python {script_filename}")
    else:
        print("No deletions selected.")


if __name__ == "__main__":
    main()
