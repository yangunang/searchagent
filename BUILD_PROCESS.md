# K8s Deployment Build Process

This document explains how `k8s_deploy_stock.py` works step by step.

## Overview

The deployment script automates the entire process of containerizing and deploying the Stock Search Agent to Kubernetes.

```
python k8s_deploy_stock.py
         ↓
    [1. Import & Initialize]
         ↓
    [2. Check Prerequisites]
         ↓
    [3. Configure Deployer]
         ↓
    [4. Define Deployment Config]
         ↓
    [5. Build Docker Image]
         ↓
    [6. Push to Registry]
         ↓
    [7. Create K8s Resources]
         ↓
    [8. Return Service URL]
```

---

## Code Mapping - Step by Step

### Step 1: Import & Initialize (Lines 1-12)

```python
# Lines 1-4: Module docstring
"""
Kubernetes Deployment for Stock Search Agent
Deploy to K8s cluster with auto-scaling support
"""

# Lines 5-6: Standard imports
import asyncio
import os

# Lines 7-11: Import K8s deployer components
from agentscope_runtime.engine.deployers.kubernetes_deployer import (
    KubernetesDeployManager,
    RegistryConfig,
    K8sConfig,
)

# Line 12: Import app (triggers stock_agent_app.py execution)
from stock_agent_app import app
```

**What happens:**
- Loads the `agentscope_runtime` deployment framework
- Imports the FastAPI app with the agent and endpoints
- When `stock_agent_app` is imported, it initializes:
  - `search_stock_price` tool
  - `AgentScopeAgent` with DashScope model
  - `AgentApp` with `/stock_query`, `/chat`, `/stream_chat` endpoints

---

### Step 2: Check Prerequisites (Lines 130-136)

```python
if __name__ == "__main__":
    # Line 131-132: Print check message
    print("🔍 Checking prerequisites...")

    # Lines 134-136: Validate API key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("⚠️  Warning: DASHSCOPE_API_KEY not set")
        print("   Export it: export DASHSCOPE_API_KEY='your_api_key'")
```

**What happens:**
- Validates that required environment variables are set
- Warns if `DASHSCOPE_API_KEY` is missing (agent won't work without it)

---

### Step 3: Configure Deployer (Lines 21-31)

```python
deployer = KubernetesDeployManager(
    # Lines 22-25: K8s cluster config
    kube_config=K8sConfig(
        k8s_namespace="agentscope-stock",
        kubeconfig_path=None,  # Uses default ~/.kube/config
    ),
    # Lines 26-29: Docker registry config
    registry_config=RegistryConfig(
        registry_url=os.getenv("DOCKER_REGISTRY", "your-registry-url"),
        namespace="agentscope-runtime",
    ),
    # Line 30: Use Deployment (not Job)
    use_deployment=True,
)
```

**What happens:**
- Creates `KubernetesDeployManager` instance
- Loads kubeconfig from `~/.kube/config`
- Connects to K8s cluster
- Configures Docker registry for image push
- Sets `use_deployment=True` to create K8s Deployment (vs one-time Job)

---

### Step 4: Define Deployment Config (Lines 34-83)

```python
deployment_config = {
    # Line 35: Service port
    "port": "8080",

    # Line 36: Number of pod replicas
    "replicas": 2,

    # Lines 37-38: Docker image name/tag
    "image_name": "stock-agent",
    "image_tag": "v1.0",

    # Lines 39-45: Python packages to install
    "requirements": [
        "agentscope",
        "agentscope-runtime",
        "fastapi",
        "uvicorn",
        "requests",
    ],

    # Line 46: Base Docker image
    "base_image": "python:3.10-slim-bookworm",

    # Lines 47-51: Environment variables
    "environment": {
        "PYTHONPATH": "/app",
        "DASHSCOPE_API_KEY": os.environ.get("DASHSCOPE_API_KEY"),
        "LOG_LEVEL": "INFO",
    },

    # Lines 52-80: K8s runtime config
    "runtime_config": {
        # Lines 53-62: Resource requests/limits
        "resources": {
            "requests": {"cpu": "500m", "memory": "1Gi"},
            "limits": {"cpu": "2000m", "memory": "4Gi"},
        },
        # Lines 64-71: Readiness probe
        "readinessProbe": {
            "httpGet": {"path": "/health", "port": 8080},
            "initialDelaySeconds": 10,
            "periodSeconds": 5
        },
        # Lines 72-79: Liveness probe
        "livenessProbe": {
            "httpGet": {"path": "/health", "port": 8080},
            "initialDelaySeconds": 30,
            "periodSeconds": 10
        }
    },

    # Lines 81-82: Build options
    "platform": "linux/amd64",
    "push_to_registry": True,
}
```

**Configuration breakdown:**

| Key | Purpose |
|-----|---------|
| `port` | Service exposed port |
| `replicas` | Number of pod instances |
| `image_name/tag` | Docker image identifier |
| `requirements` | Python packages for container |
| `base_image` | Docker base image |
| `environment` | Container env vars |
| `resources` | CPU/memory limits |
| `readinessProbe` | K8s readiness check |
| `livenessProbe` | K8s health check |

---

### Step 5: Print Build Info (Lines 85-88)

```python
print("📦 Building and pushing container image...")
print(f"   Image: {deployment_config['image_name']}:{deployment_config['image_tag']}")
print(f"   Replicas: {deployment_config['replicas']}")
print(f"   Resources: {deployment_config['runtime_config']['resources']}")
```

**What happens:**
- Logs deployment configuration to console
- Provides visibility into what will be deployed

---

### Step 6: Execute Deployment (Line 92)

```python
try:
    result = await app.deploy(deployer, **deployment_config)
```

**This is the main deployment call.** The `app.deploy()` method performs:

| Sub-step | Action | Details |
|----------|--------|---------|
| 6a | Generate Dockerfile | From `base_image`, `requirements` |
| 6b | Copy app files | `stock_agent_app.py` → container |
| 6c | Build Docker image | `stock-agent:v1.0` |
| 6d | Push to registry | `registry-url/agentscope-runtime/stock-agent:v1.0` |
| 6e | Create Namespace | `agentscope-stock` (if not exists) |
| 6f | Generate Deployment YAML | From `replicas`, `resources`, `probes` |
| 6g | Generate Service YAML | From `port: 8080` |
| 6h | Apply to K8s | Equivalent to `kubectl apply` |
| 6i | Wait for ready | Until pods pass readiness probe |

---

### Step 7: Handle Success (Lines 94-111)

```python
print("\n✅ Deployment successful!")
print(f"📍 Service URL: {result['url']}")
print(f"🔧 Deployment Name: {result.get('deployment_name', 'N/A')}")
print(f"🏷️  Namespace: agentscope-stock")

print("\n📊 Test the deployment:")
print(f"   curl {result['url']}/health")
print(f"   curl -X POST {result['url']}/chat \\")
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"input": [...]}\'')

print("\n🔧 Kubernetes commands:")
print("   kubectl get pods -n agentscope-stock")
print("   kubectl get svc -n agentscope-stock")
print("   kubectl logs -n agentscope-stock -l app=stock-agent")
print("   kubectl scale deployment stock-agent --replicas=5 -n agentscope-stock")

return result
```

**What happens:**
- Prints success message with Service URL
- Provides example curl commands for testing
- Provides kubectl commands for management

---

### Step 8: Handle Failure (Lines 113-120)

```python
except Exception as e:
    print(f"\n❌ Deployment failed: {str(e)}")
    print("\n🔍 Troubleshooting:")
    print("   1. Check Docker is running: docker --version")
    print("   2. Verify K8s access: kubectl cluster-info")
    print("   3. Check registry access: docker login <registry>")
    print("   4. Verify API key: echo $DASHSCOPE_API_KEY")
    raise
```

**What happens:**
- Catches any deployment errors
- Provides troubleshooting steps
- Re-raises exception for visibility

---

### Step 9: Run Main (Lines 138-146)

```python
# Line 139: Execute async deployment
asyncio.run(deploy_stock_agent_to_k8s())

# Lines 142-146: Wait for user exit
print("\n⏸️  Press Ctrl+C to exit (deployment will continue running)")
try:
    input()
except KeyboardInterrupt:
    print("\n👋 Exiting (deployment still active)")
```

**What happens:**
- Runs the async deployment function
- Waits for user input to exit
- Deployment continues running in K8s after script exits

---

## Internal Processes

### Generated Dockerfile

The deployer internally generates a Dockerfile like:

```dockerfile
FROM python:3.10-slim-bookworm

WORKDIR /app

# Install dependencies
RUN pip install agentscope agentscope-runtime fastapi uvicorn requests

# Copy application
COPY stock_agent_app.py /app/

# Set environment
ENV PYTHONPATH=/app
ENV DASHSCOPE_API_KEY=xxx
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8080

# Run FastAPI with uvicorn
CMD ["uvicorn", "stock_agent_app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Generated Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stock-agent
  namespace: agentscope-stock
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stock-agent
  template:
    metadata:
      labels:
        app: stock-agent
    spec:
      containers:
      - name: stock-agent
        image: registry/agentscope-runtime/stock-agent:v1.0
        ports:
        - containerPort: 8080
        env:
        - name: PYTHONPATH
          value: "/app"
        - name: DASHSCOPE_API_KEY
          value: "xxx"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Generated Kubernetes Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: stock-agent
  namespace: agentscope-stock
spec:
  type: LoadBalancer
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
  selector:
    app: stock-agent
```

---

## Timeline

| Time | Action |
|------|--------|
| 0s | Script starts, imports app |
| 1s | Configure deployer |
| 10-60s | Build Docker image |
| 30-120s | Push image to registry |
| 5s | Create K8s namespace |
| 5s | Apply Deployment & Service |
| 30-60s | Wait for pods ready |
| **Total** | **~2-4 minutes** |

---

## Summary Table

| Step | Lines | Action |
|------|-------|--------|
| 1 | 1-12 | Import modules & app |
| 2 | 130-136 | Check prerequisites |
| 3 | 21-31 | Configure deployer |
| 4 | 34-83 | Define deployment config |
| 5 | 85-88 | Print build info |
| **6** | **92** | **Execute deployment** (main work) |
| 7 | 94-111 | Handle success |
| 8 | 113-120 | Handle failure |
| 9 | 138-146 | Run async & wait |

**Key insight**: Line 92 (`app.deploy()`) does 90% of the work - everything else is configuration and output.

---

## Known Issues

Before running, fix these issues:

1. **Missing `/health` endpoint** - Add to `stock_agent_app.py`:
   ```python
   @app.endpoint("/health")
   def health_check():
       return {"status": "healthy"}
   ```

2. **Set environment variables**:
   ```bash
   export DASHSCOPE_API_KEY="your-api-key"
   export DOCKER_REGISTRY="your-registry-url"
   ```

3. **Missing `dashscope` dependency** - Add to requirements list
