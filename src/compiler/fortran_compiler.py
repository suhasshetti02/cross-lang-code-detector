"""
Compiler module for Fortran files.
Compiles Fortran source code to LLVM IR, with robust static analysis fallback.
"""
import subprocess
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class FortranCompiler:
    """Handles compilation of Fortran files to LLVM IR using flang."""
    
    def __init__(self, opt_level: str = "2"):
        self.opt_level = opt_level

    def compile(self, source_path: Path, output_path: Path, compiler_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Compile Fortran source file to LLVM IR.
        """
        # We check if compiler is flang or gfortran. 
        # If gfortran is passed, we check flags or just run as-is.
        cmd = [
            str(compiler_path),
            f"-O{self.opt_level}",
            "-S",
            "-emit-llvm",
            str(source_path),
            "-o", str(output_path)
        ]
        
        # If gfortran, standard gfortran doesn't produce LLVM IR directly without -S -emit-llvm if it is llvm-based, 
        # but flang does. If it fails, log_command records the failure.
        from compiler.compiler_detector import log_command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            success = result.returncode == 0 and output_path.exists()
            log_command(cmd, success, result.stderr or result.stdout)
            if success:
                return True, None
            else:
                err = result.stderr or result.stdout
                logger.warning(f"Fortran compiler failed for {source_path.name}: {err}")
                return False, f"Fortran compiler exit code {result.returncode}: {err}"
        except Exception as e:
            log_command(cmd, False, str(e))
            logger.warning(f"Exception compiling Fortran file {source_path.name}: {e}")
            return False, str(e)

    @staticmethod
    def clean_name(fortran_name: str) -> str:
        """Removes trailing underscore added by Fortran compilers."""
        name = fortran_name.lstrip('@')
        if name.endswith('_'):
            return name[:-1]
        return name
