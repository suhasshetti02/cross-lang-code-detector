"""
Compiler module for Rust files.
Compiles Rust source code to LLVM IR, with robust static analysis fallback.
"""
import subprocess
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class RustCompiler:
    """Handles compilation of Rust files to LLVM IR using rustc."""
    
    def __init__(self, opt_level: str = "2"):
        self.opt_level = opt_level

    def compile(self, source_path: Path, output_path: Path, compiler_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Compile Rust source file to LLVM IR.
        """
        # Create temporary build dir
        temp_dir = output_path.parent / f"rust_build_{source_path.stem}"
        temp_dir.mkdir(exist_ok=True)
        
        cmd = [
            str(compiler_path),
            "--crate-type=lib",
            "-C", f"opt-level={self.opt_level}",
            "-C", "link-dead-code=yes",
            "-C", "codegen-units=1",
            "--emit=llvm-ir",
            str(source_path),
            "-o", str(temp_dir / f"{source_path.stem}.ll")
        ]
        from compiler.compiler_detector import log_command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            generated_ll = temp_dir / f"{source_path.stem}.ll"
            success = result.returncode == 0 and generated_ll.exists()
            log_command(cmd, success, result.stderr or result.stdout)
            if success:
                output_path.write_text(generated_ll.read_text())
                import shutil
                shutil.rmtree(temp_dir)
                return True, None
            else:
                err = result.stderr or result.stdout
                logger.warning(f"Rustc failed for {source_path.name}: {err}")
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
                return False, f"Rustc exit code {result.returncode}: {err}"
        except Exception as e:
            log_command(cmd, False, str(e))
            logger.warning(f"Exception compiling Rust file {source_path.name}: {e}")
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
            return False, str(e)

    @staticmethod
    def demangle(mangled_name: str) -> str:
        """Simple demangler for Rust v0 mangled symbols."""
        name = mangled_name.lstrip('@')
        if not name.startswith("_ZN"):
            return name
        
        # Match standard forms like _ZN9factorial9factorialE
        m = re.match(r'^_ZN\d+([a-zA-Z0-9_]+)\d+([a-zA-Z0-9_]+)E', name)
        if m:
            return m.group(2)
            
        m2 = re.match(r'^_ZN\d+([a-zA-Z0-9_]+)E', name)
        if m2:
            return m2.group(1)
            
        return name.lstrip('_ZN').rstrip('E')
