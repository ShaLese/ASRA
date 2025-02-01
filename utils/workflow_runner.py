"""
Workflow Runner Module
Handles the execution of research workflow by converting notebooks to scripts
and running them in a controlled environment.
"""

import sys
from pathlib import Path
import nbformat
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
import json
import traceback

logger = logging.getLogger(__name__)

class WorkflowRunner:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.script_dir = output_dir / 'scripts'
        self.script_dir.mkdir(exist_ok=True)
        
    def notebook_to_script(self, notebook_path: Path) -> Path:
        """Convert a Jupyter notebook to a Python script."""
        try:
            # Read notebook
            with open(notebook_path) as f:
                nb = nbformat.read(f, as_version=4)
            
            # Extract code cells
            code_cells = [
                cell.source for cell in nb.cells 
                if cell.cell_type == 'code'
            ]
            
            # Create script content with proper imports
            script_content = "\n\n".join([
                "import sys",
                "from pathlib import Path",
                "sys.path.append(str(Path(__file__).parent.parent))",
                "\n".join(code_cells)
            ])
            
            # Save script
            script_path = self.script_dir / f"{notebook_path.stem}.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
                
            return script_path
            
        except Exception as e:
            logger.error(f"Error converting notebook {notebook_path}: {str(e)}")
            raise
    
    def run_script(self, script_path: Path, cwd: Optional[Path] = None) -> Dict:
        """Run a Python script and capture its output."""
        try:
            # Set working directory
            if cwd is None:
                cwd = script_path.parent
                
            # Run script with proper environment
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                env={
                    **dict(os.environ),
                    'PYTHONPATH': str(script_path.parent.parent)
                }
            )
            
            # Process result
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            return {
                'success': success,
                'output': output,
                'script': str(script_path)
            }
            
        except Exception as e:
            logger.error(f"Error running script {script_path}: {str(e)}")
            return {
                'success': False,
                'output': str(e),
                'script': str(script_path)
            }
    
    def run_workflow(self, notebook_paths: List[Path]) -> Dict:
        """Run the entire research workflow by converting and executing notebooks."""
        try:
            results = {}
            
            # Convert notebooks to scripts
            script_paths = []
            for nb_path in notebook_paths:
                try:
                    script_path = self.notebook_to_script(nb_path)
                    script_paths.append(script_path)
                except Exception as e:
                    results[nb_path.stem] = {
                        'success': False,
                        'output': f"Conversion failed: {str(e)}",
                        'script': None
                    }
            
            # Run scripts in parallel
            with ThreadPoolExecutor() as executor:
                future_to_script = {
                    executor.submit(self.run_script, script_path): script_path
                    for script_path in script_paths
                }
                
                for future in future_to_script:
                    script_path = future_to_script[future]
                    try:
                        result = future.result()
                        results[script_path.stem] = result
                    except Exception as e:
                        results[script_path.stem] = {
                            'success': False,
                            'output': f"Execution failed: {str(e)}",
                            'script': str(script_path)
                        }
            
            return results
            
        except Exception as e:
            logger.error(f"Error running workflow: {str(e)}\n{traceback.format_exc()}")
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
