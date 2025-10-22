import csv
from pathlib import Path
from typing import Union

class InteractionStorage:
    def __init__(self, csv_path: str = "interactions.csv"):
        self.csv_path = Path(csv_path)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['independent_variable', 'dependent_variable', 'effect', 'reference', 'date_published'])
    
    def add_interaction(
        self,
        independent_variable: Union[str, tuple],
        dependent_variable: Union[str, tuple],
        effect: Union[str, tuple],
        reference: str,
        date_published: str
    ) -> str:
        """Add a single interaction to the CSV file"""
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            iv = str(independent_variable) if isinstance(independent_variable, tuple) else independent_variable
            dv = str(dependent_variable) if isinstance(dependent_variable, tuple) else dependent_variable
            eff = str(effect) if isinstance(effect, tuple) else effect
            writer.writerow([iv, dv, eff, reference, date_published])
        return f"Interaction stored: {iv} -> {dv} ({eff})"

