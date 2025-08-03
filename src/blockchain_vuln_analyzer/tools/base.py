"""
Base class for blockchain vulnerability analysis tools.
"""

import tempfile
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseTool(ABC):
    """Base class for blockchain vulnerability analysis tools."""
    
    def __init__(self, name: str):
        self.name = name
    
    def create_temp_file(self, contract_code: str, suffix: str = '.sol') -> str:
        """Create a temporary file with the given contract code."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
        temp_file.write(contract_code)
        temp_file.close()
        return temp_file.name
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up a temporary file."""
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    
    def validate_input(self, contract_code: Optional[str], contract_file: Optional[str]) -> str:
        """Validate input and return the contract path to use."""
        if contract_code:
            return self.create_temp_file(contract_code)
        elif contract_file:
            if not os.path.exists(contract_file):
                raise ValueError(f"Contract file not found: {contract_file}")
            return contract_file
        else:
            raise ValueError("Either contract_code or contract_file must be provided")
    
    @abstractmethod
    async def analyze(self, **kwargs) -> Dict[str, Any]:
        """Run the analysis tool with the given parameters."""
        pass
    
    @abstractmethod
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        pass
