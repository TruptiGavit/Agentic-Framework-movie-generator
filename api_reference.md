# Core API Reference

## SystemIntegrator

The main coordinator that manages all system components and orchestrates the movie generation process.




python
from movie_generator import SystemIntegrator
system = SystemIntegrator(
config_path: str = "config",
debug_mode: bool = False
)

#### Methods

#### System Management
- `async initialize_system() -> None`
  - Initializes all system components
  - Sets up agents, pipelines, and resources
  - Raises `SystemInitializationError` if initialization fails

- `async shutdown_system() -> None`
  - Gracefully shuts down all components
  - Saves current state and cleans up resources

#### Project Management
- `async create_project(project_data: Dict[str, Any]) -> str`
  - Creates a new movie generation project
  - Returns project ID
  - Parameters:
    ```python
    project_data = {
        "title": str,
        "description": str,
        "requirements": {
            "style": str,
            "duration": int,
            "target_audience": str,
            "theme": str,
            "mood": str
        },
        "story_elements": Dict[str, Any],
        "technical_requirements": Dict[str, Any]
    }
    ```

- `async get_project_status(project_id: str) -> Dict[str, Any]`
  - Returns current project status
  - Output format:
    ```python
    {
        "status": str,  # "initializing"|"in_progress"|"completed"|"failed"
        "current_stage": str,
        "progress": float,  # 0-100
        "estimated_completion": datetime,
        "current_task": str,
        "errors": List[str]
    }
    ```

#### Pipeline Control
- `async pause_project(project_id: str) -> bool`
- `async resume_project(project_id: str) -> bool`
- `async cancel_project(project_id: str) -> bool`

#### Export and Results
- `async export_project(project_id: str, format: str, output_path: Path) -> bool`
  - Supported formats: "mp4", "mov", "avi"
  - Returns success status

## TaskScheduler

Manages task execution and resource allocation.

python
from movie_generator import TaskScheduler
scheduler = TaskScheduler()



### Methods

#### Task Management
- `async schedule_task(task: Task) -> str`
- `async cancel_task(task_id: str) -> bool`
- `async get_task_status(task_id: str) -> Dict[str, Any]`

#### Resource Management
- `async update_gpu_settings(settings: Dict[str, Any]) -> None`
- `async update_cpu_settings(settings: Dict[str, Any]) -> None`

## SystemMonitor

Monitors system resources and performance.

```python
from movie_generator import SystemMonitor

monitor = SystemMonitor()
```

### Methods

#### Monitoring
- `async get_system_metrics() -> Dict[str, Any]`
- `async get_metrics_summary(metric_type: str) -> Dict[str, Any]`
- `async export_metrics_history(start_time: datetime, end_time: datetime) -> Dict[str, Any]`

#### Alerts
- `register_alert_callback(callback: Callable) -> None`
- `async update_alert_thresholds(thresholds: Dict[str, float]) -> None`

## ConfigManager

Manages system configuration and settings.

```python
from movie_generator import ConfigManager

config_manager = ConfigManager(config_dir: str = "config")
```

### Methods

#### Configuration Management
- `async load_config(config_type: str) -> Dict[str, Any]`
- `async update_config(config_type: str, updates: Dict[str, Any]) -> bool`
- `async validate_config(config_type: str, config: Dict[str, Any]) -> List[str]`

#### Dynamic Updates
- `register_config_callback(config_type: str, callback: Callable) -> None`
- `async reload_config(config_type: Optional[str] = None) -> Dict[str, Any]`