from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import psutil
import logging
import json
from pathlib import Path
import time

@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    timestamp: datetime

class SystemMonitor:
    """Monitors system resources and performance metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # System settings
        self.settings = {
            "metrics_interval": 60,  # seconds
            "alert_threshold": 90,  # percentage
            "log_metrics": True
        }
        
        # Storage limits
        self.storage_limits = {
            "project_files": "100GB",
            "temp_files": "20GB",
            "output_files": "50GB"
        }
        
        # Retention periods (in days)
        self.retention_periods = {
            "output_files": 30,
            "temp_files": 1,
            "logs": 7
        }
        
        # Metrics storage
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {
            "cpu": [],
            "memory": [],
            "gpu": [],
            "storage": [],
            "network": []
        }
        
        # Active monitoring tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # System state
        self.is_monitoring = False
        
        # Alert callbacks
        self.alert_callbacks: List[callable] = []
    
    async def start(self):
        """Start system monitoring."""
        self.logger.info("Starting system monitoring...")
        self.is_monitoring = True
        
        # Start monitoring tasks
        self._monitoring_task = asyncio.create_task(self._monitor_metrics())
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def stop(self):
        """Stop system monitoring."""
        self.logger.info("Stopping system monitoring...")
        self.is_monitoring = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
    
    async def update_settings(self, settings: Dict[str, Any]):
        """Update monitoring settings."""
        self.logger.info("Updating monitoring settings...")
        
        if "metrics_interval" in settings:
            self.settings["metrics_interval"] = settings["metrics_interval"]
        
        if "alert_threshold" in settings:
            self.settings["alert_threshold"] = settings["alert_threshold"]
        
        if "log_metrics" in settings:
            self.settings["log_metrics"] = settings["log_metrics"]
    
    async def update_storage_limits(self, storage_type: str, limit: str):
        """Update storage limits."""
        self.logger.info(f"Updating storage limit for {storage_type} to {limit}")
        
        if storage_type in self.storage_limits:
            self.storage_limits[storage_type] = limit
            
            # Check current usage against new limit
            await self._check_storage_usage(storage_type)
    
    async def update_retention_period(self, file_type: str, days: int):
        """Update file retention period."""
        self.logger.info(f"Updating retention period for {file_type} to {days} days")
        
        if file_type in self.retention_periods:
            self.retention_periods[file_type] = days
            
            # Trigger cleanup with new retention period
            await self._cleanup_expired_files(file_type)
    
    def register_alert_callback(self, callback: callable):
        """Register callback for system alerts."""
        self.alert_callbacks.append(callback)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return {
            "cpu": await self._get_cpu_metrics(),
            "memory": await self._get_memory_metrics(),
            "gpu": await self._get_gpu_metrics(),
            "storage": await self._get_storage_metrics(),
            "network": await self._get_network_metrics()
        }
    
    async def _monitor_metrics(self):
        """Monitor system metrics periodically."""
        while self.is_monitoring:
            try:
                metrics = await self.get_system_metrics()
                
                # Store metrics history
                for metric_type, values in metrics.items():
                    self.metrics_history[metric_type].append({
                        "timestamp": datetime.now().isoformat(),
                        "values": values
                    })
                
                # Check thresholds and trigger alerts
                await self._check_thresholds(metrics)
                
                # Log metrics if enabled
                if self.settings["log_metrics"]:
                    self.logger.info(f"System metrics: {metrics}")
                
                await asyncio.sleep(self.settings["metrics_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring metrics: {str(e)}")
                await asyncio.sleep(5)  # Retry after delay
    
    async def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and trigger alerts."""
        alerts = []
        
        # Check CPU usage
        if metrics["cpu"]["usage"] > self.settings["alert_threshold"]:
            alerts.append({
                "type": "cpu",
                "message": f"High CPU usage: {metrics['cpu']['usage']}%"
            })
        
        # Check memory usage
        if metrics["memory"]["usage_percent"] > self.settings["alert_threshold"]:
            alerts.append({
                "type": "memory",
                "message": f"High memory usage: {metrics['memory']['usage_percent']}%"
            })
        
        # Check storage usage
        for storage_type, usage in metrics["storage"]["usage"].items():
            if usage["percent"] > self.settings["alert_threshold"]:
                alerts.append({
                    "type": "storage",
                    "message": f"High storage usage for {storage_type}: {usage['percent']}%"
                })
        
        # Trigger alerts
        for alert in alerts:
            await self._trigger_alert(alert)
    
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {str(e)}")
    
    async def _periodic_cleanup(self):
        """Perform periodic cleanup tasks."""
        while self.is_monitoring:
            try:
                # Cleanup expired files
                for file_type in self.retention_periods:
                    await self._cleanup_expired_files(file_type)
                
                # Trim metrics history
                await self._trim_metrics_history()
                
                await asyncio.sleep(3600)  # Check every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {str(e)}")
                await asyncio.sleep(60)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        return SystemMetrics(
            cpu_usage=psutil.cpu_percent(interval=1),
            memory_usage=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            network_io={
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv
            },
            process_count=len(psutil.pids()),
            timestamp=datetime.now()
        )
    
    async def _check_thresholds(self, metrics: SystemMetrics):
        """Check metrics against thresholds."""
        for metric_name, threshold in self.alert_thresholds.items():
            metric_value = getattr(metrics, metric_name)
            if metric_value > threshold:
                await self._create_alert(
                    level="warning",
                    message=f"{metric_name} exceeded threshold: {metric_value}%",
                    metric_name=metric_name,
                    metric_value=metric_value,
                    threshold=threshold
                )
    
    async def _create_alert(self, level: str, message: str, **details):
        """Create and log system alert."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details
        }
        
        self.active_alerts.append(alert)
        self.logger.warning(f"System Alert: {message}")
        
        # Save alert to file
        await self._save_alert(alert)
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        retention_time = datetime.now() - timedelta(seconds=self.history_retention)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > retention_time
        ]
    
    async def _save_current_metrics(self, metrics: SystemMetrics):
        """Save current metrics to file."""
        metrics_file = self.output_dir / "current_metrics.json"
        metrics_data = {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "network_io": metrics.network_io,
            "process_count": metrics.process_count
        }
        
        async with aiofiles.open(metrics_file, 'w') as f:
            await f.write(json.dumps(metrics_data, indent=2))
    
    async def _save_alert(self, alert: Dict[str, Any]):
        """Save alert to file."""
        alert_file = self.output_dir / "alerts.log"
        async with aiofiles.open(alert_file, 'a') as f:
            await f.write(json.dumps(alert) + "\n")
    
    async def _save_metrics_history(self):
        """Save metrics history to file."""
        history_file = self.output_dir / "metrics_history.json"
        history_data = [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_usage": m.cpu_usage,
                "memory_usage": m.memory_usage,
                "disk_usage": m.disk_usage,
                "network_io": m.network_io,
                "process_count": m.process_count
            }
            for m in self.metrics_history
        ]
        
        async with aiofiles.open(history_file, 'w') as f:
            await f.write(json.dumps(history_data, indent=2))
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics."""
        return self.current_metrics
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts."""
        return self.active_alerts

    async def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU metrics."""
        try:
            return {
                "usage": psutil.cpu_percent(interval=1),
                "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
                "load_avg": psutil.getloadavg(),
                "frequency": {
                    "current": psutil.cpu_freq().current,
                    "min": psutil.cpu_freq().min,
                    "max": psutil.cpu_freq().max
                },
                "core_count": psutil.cpu_count(logical=False),
                "thread_count": psutil.cpu_count(logical=True)
            }
        except Exception as e:
            self.logger.error(f"Error collecting CPU metrics: {str(e)}")
            return {"error": str(e)}

    async def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory metrics."""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            return {
                "virtual": {
                    "total": virtual_mem.total,
                    "available": virtual_mem.available,
                    "used": virtual_mem.used,
                    "free": virtual_mem.free,
                    "usage_percent": virtual_mem.percent
                },
                "swap": {
                    "total": swap_mem.total,
                    "used": swap_mem.used,
                    "free": swap_mem.free,
                    "usage_percent": swap_mem.percent
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting memory metrics: {str(e)}")
            return {"error": str(e)}

    async def _get_gpu_metrics(self) -> Dict[str, Any]:
        """Get GPU metrics."""
        try:
            # This implementation assumes NVIDIA GPUs using nvidia-smi
            # You might need to modify this based on your GPU setup
            import pynvml
            
            pynvml.nvmlInit()
            gpu_metrics = []
            
            for i in range(pynvml.nvmlDeviceGetCount()):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                gpu_metrics.append({
                    "id": i,
                    "name": pynvml.nvmlDeviceGetName(handle),
                    "memory": {
                        "total": info.total,
                        "used": info.used,
                        "free": info.free,
                        "usage_percent": (info.used / info.total) * 100
                    },
                    "utilization": {
                        "gpu": utilization.gpu,
                        "memory": utilization.memory
                    },
                    "temperature": pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                })
            
            return {"devices": gpu_metrics}
        except ImportError:
            return {"error": "GPU monitoring not available - pynvml not installed"}
        except Exception as e:
            self.logger.error(f"Error collecting GPU metrics: {str(e)}")
            return {"error": str(e)}

    async def _get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage metrics."""
        try:
            storage_metrics = {"usage": {}}
            
            # Check each storage location
            for storage_type, limit in self.storage_limits.items():
                path = self._get_storage_path(storage_type)
                usage = psutil.disk_usage(str(path))
                
                storage_metrics["usage"][storage_type] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                    "limit": self._parse_size(limit)
                }
            
            return storage_metrics
        except Exception as e:
            self.logger.error(f"Error collecting storage metrics: {str(e)}")
            return {"error": str(e)}

    async def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network metrics."""
        try:
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections()
            
            return {
                "io_counters": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "error_in": net_io.errin,
                    "error_out": net_io.errout,
                    "drop_in": net_io.dropin,
                    "drop_out": net_io.dropout
                },
                "connection_count": len(net_connections),
                "interfaces": self._get_network_interfaces()
            }
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {str(e)}")
            return {"error": str(e)}

    def _get_network_interfaces(self) -> Dict[str, Any]:
        """Get network interface information."""
        interfaces = {}
        
        for interface, addresses in psutil.net_if_addrs().items():
            interfaces[interface] = {
                "addresses": [
                    {
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "family": str(addr.family)
                    }
                    for addr in addresses
                ],
                "stats": self._get_interface_stats(interface)
            }
        
        return interfaces

    def _get_interface_stats(self, interface: str) -> Dict[str, Any]:
        """Get statistics for a network interface."""
        try:
            stats = psutil.net_if_stats()[interface]
            return {
                "isup": stats.isup,
                "speed": stats.speed,
                "mtu": stats.mtu,
                "duplex": str(stats.duplex)
            }
        except Exception:
            return {"error": "Stats not available"}

    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '100GB') to bytes."""
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4
        }
        
        size = size_str.strip()
        for unit, multiplier in units.items():
            if size.endswith(unit):
                try:
                    number = float(size[:-len(unit)])
                    return int(number * multiplier)
                except ValueError:
                    return 0
        return 0

    def _get_storage_path(self, storage_type: str) -> Path:
        """Get path for storage type."""
        base_path = Path("data")
        return base_path / storage_type

    async def _trim_metrics_history(self):
        """Trim metrics history to prevent memory overflow."""
        try:
            # Keep last 24 hours of metrics by default
            max_age = timedelta(hours=24)
            current_time = datetime.now()
            
            for metric_type in self.metrics_history:
                self.metrics_history[metric_type] = [
                    metric for metric in self.metrics_history[metric_type]
                    if (current_time - datetime.fromisoformat(metric["timestamp"])) <= max_age
                ]
                
        except Exception as e:
            self.logger.error(f"Error trimming metrics history: {str(e)}")

    async def _cleanup_expired_files(self, file_type: str):
        """Clean up expired files based on retention period."""
        try:
            retention_days = self.retention_periods.get(file_type)
            if not retention_days:
                return
            
            base_path = self._get_storage_path(file_type)
            if not base_path.exists():
                return
            
            cutoff_time = time.time() - (retention_days * 86400)  # Convert days to seconds
            
            for item in base_path.rglob("*"):
                if item.is_file():
                    try:
                        if item.stat().st_mtime < cutoff_time:
                            item.unlink()
                            self.logger.info(f"Deleted expired file: {item}")
                    except Exception as e:
                        self.logger.error(f"Error deleting file {item}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up {file_type} files: {str(e)}")

    async def _check_storage_usage(self, storage_type: str):
        """Check storage usage against limits."""
        try:
            path = self._get_storage_path(storage_type)
            if not path.exists():
                return
            
            usage = psutil.disk_usage(str(path))
            limit = self._parse_size(self.storage_limits[storage_type])
            
            if usage.used > limit:
                await self._trigger_alert({
                    "type": "storage_limit",
                    "message": f"Storage limit exceeded for {storage_type}",
                    "storage_type": storage_type,
                    "used": usage.used,
                    "limit": limit
                })
                
                # Attempt emergency cleanup
                await self._emergency_storage_cleanup(storage_type)
            
        except Exception as e:
            self.logger.error(f"Error checking storage usage for {storage_type}: {str(e)}")

    async def _emergency_storage_cleanup(self, storage_type: str):
        """Perform emergency cleanup when storage limits are exceeded."""
        try:
            self.logger.warning(f"Performing emergency cleanup for {storage_type}")
            
            # Reduce retention period temporarily
            original_retention = self.retention_periods.get(storage_type, 30)
            temp_retention = max(1, original_retention // 2)
            
            # Perform aggressive cleanup
            await self._cleanup_expired_files(storage_type)
            
            # Clean up old metrics history
            if storage_type == "metrics":
                await self._trim_metrics_history()
            
            # Restore original retention period
            self.retention_periods[storage_type] = original_retention
            
        except Exception as e:
            self.logger.error(f"Error in emergency cleanup for {storage_type}: {str(e)}")

    async def export_metrics_history(self, metric_type: Optional[str] = None,
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Export metrics history within specified time range."""
        try:
            if metric_type and metric_type not in self.metrics_history:
                raise ValueError(f"Invalid metric type: {metric_type}")
            
            export_data = {}
            current_time = datetime.now()
            
            for mtype, metrics in self.metrics_history.items():
                if metric_type and mtype != metric_type:
                    continue
                
                filtered_metrics = []
                for metric in metrics:
                    metric_time = datetime.fromisoformat(metric["timestamp"])
                    
                    if start_time and metric_time < start_time:
                        continue
                    if end_time and metric_time > end_time:
                        continue
                    
                    filtered_metrics.append(metric)
                
                if filtered_metrics:
                    export_data[mtype] = filtered_metrics
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics history: {str(e)}")
            raise

    async def get_metrics_summary(self, metric_type: str,
                                duration: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get summary of metrics for specified duration."""
        try:
            if metric_type not in self.metrics_history:
                raise ValueError(f"Invalid metric type: {metric_type}")
            
            start_time = datetime.now() - duration
            relevant_metrics = [
                metric["values"] for metric in self.metrics_history[metric_type]
                if datetime.fromisoformat(metric["timestamp"]) >= start_time
            ]
            
            if not relevant_metrics:
                return {"error": "No metrics available for specified duration"}
            
            # Calculate summary statistics
            summary = {
                "count": len(relevant_metrics),
                "duration": str(duration),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
            
            # Add metric-specific summaries
            if metric_type == "cpu":
                summary.update(self._summarize_cpu_metrics(relevant_metrics))
            elif metric_type == "memory":
                summary.update(self._summarize_memory_metrics(relevant_metrics))
            elif metric_type == "storage":
                summary.update(self._summarize_storage_metrics(relevant_metrics))
            elif metric_type == "network":
                summary.update(self._summarize_network_metrics(relevant_metrics))
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating metrics summary: {str(e)}")
            return {"error": str(e)}

    def _summarize_cpu_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize CPU metrics."""
        try:
            cpu_usages = [m["usage"] for m in metrics]
            per_cpu_usages = [m["per_cpu"] for m in metrics]
            
            summary = {
                "usage": {
                    "average": sum(cpu_usages) / len(cpu_usages),
                    "max": max(cpu_usages),
                    "min": min(cpu_usages)
                },
                "per_cpu_stats": self._calculate_per_cpu_stats(per_cpu_usages),
                "frequency": {
                    "current": metrics[-1]["frequency"]["current"],
                    "min": metrics[-1]["frequency"]["min"],
                    "max": metrics[-1]["frequency"]["max"]
                }
            }
            
            return summary
        except Exception as e:
            self.logger.error(f"Error summarizing CPU metrics: {str(e)}")
            return {"error": str(e)}

    def _summarize_memory_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize memory metrics."""
        try:
            virtual_usages = [m["virtual"]["usage_percent"] for m in metrics]
            swap_usages = [m["swap"]["usage_percent"] for m in metrics]
            
            latest = metrics[-1]
            summary = {
                "virtual": {
                    "usage_percent": {
                        "average": sum(virtual_usages) / len(virtual_usages),
                        "max": max(virtual_usages),
                        "min": min(virtual_usages)
                    },
                    "total": latest["virtual"]["total"],
                    "current_used": latest["virtual"]["used"],
                    "current_free": latest["virtual"]["free"]
                },
                "swap": {
                    "usage_percent": {
                        "average": sum(swap_usages) / len(swap_usages),
                        "max": max(swap_usages),
                        "min": min(swap_usages)
                    },
                    "total": latest["swap"]["total"],
                    "current_used": latest["swap"]["used"],
                    "current_free": latest["swap"]["free"]
                }
            }
            
            return summary
        except Exception as e:
            self.logger.error(f"Error summarizing memory metrics: {str(e)}")
            return {"error": str(e)}

    def _summarize_storage_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize storage metrics."""
        try:
            summary = {"storage_types": {}}
            latest = metrics[-1]
            
            for storage_type, usage in latest["usage"].items():
                usages = [m["usage"][storage_type]["percent"] for m in metrics]
                
                summary["storage_types"][storage_type] = {
                    "usage_percent": {
                        "average": sum(usages) / len(usages),
                        "max": max(usages),
                        "min": min(usages)
                    },
                    "total": usage["total"],
                    "current_used": usage["used"],
                    "current_free": usage["free"],
                    "limit": usage["limit"]
                }
            
            return summary
        except Exception as e:
            self.logger.error(f"Error summarizing storage metrics: {str(e)}")
            return {"error": str(e)}

    def _summarize_network_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize network metrics."""
        try:
            # Calculate transfer rates
            transfer_rates = []
            for i in range(1, len(metrics)):
                prev = metrics[i-1]["io_counters"]
                curr = metrics[i]["io_counters"]
                time_diff = self.settings["metrics_interval"]
                
                transfer_rates.append({
                    "bytes_sent_rate": (curr["bytes_sent"] - prev["bytes_sent"]) / time_diff,
                    "bytes_recv_rate": (curr["bytes_recv"] - prev["bytes_recv"]) / time_diff
                })
            
            latest = metrics[-1]
            summary = {
                "transfer_rates": {
                    "bytes_sent": {
                        "average": sum(r["bytes_sent_rate"] for r in transfer_rates) / len(transfer_rates),
                        "max": max(r["bytes_sent_rate"] for r in transfer_rates),
                        "min": min(r["bytes_sent_rate"] for r in transfer_rates)
                    },
                    "bytes_recv": {
                        "average": sum(r["bytes_recv_rate"] for r in transfer_rates) / len(transfer_rates),
                        "max": max(r["bytes_recv_rate"] for r in transfer_rates),
                        "min": min(r["bytes_recv_rate"] for r in transfer_rates)
                    }
                },
                "total_transfer": {
                    "bytes_sent": latest["io_counters"]["bytes_sent"],
                    "bytes_recv": latest["io_counters"]["bytes_recv"],
                    "packets_sent": latest["io_counters"]["packets_sent"],
                    "packets_recv": latest["io_counters"]["packets_recv"]
                },
                "errors": {
                    "in": latest["io_counters"]["error_in"],
                    "out": latest["io_counters"]["error_out"]
                },
                "drops": {
                    "in": latest["io_counters"]["drop_in"],
                    "out": latest["io_counters"]["drop_out"]
                },
                "connection_count": latest["connection_count"]
            }
            
            return summary
        except Exception as e:
            self.logger.error(f"Error summarizing network metrics: {str(e)}")
            return {"error": str(e)}

    def _calculate_per_cpu_stats(self, per_cpu_metrics: List[List[float]]) -> Dict[str, Any]:
        """Calculate statistics for per-CPU metrics."""
        try:
            num_cpus = len(per_cpu_metrics[0])
            per_cpu_stats = []
            
            for cpu_idx in range(num_cpus):
                cpu_usages = [metrics[cpu_idx] for metrics in per_cpu_metrics]
                per_cpu_stats.append({
                    "cpu_id": cpu_idx,
                    "average": sum(cpu_usages) / len(cpu_usages),
                    "max": max(cpu_usages),
                    "min": min(cpu_usages)
                })
            
            return {
                "per_cpu": per_cpu_stats,
                "overall": {
                    "average_deviation": self._calculate_cpu_deviation(per_cpu_stats),
                    "balanced": self._check_cpu_balance(per_cpu_stats)
                }
            }
        except Exception as e:
            self.logger.error(f"Error calculating per-CPU stats: {str(e)}")
            return {"error": str(e)}

    def _calculate_cpu_deviation(self, per_cpu_stats: List[Dict[str, Any]]) -> float:
        """Calculate average deviation between CPU usages."""
        try:
            averages = [stats["average"] for stats in per_cpu_stats]
            mean = sum(averages) / len(averages)
            deviation = sum(abs(avg - mean) for avg in averages) / len(averages)
            return deviation
        except Exception:
            return -1.0

    def _check_cpu_balance(self, per_cpu_stats: List[Dict[str, Any]]) -> bool:
        """Check if CPU load is balanced."""
        try:
            deviation = self._calculate_cpu_deviation(per_cpu_stats)
            # Consider balanced if average deviation is less than 20%
            return deviation < 20.0
        except Exception:
            return False 