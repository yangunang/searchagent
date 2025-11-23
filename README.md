# NVIDIA Stock Search Agent - Kubernetes Deployment Demo

Demo implementation based on AgentScope Runtime advanced deployment guide, featuring a stock search agent that queries NVIDIA and other stock prices.

## 📋 Features

- **ReAct Agent** with stock price search tool
- **Kubernetes Deployment** with auto-scaling
- **Multiple Endpoints**: sync, async, and streaming
- **Health Checks** and resource limits
- **High Availability** with 2+ replicas

## 🔧 Prerequisites

```bash
# 1. Install dependencies
pip install agentscope-runtime[deployment]

# 2. Set up environment
export DASHSCOPE_API_KEY="your_qwen_api_key"
export DOCKER_REGISTRY="your-registry-url"  # Optional

# 3. Verify Kubernetes access
kubectl cluster-info
kubectl get nodes

# 4. Docker registry access
docker login your-registry-url
```

## 🚀 Quick Start

### Deploy to Kubernetes

```bash
# Deploy the agent
python k8s_deploy_stock.py
```

### Test the Deployment

```bash
# Health check
curl http://your-service-url:8080/health

# Query NVIDIA stock
curl -X POST http://your-service-url:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{
      "role": "user",
      "content": [{"type": "text", "text": "What is NVIDIA current stock price?"}]
    }],
    "session_id": "demo123"
  }'

# Stream response
curl -X POST http://your-service-url:8080/stream_chat \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{
      "role": "user",
      "content": [{"type": "text", "text": "Tell me about NVDA stock"}]
    }],
    "session_id": "demo123"
  }'
```

## 📊 Current NVIDIA Stock Data

Based on recent market data (Nov 23, 2025):
- **Price**: $180.05
- **Change**: +1.06%
- **Market Cap**: $4.4T
- **P/E Ratio**: 44.31
- **52-Week Range**: $86.62 - $212.19

## 🎯 Architecture

```
┌─────────────────────────────────────────┐
│         Kubernetes Cluster               │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │  Stock Agent Deployment          │   │
│  │  (2 replicas)                    │   │
│  │                                  │   │
│  │  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Pod 1   │  │  Pod 2   │    │   │
│  │  │          │  │          │    │   │
│  │  │ Agent    │  │ Agent    │    │   │
│  │  │ + Tools  │  │ + Tools  │    │   │
│  │  └──────────┘  └──────────┘    │   │
│  └─────────────────────────────────┘   │
│               │                          │
│               ▼                          │
│     ┌──────────────────┐                │
│     │  Service (LB)    │                │
│     │  Port: 8080      │                │
│     └──────────────────┘                │
└─────────────────────────────────────────┘
```

## 📝 Kubernetes Management

```bash
# View pods
kubectl get pods -n agentscope-stock

# Check logs
kubectl logs -n agentscope-stock -l app=stock-agent

# Scale deployment
kubectl scale deployment stock-agent --replicas=5 -n agentscope-stock

# Get service details
kubectl get svc -n agentscope-stock

# Port forward for local testing
kubectl port-forward -n agentscope-stock svc/stock-agent 8080:8080
```

## 🔍 Monitoring

```bash
# Watch pod status
kubectl get pods -n agentscope-stock -w

# Describe deployment
kubectl describe deployment stock-agent -n agentscope-stock

# View events
kubectl get events -n agentscope-stock --sort-by='.lastTimestamp'
```

## 🧹 Cleanup

```bash
# Delete deployment
kubectl delete deployment stock-agent -n agentscope-stock

# Delete entire namespace
kubectl delete namespace agentscope-stock
```

## 📚 Supported Stock Symbols

- **NVDA** - NVIDIA Corporation
- **AAPL** - Apple Inc.
- **MSFT** - Microsoft Corporation

## 🛠️ Customization

### Add More Stocks

Edit `stock_agent_app.py`:

```python
stock_data = {
    "TSLA": {
        "symbol": "TSLA",
        "company": "Tesla Inc.",
        "price": 234.50,
        # ... more data
    }
}
```

### Adjust Resources

Edit `k8s_deploy_stock.py`:

```python
"resources": {
    "requests": {"cpu": "1000m", "memory": "2Gi"},
    "limits": {"cpu": "4000m", "memory": "8Gi"}
}
```

### Scale Replicas

```bash
kubectl scale deployment stock-agent --replicas=10 -n agentscope-stock
```

## 🔗 References

- [AgentScope Runtime Docs](https://runtime.agentscope.io/zh/advanced_deployment.html)
- NVIDIA Stock: Currently trading at ~$180.05
- Kubernetes Docs: https://kubernetes.io/docs/

## ⚡ Performance Tips

1. **Resource Optimization**: Adjust CPU/memory based on load
2. **Horizontal Scaling**: Use HPA for auto-scaling
3. **Caching**: Add Redis for stock data caching
4. **Load Balancing**: K8s service handles distribution
5. **Health Checks**: Ensure proper probe configuration

## 📞 Support

For issues with:
- **AgentScope**: https://github.com/modelscope/agentscope
- **Kubernetes**: Check cluster logs and events
- **API Keys**: Verify DASHSCOPE_API_KEY is set
