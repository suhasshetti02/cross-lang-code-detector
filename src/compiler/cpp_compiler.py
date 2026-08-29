"""
Compiler module for C++ files.
Compiles C++ source code to LLVM IR, with robust static analysis fallback.
"""
import subprocess
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class CPPCompiler:
    """Handles compilation of C++ files to LLVM IR using clang++."""
    
    def __init__(self, opt_level: str = "2"):
        self.opt_level = opt_level

    def compile(self, source_path: Path, output_path: Path, compiler_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Compile C++ source file to LLVM IR.
        """
        cmd = [
            str(compiler_path),
            f"-O{self.opt_level}",
            "-S",
            "-emit-llvm",
            "-fno-discard-value-names",
            "-Xclang", "-disable-O0-optnone",
            str(source_path),
            "-o", str(output_path)
        ]
        from compiler.compiler_detector import log_command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            success = result.returncode == 0 and output_path.exists()
            log_command(cmd, success, result.stderr or result.stdout)
            if success:
                return True, None
            else:
                err = result.stderr or result.stdout
                logger.warning(f"Clang++ failed for {source_path.name}: {err}")
                return False, f"Clang++ exit code {result.returncode}: {err}"
        except Exception as e:
            log_command(cmd, False, str(e))
            logger.warning(f"Exception compiling C++ file {source_path.name}: {e}")
            return False, str(e)

    @staticmethod
    def demangle(mangled_name: str) -> str:
        """Simple regex-based demangler for typical GCC/Clang names."""
        if not mangled_name.startswith("_Z"):
            return mangled_name.lstrip('@')
        
        # Match standard forms like _ZN9quicksort10quick_sortE or _Z9factoriali
        m = re.match(r'^_Z(?:N\d+)?(\d+)([a-zA-Z0-9_]+)E?', mangled_name)
        if m:
            length = int(m.group(1))
            name = m.group(2)[:length]
            return name
        
        # Backup simple match
        m2 = re.match(r'^_Z(\d+)([a-zA-Z0-9_]+)', mangled_name)
        if m2:
            length = int(m2.group(1))
            name = m2.group(2)[:length]
            return name
            
        return mangled_name.lstrip('_Z').lstrip('@')
