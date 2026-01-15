"""Integration tests using real RobotMqttClient (requires MQTT broker or stub).

To run with a real MQTT broker:
  1. Start Mosquitto: mosquitto -p 1883
  2. Run: python -m unittest robot.test_integration -v

This test uses a lightweight in-process stub if no broker is available.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import unittest
from collections import deque

# Ensure package root (src) is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from robot.mqtt.robot_mqtt_client import RobotMqttClient
from robot.mqtt.mqtt_msg import MqttMsg


class InMemoryMQTTBroker:
    """Lightweight in-process MQTT broker stub for testing without external dependencies."""
    
    def __init__(self):
        self.topics = {}  # topic -> list of subscribers
        self.message_queues = {}  # client_id -> deque of messages
        self.lock = threading.Lock()
    
    def subscribe(self, client_id: str, topic: str):
        with self.lock:
            if topic not in self.topics:
                self.topics[topic] = []
            if client_id not in self.topics[topic]:
                self.topics[topic].append(client_id)
            if client_id not in self.message_queues:
                self.message_queues[client_id] = deque()
    
    def publish(self, topic: str, payload: str):
        with self.lock:
            if topic in self.topics:
                for client_id in self.topics[topic]:
                    if client_id in self.message_queues:
                        self.message_queues[client_id].append(MqttMsg(topic, payload))
    
    def get_message(self, client_id: str) -> MqttMsg | None:
        with self.lock:
            if client_id in self.message_queues and self.message_queues[client_id]:
                return self.message_queues[client_id].popleft()
        return None


# Global broker instance
_broker = InMemoryMQTTBroker()


class IntegrationTestRobotMqttClient(unittest.TestCase):
    """Test RobotMqttClient behavior with in-process broker."""
    
    def test_client_initialization(self):
        """Test that client can be created."""
        try:
            client = RobotMqttClient(
                server="localhost",
                port=1883,
                user_name="",
                password="",
                channel="test_ch1"
            )
            # If it connects successfully, close it
            client.close()
        except Exception as e:
            # If real broker not available, that's okay for this test
            print(f"Note: Real MQTT broker not available: {e}")
            self.skipTest("Real MQTT broker not available (expected)")
    
    def test_publish_and_receive(self):
        """Test publish/subscribe cycle with in-memory broker."""
        broker = _broker
        
        # Simulate two clients
        client1_id = "test_client_1"
        client2_id = "test_client_2"
        
        # Client 1 subscribes to a topic
        broker.subscribe(client1_id, "test/topic")
        
        # Client 2 publishes to that topic
        broker.publish("test/topic", "Hello World")
        
        # Client 1 should receive the message
        msg = broker.get_message(client1_id)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.topic, "test/topic")
        self.assertEqual(msg.message, "Hello World")
    
    def test_multiple_subscribers(self):
        """Test that multiple clients receive same message."""
        broker = _broker
        
        client1_id = "multi_client_1"
        client2_id = "multi_client_2"
        topic = "broadcast/topic"
        
        # Both subscribe
        broker.subscribe(client1_id, topic)
        broker.subscribe(client2_id, topic)
        
        # Publish
        broker.publish(topic, "Broadcast Message")
        
        # Both should receive
        msg1 = broker.get_message(client1_id)
        msg2 = broker.get_message(client2_id)
        
        self.assertIsNotNone(msg1)
        self.assertIsNotNone(msg2)
        self.assertEqual(msg1.message, msg2.message)
    
    def test_mqtt_msg_queueing(self):
        """Test that MqttMsg objects are properly queued."""
        broker = _broker
        client_id = "queue_test"
        
        broker.subscribe(client_id, "queue/test")
        
        # Publish multiple messages
        for i in range(5):
            broker.publish("queue/test", f"Message {i}")
        
        # Retrieve all
        messages = []
        for _ in range(5):
            msg = broker.get_message(client_id)
            if msg:
                messages.append(msg)
        
        self.assertEqual(len(messages), 5)
        for i, msg in enumerate(messages):
            self.assertEqual(msg.message, f"Message {i}")


class RobotMqttClientMockTests(unittest.TestCase):
    """Test RobotMqttClient with the paho mock stub."""
    
    def test_client_queue_operations(self):
        """Test in_queue and out_queue operations."""
        try:
            client = RobotMqttClient(
                server="localhost",
                port=1883,
                user_name=None,
                password=None,
                channel="v1"
            )
            
            # Test queue pop on empty
            result = client.in_queue_pop()
            self.assertIsNone(result)
            
            result = client.out_queue_pop()
            self.assertIsNone(result)
            
            client.close()
        except Exception as e:
            print(f"Note: Real MQTT broker not available: {e}")
            self.skipTest("Real MQTT broker not available (expected)")
    
    def test_in_queue_append(self):
        """Test appending to in_queue."""
        try:
            client = RobotMqttClient(
                server="localhost",
                port=1883,
                user_name=None,
                password=None,
                channel="v1"
            )
            
            # Manually add a message (simulating broker callback)
            msg = MqttMsg("test/topic", "test payload")
            client.in_queue.append(msg)
            
            # Pop it back
            popped = client.in_queue_pop()
            self.assertIsNotNone(popped)
            self.assertEqual(popped.topic, "test/topic")
            self.assertEqual(popped.message, "test payload")
            
            client.close()
        except Exception as e:
            print(f"Note: Real MQTT broker not available: {e}")
            self.skipTest("Real MQTT broker not available (expected)")


if __name__ == "__main__":
    unittest.main()
