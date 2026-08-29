"""
Unit and integration test suite for the Cross-Language Semantic Code Clone Detector.
"""
import sys
from pathlib import Path
# Self-contained path resolution to locate dependencies inside src/
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

import unittest
import tempfile
import shutil

from compiler import CompilerPipeline
from compiler.compiler_detector import detect_clang
from ir import IRExtractor, IRParser, IRNormalizer
from graph import CFGBuilder, DFGBuilder, GraphFingerprint
from semantic import IntentDetector, NegativeRules, FunctionalFamily
from backend.core.similarity_engine import StrictSemanticSimilarityEngine

class TestCompilerPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = CompilerPipeline()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cd_tests_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_language_detection(self):
        self.assertEqual(self.pipeline.detect_language("test.c"), "c")
        self.assertEqual(self.pipeline.detect_language("test.cpp"), "cpp")
        self.assertEqual(self.pipeline.detect_language("test.rs"), "rust")
        self.assertEqual(self.pipeline.detect_language("test.f90"), "fortran")
        self.assertIsNone(self.pipeline.detect_language("test.txt"))

    @unittest.skipIf(not detect_clang(), "Clang compiler not installed")
    def test_c_compilation(self):
        source = self.temp_dir / "factorial.c"
        source.write_text("int factorial(int n) { return n <= 1 ? 1 : n * factorial(n - 1); }")
        output = self.temp_dir / "factorial.ll"
        
        self.pipeline.compile_to_ir(source, output)
        self.assertTrue(output.exists())
        self.assertIn("define", output.read_text(errors="ignore"))

class TestIRProcessing(unittest.TestCase):
    def test_ir_extractor_and_parser(self):
        ir = """
define i32 @factorial(i32 %n) {
entry:
  %cmp = icmp sle i32 %n, 1
  br i1 %cmp, label %if.then, label %if.else

if.then:
  ret i32 1

if.else:
  ret i32 0
}
"""
        funcs = IRExtractor.extract_functions(ir)
        self.assertIn("@factorial", funcs)
        
        blocks = IRParser.parse_function_body(funcs["@factorial"])
        self.assertIn("entry", blocks)
        self.assertIn("if.then", blocks)
        self.assertIn("if.else", blocks)
        
        # entry block should jump to if.then and if.else
        self.assertEqual(sorted(blocks["entry"].successors), ["if.else", "if.then"])

    def test_ir_normalization(self):
        raw = """
define i32 @factorial_recursive(i32 %n.addr) {
  %1 = load i32, i32* %n.addr
  ret i32 %1
}
"""
        norm = IRNormalizer.normalize_ir(raw)
        self.assertIn("VAR", norm)
        self.assertIn("FUNC", norm)
        self.assertNotIn("factorial_recursive", norm)

class TestGraphAnalytics(unittest.TestCase):
    def test_cfg_and_dfg_builders(self):
        ir = """
define i32 @test() {
entry:
  %0 = alloca i32
  store i32 5, i32* %0
  %1 = load i32, i32* %0
  br label %exit

exit:
  ret i32 %1
}
"""
        blocks = IRParser.parse_function_body(ir)
        cfg = CFGBuilder.build_cfg(blocks)
        dfg = DFGBuilder.build_dfg(blocks)
        
        self.assertEqual(cfg.number_of_nodes(), 2)
        self.assertTrue(dfg.has_node("%0"))
        
        # Test WL Hashing
        cfg_hash = GraphFingerprint.compute_wl_hash(cfg, iterations=1)
        self.assertIsNotNone(cfg_hash)

class TestSemanticIntentEngine(unittest.TestCase):
    def setUp(self):
        self.detector = IntentDetector()

    def test_intent_keywords(self):
        source = "int factorial(int n) { if(n==0) return 1; return n*factorial(n-1); }"
        res = self.detector.detect_intent(source, "fact.c")
        self.assertEqual(res["intent"], "Factorial")
        self.assertEqual(res["domain"], "Numeric")

    def test_negative_rules(self):
        self.assertTrue(NegativeRules.is_negative_pair("Maximum Element", "Vowel Counter"))
        self.assertFalse(NegativeRules.is_negative_pair("Factorial", "Fibonacci"))

    def test_functional_family(self):
        self.assertEqual(FunctionalFamily.get_family("Factorial"), "NUMERIC_COMPUTATION")
        self.assertEqual(FunctionalFamily.get_family("Sorting"), "ARRAY_PROCESSING")
        self.assertEqual(FunctionalFamily.calculate_similarity("Factorial", "Fibonacci"), 1.0)
        self.assertEqual(FunctionalFamily.calculate_similarity("Factorial", "Sorting"), 0.0)

class TestSimilarityEngine(unittest.TestCase):
    @unittest.skipIf(not detect_clang(), "Clang compiler not installed")
    def test_engine_smoke(self):
        engine = StrictSemanticSimilarityEngine()
        with tempfile.TemporaryDirectory() as tmp:
            f1 = Path(tmp) / "f1.c"
            f2 = Path(tmp) / "f2.c"
            f1.write_text("int factorial(int n) { return n <= 1 ? 1 : n * factorial(n - 1); }")
            f2.write_text("int fact(int n) { int acc = 1; for(int i=2;i<=n;i++) acc*=i; return acc; }")
            
            res = engine.compare_files(str(f1), str(f2))
            self.assertIn("similarity", res)
            self.assertGreaterEqual(res["similarity"], 55.0)

if __name__ == "__main__":
    unittest.main()
