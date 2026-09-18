# Architecture Documentation

## System Design Principles

1. **Separation of Concerns**: Each module handles one responsibility
2. **State Immutability**: UserState mutations happen through explicit methods
3. **Graceful Degradation**: System works without LLM (fallback mode)
4. **Explainability**: Every adaptive decision generates a human-readable explanation
5. **Testability**: Core logic is isolated from I/O for unit testing

## Data Flow