# Agents API Reference

## Story Agents

### PlotGenerator

```python
from movie_generator.agents.story import PlotGenerator

plot_generator = PlotGenerator(
    agent_id: str,
    model: str = "gpt-4",
    temperature: float = 0.7
)
```

#### Methods
- `async generate_plot(requirements: Dict[str, Any]) -> Dict[str, Any]`
- `async refine_plot(plot: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]`
- `async analyze_plot_structure(plot: Dict[str, Any]) -> Dict[str, Any]`

### CharacterDeveloper

```python
from movie_generator.agents.story import CharacterDeveloper

character_developer = CharacterDeveloper(
    agent_id: str,
    personality_depth: str = "detailed"
)
```

[... continue with all agents ...] 