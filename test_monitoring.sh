#!/bin/bash
# ScholarForge Monitoring Quick Test
# Run this to verify monitoring is working correctly

echo "=== ScholarForge Monitoring Verification ==="
echo ""

# Test Prometheus metrics endpoint
echo "[1/3] Testing Prometheus metrics endpoint..."
METRICS_RESPONSE=$(curl -s http://localhost:5000/metrics | head -5)
if [[ $METRICS_RESPONSE == *"requests_total"* ]]; then
    echo "✓ Prometheus metrics available at http://localhost:5000/metrics"
else
    echo "✗ Prometheus metrics endpoint not responding correctly"
fi

# Test health check
echo ""
echo "[2/3] Testing health check endpoint..."
HEALTH=$(curl -s http://localhost:5000/health)
if [[ $HEALTH == *"healthy"* ]] || [[ $HEALTH == *"degraded"* ]]; then
    echo "✓ Health check available at http://localhost:5000/health"
    echo "  Status: $HEALTH"
else
    echo "✗ Health check endpoint not responding correctly"
fi

# Test Flower availability (if running)
echo ""
echo "[3/3] Testing Flower Celery monitoring..."
FLOWER_CHECK=$(curl -s http://localhost:5555/api/tasks 2>/dev/null)
if [[ ! -z "$FLOWER_CHECK" ]]; then
    echo "✓ Flower dashboard available at http://localhost:5555"
else
    echo "⚠ Flower dashboard not running (it's optional for development)"
    echo "  Run with: docker-compose up flower"
fi

echo ""
echo "=== Monitoring URLs ==="
echo "Prometheus Metrics:  http://localhost:5000/metrics"
echo "Health Check:        http://localhost:5000/health"
echo "Flower Dashboard:    http://localhost:5555 (optional)"
echo ""
