#!/bin/bash
# Quick Start Script for Stock Search Agent Deployment

set -e

echo "🚀 Stock Search Agent - Quick Start"
echo "===================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✅ Docker: $(docker --version)"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi
echo "✅ kubectl: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"

# Check environment variables
echo ""
echo "🔑 Checking environment variables..."

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "⚠️  DASHSCOPE_API_KEY is not set"
    read -p "Enter your DashScope API key: " api_key
    export DASHSCOPE_API_KEY="$api_key"
else
    echo "✅ DASHSCOPE_API_KEY is set"
fi

if [ -z "$DOCKER_REGISTRY" ]; then
    echo "⚠️  DOCKER_REGISTRY is not set (using default)"
    export DOCKER_REGISTRY="your-registry-url"
else
    echo "✅ DOCKER_REGISTRY: $DOCKER_REGISTRY"
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Verify Kubernetes connection
echo ""
echo "🔌 Verifying Kubernetes connection..."
if kubectl cluster-info &> /dev/null; then
    echo "✅ Connected to Kubernetes cluster"
    kubectl get nodes
else
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "   Please check your kubeconfig: $KUBECONFIG"
    exit 1
fi

# Create namespace if it doesn't exist
echo ""
echo "📁 Creating namespace..."
kubectl create namespace agentscope-stock --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespace ready"

# Run deployment
echo ""
echo "🚀 Starting deployment..."
python3 k8s_deploy_stock.py

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📊 Monitor deployment:"
echo "   kubectl get pods -n agentscope-stock -w"
echo ""
echo "🧪 Test when ready:"
echo "   python3 test_deployment.py http://YOUR-SERVICE-URL:8080"
echo ""
echo "🔍 Get service URL:"
echo "   kubectl get svc -n agentscope-stock"
