"""
Unit tests for cross-language semantic clones.
Verifies that program pairs with identical functional intent yield similarity scores > 75%.
"""
import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from backend.core.similarity_engine import StrictSemanticSimilarityEngine
from compiler.compiler_detector import detect_flang, detect_clang, detect_clangpp, detect_rustc

class TestCrossLanguageClones(unittest.TestCase):
    """Asserts that equivalent functional clone pairs meet similarity thresholds."""

    @classmethod
    def setUpClass(cls):
        cls.engine = StrictSemanticSimilarityEngine()
        cls.benchmark_dir = Path("testcases") / "benchmark"

    @unittest.skipIf(not detect_clang() or not detect_rustc(), "Clang or Rust compiler missing")
    def test_fibonacci_c_rust(self):
        """Verify C Fibonacci vs Rust Fibonacci similarity is > 75%."""
        f1 = self.benchmark_dir / "fibonacci.c"
        f2 = self.benchmark_dir / "fibonacci.rs"
        
        res = self.engine.compare_files(str(f1), str(f2))
        score = res["similarity"]
        self.assertGreaterEqual(score, 75.0, f"Fibonacci C ↔ Rust scored only {score}%")
        
    @unittest.skipIf(not detect_clang() or not detect_clangpp(), "Clang or Clang++ compiler missing")
    def test_fibonacci_recursive_iterative(self):
        """Verify Fibonacci recursive (C++) vs iterative (C) similarity is > 75%."""
        f1 = self.benchmark_dir / "fibonacci.c"
        f2 = self.benchmark_dir / "fibonacci.cpp"
        
        res = self.engine.compare_files(str(f1), str(f2))
        score = res["similarity"]
        self.assertGreaterEqual(score, 75.0, f"Fibonacci Rec ↔ Iter scored only {score}%")

    @unittest.skipIf(not detect_clang() or not detect_clangpp(), "Clang or Clang++ compiler missing")
    def test_max_element_c_cpp(self):
        """Verify C Max Element vs C++ Max Element similarity is > 75%."""
        f1 = self.benchmark_dir / "max_element.c"
        f2 = self.benchmark_dir / "max_element.cpp"
        
        res = self.engine.compare_files(str(f1), str(f2))
        score = res["similarity"]
        self.assertGreaterEqual(score, 75.0, f"Max Element C ↔ C++ scored only {score}%")

    @unittest.skipIf(not detect_clang() or not detect_rustc(), "Clang or Rust compiler missing")
    def test_student_management_rust_c(self):
        """Verify Rust Student Management vs C Student Management similarity is > 75%."""
        f1 = self.benchmark_dir / "student.c"
        f2 = self.benchmark_dir / "student.rs"
        
        res = self.engine.compare_files(str(f1), str(f2))
        score = res["similarity"]
        self.assertGreaterEqual(score, 75.0, f"Student Management Rust ↔ C scored only {score}%")

    @unittest.skipIf(not detect_clang() or not detect_flang(), "Clang or Flang compiler missing")
    def test_fortran_pair_if_available(self):
        f1 = self.benchmark_dir / "factorial.f90"
        f2 = self.benchmark_dir / "factorial.c"
        res = self.engine.compare_files(str(f1), str(f2))
        self.assertGreaterEqual(res["similarity"], 75.0)

    @unittest.skipIf(not detect_clang(), "Clang compiler missing")
    def test_negative_pair_capped(self):
        f1 = self.benchmark_dir / "fibonacci.c"
        f2 = self.benchmark_dir / "factorial.c"
        res = self.engine.compare_files(str(f1), str(f2))
        self.assertLessEqual(res["similarity"], 30.0)

if __name__ == "__main__":
    unittest.main()
