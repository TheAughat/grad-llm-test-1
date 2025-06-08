// Option 1: Spring Boot with Socket.IO support
// Add to pom.xml:
// <dependency>
//     <groupId>com.corundumstudio.socketio</groupId>
//     <artifactId>netty-socketio</artifactId>
//     <version>1.7.19</version>
// </dependency>

package com.yourcompany.websocket.config;

import com.corundumstudio.socketio.Configuration;
import com.corundumstudio.socketio.SocketIOServer;
import com.corundumstudio.socketio.AuthorizationListener;
import com.corundumstudio.socketio.HandshakeData;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class SocketIOConfig {

    private static final Logger logger = LoggerFactory.getLogger(SocketIOConfig.class);

    @Value("${socket.io.host:localhost}")
    private String host;

    @Value("${socket.io.port:8080}")
    private Integer port;

    @Bean
    public SocketIOServer socketIOServer() {
        Configuration config = new Configuration();
        config.setHostname(host);
        config.setPort(port);
        
        // CORS configuration
        config.setOrigin("*");
        
        // Authentication handler
        config.setAuthorizationListener(new AuthorizationListener() {
            @Override
            public boolean isAuthorized(HandshakeData data) {
                logger.info("🔍 Socket.IO authorization attempt from: {}", data.getAddress());
                
                try {
                    // Extract JWT from headers
                    String authHeader = data.getSingleHeader("Authorization");
                    String jwtToken = null;
                    
                    if (authHeader != null && authHeader.startsWith("Bearer ")) {
                        jwtToken = authHeader.substring(7);
                    } else {
                        // Check auth parameter
                        String authToken = data.getSingleUrlParam("token");
                        if (authToken != null) {
                            jwtToken = authToken;
                        }
                    }
                    
                    if (jwtToken == null || jwtToken.isEmpty()) {
                        logger.warn("❌ No JWT token found in request headers or params");
                        return false;
                    }
                    
                    // Validate JWT token
                    if (!validateJwtToken(jwtToken)) {
                        logger.warn("❌ Invalid JWT token provided");
                        return false;
                    }
                    
                    // Store user information for later use
                    String userId = extractUserIdFromJwt(jwtToken);
                    String userRole = extractUserRoleFromJwt(jwtToken);
                    
                    // Store in handshake data for access in event handlers
                    data.getStore().set("userId", userId);
                    data.getStore().set("userRole", userRole);
                    data.getStore().set("jwtToken", jwtToken);
                    
                    logger.info("✅ Socket.IO authorization successful for user: {} with role: {}", userId, userRole);
                    return true;
                    
                } catch (Exception e) {
                    logger.error("❌ Error during Socket.IO authorization: {}", e.getMessage(), e);
                    return false;
                }
            }
        });
        
        return new SocketIOServer(config);
    }

    private boolean validateJwtToken(String jwtToken) {
        // TODO: Implement your JWT validation logic here
        try {
            // Example using Spring Security JWT or your JWT library
            // JwtDecoder decoder = ...;
            // Jwt jwt = decoder.decode(jwtToken);
            // return jwt.getExpiresAt().isAfter(Instant.now());
            
            // Placeholder validation
            return jwtToken.length() > 20;
            
        } catch (Exception e) {
            logger.error("JWT validation failed: {}", e.getMessage());
            return false;
        }
    }

    private String extractUserIdFromJwt(String jwtToken) {
        // TODO: Implement JWT parsing to extract user ID
        return "user123"; // Placeholder
    }

    private String extractUserRoleFromJwt(String jwtToken) {
        // TODO: Implement JWT parsing to extract user role
        return "USER"; // Placeholder
    }
}

// Socket.IO Event Handlers
@Component
public class SocketIOEventHandler {

    private static final Logger logger = LoggerFactory.getLogger(SocketIOEventHandler.class);

    @Autowired
    private SocketIOServer server;

    @EventListener
    public void onApplicationReady(ApplicationReadyEvent event) {
        server.start();
        logger.info("✅ Socket.IO server started on port: {}", server.getConfiguration().getPort());
        
        // Connection event
        server.addConnectListener(client -> {
            String userId = client.getHandshakeData().getStore().get("userId");
            logger.info("✅ Client connected: {} (User: {})", client.getSessionId(), userId);
            
            // Send welcome message
            client.sendEvent("welcome", "Connected successfully!");
        });

        // Disconnection event
        server.addDisconnectListener(client -> {
            String userId = client.getHandshakeData().getStore().get("userId");
            logger.info("🔌 Client disconnected: {} (User: {})", client.getSessionId(), userId);
        });

        // Custom message handlers
        server.addEventListener("message", String.class, (client, data, ackSender) -> {
            String userId = client.getHandshakeData().getStore().get("userId");
            logger.info("📨 Received message from {}: {}", userId, data);
            
            // Echo back or broadcast to other clients
            client.sendEvent("message_received", "Server received: " + data);
        });

        // Broadcast to all connected clients
        server.addEventListener("broadcast", String.class, (client, data, ackSender) -> {
            String userId = client.getHandshakeData().getStore().get("userId");
            logger.info("📢 Broadcasting message from {}: {}", userId, data);
            
            server.getBroadcastOperations().sendEvent("broadcast", data);
        });
    }

    @PreDestroy
    public void onDestroy() {
        if (server != null) {
            server.stop();
            logger.info("🔌 Socket.IO server stopped");
        }
    }
}

// Option 2: Alternative approach using SockJS with Spring WebSocket (if you prefer to stick with Spring WebSocket)
@Configuration
@EnableWebSocket
public class WebSocketConfigAlternative implements WebSocketConfigurer {

    private static final Logger logger = LoggerFactory.getLogger(WebSocketConfigAlternative.class);

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        // Register WebSocket handler with SockJS support
        registry.addHandler(new CustomWebSocketHandler(), "/ws")
                .addInterceptors(new JwtHandshakeInterceptor())
                .setAllowedOrigins("*")
                .withSockJS(); // This enables SockJS which supports more transport options
    }

    @Component
    public static class JwtHandshakeInterceptor implements HandshakeInterceptor {

        @Override
        public boolean beforeHandshake(
                ServerHttpRequest request,
                ServerHttpResponse response,
                WebSocketHandler wsHandler,
                Map<String, Object> attributes) throws Exception {
            
            logger.info("🔍 WebSocket handshake from: {}", request.getRemoteAddress());
            
            // For SockJS, check multiple possible locations for the JWT
            String jwtToken = extractJwtToken(request);
            
            if (jwtToken == null || jwtToken.isEmpty()) {
                logger.warn("❌ No JWT token found");
                return false;
            }
            
            if (!validateJwtToken(jwtToken)) {
                logger.warn("❌ Invalid JWT token");
                return false;
            }
            
            // Store user info in session attributes
            String userId = extractUserIdFromJwt(jwtToken);
            attributes.put("userId", userId);
            attributes.put("jwtToken", jwtToken);
            
            logger.info("✅ WebSocket handshake successful for user: {}", userId);
            return true;
        }

        @Override
        public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response,
                WebSocketHandler wsHandler, Exception exception) {
            if (exception != null) {
                logger.error("❌ WebSocket handshake failed: {}", exception.getMessage());
            }
        }

        private String extractJwtToken(ServerHttpRequest request) {
            // Try Authorization header first
            List<String> authHeaders = request.getHeaders().get("Authorization");
            if (authHeaders != null && !authHeaders.isEmpty()) {
                String authHeader = authHeaders.get(0);
                if (authHeader.startsWith("Bearer ")) {
                    return authHeader.substring(7);
                }
            }
            
            // Try query parameter as fallback (for SockJS compatibility)
            String query = request.getURI().getQuery();
            if (query != null && query.contains("token=")) {
                String[] params = query.split("&");
                for (String param : params) {
                    if (param.startsWith("token=")) {
                        return param.substring(6);
                    }
                }
            }
            
            return null;
        }

        private boolean validateJwtToken(String jwtToken) {
            // Your JWT validation logic
            return jwtToken.length() > 20;
        }

        private String extractUserIdFromJwt(String jwtToken) {
            // Your JWT parsing logic
            return "user123";
        }
    }

    @Component
    public static class CustomWebSocketHandler extends TextWebSocketHandler {

        @Override
        public void afterConnectionEstablished(WebSocketSession session) throws Exception {
            String userId = (String) session.getAttributes().get("userId");
            logger.info("✅ WebSocket connection established for user: {}", userId);
            
            // Send welcome message
            session.sendMessage(new TextMessage("Welcome! Connection established."));
        }

        @Override
        protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
            String userId = (String) session.getAttributes().get("userId");
            logger.info("📨 Received message from {}: {}", userId, message.getPayload());
            
            // Echo back the message
            session.sendMessage(new TextMessage("Server received: " + message.getPayload()));
        }

        @Override
        public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
            String userId = (String) session.getAttributes().get("userId");
            logger.info("🔌 WebSocket connection closed for user: {}", userId);
        }

        @Override
        public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
            String userId = (String) session.getAttributes().get("userId");
            logger.error("❌ WebSocket transport error for user {}: {}", userId, exception.getMessage());
        }
    }
}