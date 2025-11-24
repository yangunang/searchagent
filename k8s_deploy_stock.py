"""
Kubernetes Deployment for Stock Search Agent
Deploy to K8s cluster with auto-scaling support
"""
import asyncio
import os
import subprocess
import sys
# Add local agentscope-runtime to path to ensure we use the patched version
sys.path.insert(0, os.path.join(os.getcwd(), "agentscope-runtime", "src"))

from agentscope_runtime.engine.deployers.kubernetes_deployer import (
    KubernetesDeployManager,
    RegistryConfig,
    K8sConfig,
)
import agentscope_runtime
print(f"🔍 Loaded agentscope_runtime from: {agentscope_runtime.__file__}")
from stock_agent_app import app


async def deploy_stock_agent_to_k8s():
    """Deploy Stock Search Agent to Kubernetes"""
    
    print("🚀 Starting Kubernetes deployment...")
    
    # Configure Kubernetes deployer
    deployer = KubernetesDeployManager(
        kube_config=K8sConfig(
            k8s_namespace="agentscope-stock",  # Dedicated namespace for stock agent
            kubeconfig_path=None,  # Uses default ~/.kube/config
        ),
        registry_config=RegistryConfig(
            registry_url=os.getenv("your-registry-url"),
            namespace="agentscope-runtime",
        ),
        use_deployment=True,  # Use K8s Deployment instead of Job
    )
    
    # Define deployment configuration
    deployment_config = {
        "port": "8080",
        "replicas": 2,  # Start with 2 replicas for HA
        "image_name": "stock-agent",
        "image_tag": subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip(),
        "requirements": [
            "agentscope",
            "agentscope-runtime",
            "fastapi",
            "uvicorn",
            "requests",
        ],
        "base_image": "python:3.10-slim-bookworm",
        "environment": {
            "PYTHONPATH": "/app",
            "DASHSCOPE_API_KEY": os.environ.get("DASHSCOPE_API_KEY"),
            "LOG_LEVEL": "INFO",
        },
        "runtime_config": {
            "resources": {
                "requests": {
                    "cpu": "500m",  # 0.5 CPU cores
                    "memory": "1Gi"  # 1GB RAM
                },
                "limits": {
                    "cpu": "2000m",  # 2 CPU cores max
                    "memory": "4Gi"  # 4GB RAM max
                },
            },
            # Health checks
            "readinessProbe": {
                "httpGet": {
                    "path": "/health",
                    "port": 8080
                },
                "initialDelaySeconds": 10,
                "periodSeconds": 5
            },
            "livenessProbe": {
                "httpGet": {
                    "path": "/health",
                    "port": 8080
                },
                "initialDelaySeconds": 30,
                "periodSeconds": 10
            },
            "image_pull_secrets": ["regcred"],  # Secrets for pulling images from private registry
        },
        "platform": "linux/amd64",
        "push_to_registry": True,  # Push image to registry
    }
    
    print("📦 Building and pushing container image...")
    print(f"   Image: {deployment_config['image_name']}:{deployment_config['image_tag']}")
    print(f"   Replicas: {deployment_config['replicas']}")
    print(f"   Resources: {deployment_config['runtime_config']['resources']}")
    
    # Deploy to Kubernetes
    try:
        result = await app.deploy(deployer, **deployment_config)
        
        print("\n✅ Deployment successful!")
        print(f"📍 Service URL: {result['url']}")
        print(f"🔧 Deployment Name: {result.get('deployment_name', 'N/A')}")
        print(f"🏷️  Namespace: agentscope-stock")
        
        print("\n📊 Test the deployment:")
        print(f"   curl {result['url']}/health")
        print(f"   curl -X POST {result['url']}/chat \\")
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"input": [{"role": "user", "content": [{"type": "text", "text": "What is NVIDIA stock price?"}]}], "session_id": "test123"}\'')
        
        print("\n🔧 Kubernetes commands:")
        print("   kubectl get pods -n agentscope-stock")
        print("   kubectl get svc -n agentscope-stock")
        print("   kubectl logs -n agentscope-stock -l app=stock-agent")
        print("   kubectl scale deployment stock-agent --replicas=5 -n agentscope-stock")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        print("\n🔍 Troubleshooting:")
        print("   1. Check Docker is running: docker --version")
        print("   2. Verify K8s access: kubectl cluster-info")
        print("   3. Check registry access: docker login <registry>")
        print("   4. Verify API key: echo $DASHSCOPE_API_KEY")
        raise


async def cleanup_deployment():
    """Clean up K8s deployment"""
    print("🧹 Cleaning up deployment...")
    # Add cleanup logic if needed
    os.system("kubectl delete namespace agentscope-stock")


if __name__ == "__main__":
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("⚠️  Warning: DASHSCOPE_API_KEY not set")
        print("   Export it: export DASHSCOPE_API_KEY='your_api_key'")
    
    # Run deployment
    asyncio.run(deploy_stock_agent_to_k8s())
    
    # Keep script running or wait for user input
    print("\n⏸️  Press Ctrl+C to exit (deployment will continue running)")
    try:
        input()
    except KeyboardInterrupt:
        print("\n👋 Exiting (deployment still active)")
