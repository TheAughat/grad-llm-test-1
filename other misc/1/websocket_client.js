import { useState, useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';

// Custom hook for Socket.IO with JWT header support
const useSocketIOWithHeaders = (url, jwtToken, options = {}) => {
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const socket = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  const {
    shouldReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onOpen,
    onMessage,
    onClose,
    onError,
    namespace = '/'
  } = options;
  
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const connect = useCallback(() => {
    try {
      console.log('🔄 Attempting to connect to Socket.IO server:', url);
      console.log('🔑 Using JWT token length:', jwtToken?.length || 0);
      
      setConnectionStatus('Connecting');
      setError(null);
      
      // Create Socket.IO connection with custom headers
      socket.current = io(url + namespace, {
        transportOptions: {
          polling: {
            extraHeaders: {
              'Authorization': `Bearer ${jwtToken}`,
              'X-Client-Type': 'react-app'
            }
          }
        },
        // Additional auth options
        auth: {
          token: jwtToken
        },
        // Connection options
        autoConnect: true,
        reconnection: false, // We'll handle reconnection manually
        timeout: 10000,
        forceNew: true
      });

      // Connection established
      socket.current.on('connect', () => {
        console.log('✅ Socket.IO connection established');
        console.log('🆔 Socket ID:', socket.current.id);
        setConnectionStatus('Connected');
        setReconnectAttempts(0);
        setError(null);
        onOpen?.(socket.current);
      });

      // Handle any message/event (catch-all listener)
      socket.current.onAny((eventName, ...args) => {
        console.log('📨 Received event:', eventName, 'with data:', args);
        const message = {
          event: eventName,
          data: args,
          timestamp: new Date().toISOString()
        };
        setLastMessage(message);
        onMessage?.(eventName, ...args);
      });

      // Connection error
      socket.current.on('connect_error', (err) => {
        console.error('❌ Socket.IO connection error:', err.message);
        console.error('Error details:', err);
        setError(`Connection failed: ${err.message}`);
        setConnectionStatus('Error');
        
        // Attempt reconnection if enabled
        if (shouldReconnect && reconnectAttempts < maxReconnectAttempts) {
          const nextAttempt = reconnectAttempts + 1;
          setReconnectAttempts(nextAttempt);
          console.log(`🔄 Scheduling reconnection attempt ${nextAttempt}/${maxReconnectAttempts} in ${reconnectInterval}ms`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error('❌ Max reconnection attempts reached');
          setError('Max reconnection attempts reached');
        }
        
        onError?.(err);
      });

      // Disconnection
      socket.current.on('disconnect', (reason) => {
        console.log('🔌 Socket.IO disconnected:', reason);
        setConnectionStatus('Disconnected');
        
        // Only attempt reconnection for unexpected disconnects
        if (reason === 'io server disconnect' || reason === 'transport close') {
          if (shouldReconnect && reconnectAttempts < maxReconnectAttempts) {
            const nextAttempt = reconnectAttempts + 1;
            setReconnectAttempts(nextAttempt);
            console.log(`🔄 Scheduling reconnection attempt ${nextAttempt}/${maxReconnectAttempts} in ${reconnectInterval}ms`);
            
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, reconnectInterval);
          }
        }
        
        onClose?.(reason);
      });

      // Authentication error (if your server emits this)
      socket.current.on('auth_error', (error) => {
        console.error('🔐 Authentication error:', error);
        setError(`Authentication failed: ${error}`);
        setConnectionStatus('Error');
      });

      // Custom message events (add more as needed)
      socket.current.on('message', (data) => {
        console.log('💬 Received message:', data);
      });

      socket.current.on('notification', (data) => {
        console.log('🔔 Received notification:', data);
      });

      socket.current.on('broadcast', (data) => {
        console.log('📢 Received broadcast:', data);
      });

    } catch (err) {
      console.error('❌ Failed to create Socket.IO connection:', err);
      setError(err.message);
      setConnectionStatus('Error');
    }
  }, [url, jwtToken, namespace, shouldReconnect, reconnectInterval, maxReconnectAttempts, reconnectAttempts, onOpen, onMessage, onClose, onError]);

  const disconnect = useCallback(() => {
    console.log('🔌 Manually disconnecting Socket.IO');
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socket.current) {
      socket.current.disconnect();
    }
    setConnectionStatus('Disconnected');
    setReconnectAttempts(0);
  }, []);

  const sendMessage = useCallback((event, data) => {
    if (socket.current && socket.current.connected) {
      socket.current.emit(event, data);
      console.log('📤 Sent event:', event, 'with data:', data);
    } else {
      console.warn('⚠️ Cannot send message - Socket.IO not connected');
    }
  }, []);

  useEffect(() => {
    if (jwtToken) {
      connect();
    } else {
      console.warn('⚠️ No JWT token provided, skipping connection');
    }
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socket.current) {
        socket.current.disconnect();
      }
    };
  }, [connect, jwtToken]);

  return {
    connectionStatus,
    lastMessage,
    error,
    sendMessage,
    disconnect,
    reconnect: connect,
    socket: socket.current
  };
};

// Alternative: Using ws library (if you prefer pure WebSocket with header support)
const useWSWithHeaders = (url, jwtToken, options = {}) => {
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const ws = useRef(null);

  const connect = useCallback(() => {
    try {
      console.log('🔄 Attempting to connect with ws library:', url);
      
      setConnectionStatus('Connecting');
      setError(null);

      // Note: This approach requires the 'ws' library which only works in Node.js
      // For browser use, you'd need to use a WebSocket library that supports headers
      // or implement the handshake approach from the previous example
      
      console.warn('⚠️ ws library approach requires Node.js environment or browser polyfill');
      
      // This is a placeholder - you'd need to use a library like 'isomorphic-ws' 
      // or implement a custom solution for browser compatibility
      
    } catch (err) {
      console.error('❌ WS connection failed:', err);
      setError(err.message);
      setConnectionStatus('Error');
    }
  }, [url, jwtToken]);

  return {
    connectionStatus,
    lastMessage,
    error,
    connect
  };
};

// Usage example component
const SocketIOExample = () => {
  const jwtToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"; // Your actual JWT token
  
  const {
    connectionStatus,
    lastMessage,
    error,
    sendMessage,
    disconnect,
    reconnect
  } = useSocketIOWithHeaders(
    'http://localhost:8080', // Your Socket.IO server URL
    jwtToken,
    {
      shouldReconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      namespace: '/', // or '/your-namespace'
      onOpen: (socket) => {
        console.log('🎉 Custom onOpen callback - Socket ID:', socket.id);
      },
      onMessage: (event, ...data) => {
        console.log('🎉 Custom onMessage callback:', event, data);
      },
      onClose: (reason) => {
        console.log('🎉 Custom onClose callback:', reason);
      },
      onError: (error) => {
        console.log('🎉 Custom onError callback:', error);
      }
    }
  );

  const handleSendTestMessage = () => {
    sendMessage('test', { message: 'Hello from React!', timestamp: Date.now() });
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h3>Socket.IO Connection with JWT Headers</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <strong>Status:</strong> 
        <span style={{ 
          color: connectionStatus === 'Connected' ? 'green' : 
                connectionStatus === 'Error' ? 'red' : 'orange',
          marginLeft: '10px'
        }}>
          {connectionStatus}
        </span>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <button onClick={reconnect} disabled={connectionStatus === 'Connected'}>
          Reconnect
        </button>
        <button onClick={disconnect} disabled={connectionStatus === 'Disconnected'} style={{ marginLeft: '10px' }}>
          Disconnect
        </button>
        <button onClick={handleSendTestMessage} disabled={connectionStatus !== 'Connected'} style={{ marginLeft: '10px' }}>
          Send Test Message
        </button>
      </div>
      
      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          <strong>Error:</strong> {error}
        </div>
      )}
      
      {lastMessage && (
        <div style={{ marginTop: '20px' }}>
          <h4>Last Message/Event:</h4>
          <div style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
            <div><strong>Event:</strong> {lastMessage.event}</div>
            <div><strong>Data:</strong> {JSON.stringify(lastMessage.data, null, 2)}</div>
            <div><strong>Timestamp:</strong> {lastMessage.timestamp}</div>
          </div>
        </div>
      )}
      
      <div style={{ marginTop: '30px', padding: '15px', background: '#e8f4fd', borderRadius: '5px' }}>
        <h4>Installation Instructions:</h4>
        <pre style={{ background: '#fff', padding: '10px', borderRadius: '3px' }}>
          npm install socket.io-client
        </pre>
        
        <h4 style={{ marginTop: '15px' }}>Make sure your Spring Boot server supports Socket.IO or use:</h4>
        <pre style={{ background: '#fff', padding: '10px', borderRadius: '3px' }}>
          {`// For Spring Boot WebSocket compatibility
// You might need to add Socket.IO server support or
// modify the connection to work with your WebSocket endpoint`}
        </pre>
      </div>
    </div>
  );
};

export default SocketIOExample;