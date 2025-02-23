import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { SystemMetrics } from '../types/metrics';
import { useWebSocket } from '../hooks/useWebSocket';

const MetricsDashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<SystemMetrics[]>([]);
    const ws = useWebSocket('ws://localhost:8000/ws/system');

    useEffect(() => {
        if (ws) {
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'metrics') {
                    setMetrics(prev => [...prev, data.data].slice(-60)); // Keep last 60 readings
                }
            };
        }
    }, [ws]);

    return (
        <div className="metrics-dashboard">
            <h2>System Metrics</h2>
            
            <div className="metric-card">
                <h3>CPU Usage</h3>
                <Line
                    data={{
                        labels: metrics.map(m => new Date(m.timestamp).toLocaleTimeString()),
                        datasets: [{
                            label: 'CPU Usage %',
                            data: metrics.map(m => m.cpu.usage),
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    }}
                />
            </div>

            <div className="metric-card">
                <h3>Memory Usage</h3>
                <Line
                    data={{
                        labels: metrics.map(m => new Date(m.timestamp).toLocaleTimeString()),
                        datasets: [{
                            label: 'Memory Usage %',
                            data: metrics.map(m => m.memory.usage_percent),
                            borderColor: 'rgb(153, 102, 255)',
                            tension: 0.1
                        }]
                    }}
                />
            </div>

            <div className="metric-card">
                <h3>GPU Usage</h3>
                <Line
                    data={{
                        labels: metrics.map(m => new Date(m.timestamp).toLocaleTimeString()),
                        datasets: [{
                            label: 'GPU Usage %',
                            data: metrics.map(m => m.gpu.usage),
                            borderColor: 'rgb(255, 99, 132)',
                            tension: 0.1
                        }]
                    }}
                />
            </div>

            <div className="metrics-summary">
                <div className="summary-card">
                    <h4>Current Usage</h4>
                    {metrics.length > 0 && (
                        <ul>
                            <li>CPU: {metrics[metrics.length - 1].cpu.usage}%</li>
                            <li>Memory: {metrics[metrics.length - 1].memory.usage_percent}%</li>
                            <li>GPU: {metrics[metrics.length - 1].gpu.usage}%</li>
                            <li>Storage: {metrics[metrics.length - 1].storage.usage}%</li>
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MetricsDashboard; 