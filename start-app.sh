#!/bin/bash

# Lost and Found Application Startup Script
# This script ensures backend runs on port 8080 and frontend on port 8081

echo "=== Starting Lost and Found Application ==="

# Kill any existing processes
echo "Stopping existing processes..."
pkill -f "python manage.py runserver" 2>/dev/null
pkill -f "npm run serve" 2>/dev/null
pkill -f "vue-cli-service serve" 2>/dev/null
sleep 2

# Start backend on port 8080
echo "Starting backend on port 8080..."
cd /home/ubuntu/lost-and-found/backend
python manage.py runserver 0.0.0.0:8080 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 5

# Test backend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/notices/ | grep -q "200"; then
    echo "✅ Backend started successfully on port 8080"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend on port 8081
echo "Starting frontend on port 8081..."
cd /home/ubuntu/lost-and-found/frontend
rm -rf node_modules/.cache 2>/dev/null
npm run serve &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 10

# Test frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8081 | grep -q "200"; then
    echo "✅ Frontend started successfully on port 8081"
else
    echo "❌ Frontend failed to start"
    exit 1
fi

# Test proxy communication
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/notices/ | grep -q "200"; then
    echo "✅ Frontend-backend communication working"
else
    echo "❌ Frontend-backend communication failed"
    exit 1
fi

echo
echo "=== Application Started Successfully ==="
echo "Backend URL: http://localhost:8080"
echo "Frontend URL: http://localhost:8081"
echo "Browser Preview: Available through your IDE"
echo
echo "To stop the application:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or run: pkill -f 'python manage.py runserver' && pkill -f 'npm run serve'"
