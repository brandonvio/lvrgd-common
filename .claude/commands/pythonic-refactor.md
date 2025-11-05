---
name: pythonic-refactor
description: Add type hints and refactor Python code to use Pydantic models without breaking interfaces
---

Analyze the Python file at path: {{python_file_path}} and refactor it with the following improvements WITHOUT breaking the external interface:

## Requirements:

1. **Add Type Hints**:
   - Add comprehensive type hints to all functions, methods, and class attributes
   - Use appropriate typing imports (List, Dict, Optional, Union, Any, etc.)
   - Add return type hints for all functions/methods
   - Use forward references where needed for self-referential types

2. **Pydantic Model Refactoring**:
   - Identify data classes, dictionaries, or classes with validation logic that could benefit from Pydantic
   - Convert appropriate classes to Pydantic BaseModel or create new Pydantic models for data validation
   - Preserve the external interface by maintaining compatibility with existing method signatures
   - Use Pydantic's validation features (validators, Field constraints, etc.) where beneficial
   - For classes that need to remain regular classes, consider using Pydantic models internally for validation

3. **Interface Preservation**:
   - Ensure all public methods maintain their original signatures (can add optional parameters with defaults)
   - Keep return types compatible (e.g., if returning dict, ensure Pydantic model.dict() is used)
   - Maintain backward compatibility for class instantiation
   - Add adapter methods if needed to maintain compatibility

4. **Code Quality**:
   - Ensure all changes maintain or improve code readability
   - Add docstrings if missing, with type information
   - Follow PEP 8 and Python best practices
   - Optimize imports and remove unused ones

## Process:

1. First, read and analyze the file at {{python_file_path}}
2. Identify all opportunities for type hints and Pydantic model usage
3. Create a refactored version that:
   - Adds complete type hints throughout
   - Introduces Pydantic models where appropriate
   - Maintains 100% backward compatibility
4. Write the refactored code back to the file

## Example transformations:

### Before:
```python
class User:
    def __init__(self, name, age, email=None):
        self.name = name
        self.age = age
        self.email = email
    
    def to_dict(self):
        return {"name": self.name, "age": self.age, "email": self.email}
```

### After:
```python
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    name: str
    age: int = Field(gt=0, le=150)
    email: Optional[EmailStr] = None
    
    def __init__(self, name: str, age: int, email: Optional[str] = None) -> None:
        # Maintain compatibility with original constructor
        super().__init__(name=name, age=age, email=email)
    
    def to_dict(self) -> Dict[str, Any]:
        # Maintain original interface
        return self.model_dump()
```

Start by reading the file and analyzing its current structure, then proceed with the refactoring.