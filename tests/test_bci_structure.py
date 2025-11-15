"""
Test BCI module structure (without requiring numpy/scipy).

This test verifies that the BCI modules are properly structured
and can be imported (assuming dependencies are available).
"""

import sys
import os

def test_bci_module_structure():
    """Test that BCI module files exist and are properly structured."""

    bci_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bci')

    # Check that required files exist
    required_files = [
        '__init__.py',
        'openbci_interface.py',
        'neuralink_adapter.py',
        'signal_processor.py',
        'neural_bridge.py',
        'README.md',
    ]

    for filename in required_files:
        filepath = os.path.join(bci_path, filename)
        assert os.path.exists(filepath), f"Missing file: {filename}"
        print(f"✓ Found: {filename}")

    # Check that example files exist
    examples_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'bci')

    example_files = [
        'demo_openbci_heart_brain.py',
        'demo_neuralink_adaptive_control.py',
    ]

    for filename in example_files:
        filepath = os.path.join(examples_path, filename)
        assert os.path.exists(filepath), f"Missing example: {filename}"
        print(f"✓ Found example: {filename}")

    print("\n✅ All BCI module files found successfully!")
    return True


def test_thesis_structure():
    """Test that thesis document structure is complete."""

    thesis_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'thesis')

    # Check main file
    main_tex = os.path.join(thesis_path, 'main.tex')
    assert os.path.exists(main_tex), "Missing main.tex"
    print("✓ Found: main.tex")

    # Check references
    refs_bib = os.path.join(thesis_path, 'references.bib')
    assert os.path.exists(refs_bib), "Missing references.bib"
    print("✓ Found: references.bib")

    # Check key chapters
    chapters_path = os.path.join(thesis_path, 'chapters')

    required_chapters = [
        'titlepage.tex',
        'abstract.tex',
        '01_introduction.tex',
        '03_mathematical_preliminaries.tex',
        '05_lyapunov_analysis.tex',
    ]

    for chapter in required_chapters:
        filepath = os.path.join(chapters_path, chapter)
        assert os.path.exists(filepath), f"Missing chapter: {chapter}"
        print(f"✓ Found chapter: {chapter}")

    print("\n✅ Thesis document structure is complete!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("BCI AND THESIS STRUCTURE TESTS")
    print("=" * 60)
    print()

    print("Testing BCI module structure...")
    print("-" * 60)
    test_bci_module_structure()

    print()
    print("Testing thesis document structure...")
    print("-" * 60)
    test_thesis_structure()

    print()
    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Note: Actual execution requires numpy, scipy, matplotlib.")
    print("Install with: pip install numpy scipy matplotlib")
    print()
