"""
Compiler package providing C, C++, Fortran, and Rust compilation to LLVM IR.
"""
from pathlib import Path
from typing import Optional, Tuple
import logging

from compiler.c_compiler import CCompiler
from compiler.cpp_compiler import CPPCompiler
from compiler.fortran_compiler import FortranCompiler
from compiler.rust_compiler import RustCompiler
from compiler.compiler_detector import detect_clang, detect_clangpp, detect_rustc, detect_flang
from compiler.llvm_validator import LLVMValidator, LLVMCompilationError, LLVMGenerationError

logger = logging.getLogger(__name__)

class CompilerPipeline:
    """Combines C, C++, Fortran, and Rust compilers into a single pipeline."""
    
    def __init__(self, opt_level: str = "2"):
        self.opt_level = opt_level
        self.c = CCompiler(opt_level)
        self.cpp = CPPCompiler(opt_level)
        self.fortran = FortranCompiler(opt_level)
        self.rust = RustCompiler(opt_level)

    def detect_language(self, filename: str) -> Optional[str]:
        ext = Path(filename).suffix.lower()
        if ext == ".c":
            return "c"
        elif ext in [".cpp", ".cc", ".cxx", ".hpp"]:
            return "cpp"
        elif ext in [".f90", ".f95", ".f03", ".f", ".for"]:
            return "fortran"
        elif ext == ".rs":
            return "rust"
        return None

    def compile_to_ir(self, source_path: Path, output_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Compiles source file to LLVM IR.
        
        Raises LLVMCompilationError if compiler is missing or if compilation fails.
        """
        lang = self.detect_language(source_path.name)
        if not lang:
            raise LLVMCompilationError(f"Unsupported file type: {source_path.suffix}")
            
        success = False
        err = None
        
        if lang == "c":
            clang_path = detect_clang()
            if not clang_path:
                raise LLVMCompilationError("Clang compiler not found on system.")
            success, err = self.c.compile(source_path, output_path, clang_path)
            if not success:
                raise LLVMCompilationError(f"Clang compilation failed: {err}")
            LLVMValidator.validate_ir_file(output_path)
                
        elif lang == "cpp":
            clangpp_path = detect_clangpp()
            if not clangpp_path:
                raise LLVMCompilationError("Clang++ compiler not found on system.")
            success, err = self.cpp.compile(source_path, output_path, clangpp_path)
            if not success:
                raise LLVMCompilationError(f"Clang++ compilation failed: {err}")
            LLVMValidator.validate_ir_file(output_path)
                
        elif lang == "fortran":
            flang_path = detect_flang()
            if not flang_path:
                raise LLVMCompilationError("Fortran compiler not found on system.")
            success, err = self.fortran.compile(source_path, output_path, flang_path)
            if not success:
                raise LLVMCompilationError(f"Fortran compilation failed: {err}")
            LLVMValidator.validate_ir_file(output_path)
                
        elif lang == "rust":
            rustc_path = detect_rustc()
            if not rustc_path:
                raise LLVMCompilationError("Rust compiler not found on system.")
            success, err = self.rust.compile(source_path, output_path, rustc_path)
            if not success:
                raise LLVMCompilationError(f"Rustc compilation failed: {err}")
            LLVMValidator.validate_ir_file(output_path)
                
        return success, err

    def demangle(self, name: str, language: str) -> str:
        if language == "cpp":
            return CPPCompiler.demangle(name)
        elif language == "rust":
            return RustCompiler.demangle(name)
        elif language == "fortran":
            return FortranCompiler.clean_name(name)
        return name.lstrip('@')
