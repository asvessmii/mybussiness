#!/usr/bin/env python3
"""
Тестирование API для универсального ИИ чат-бота
"""

import requests
import json
import sys
from datetime import datetime

class ChatbotAPITester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
    def run_test(self, name, method, endpoint, expected_status, data=None, check_response=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            
            # Check status code
            status_ok = response.status_code == expected_status
            
            # Check response content if needed
            content_ok = True
            response_data = {}
            
            if status_ok:
                try:
                    response_data = response.json()
                    if check_response:
                        content_ok = check_response(response_data)
                except Exception as e:
                    content_ok = False
                    print(f"❌ Failed to parse response JSON: {str(e)}")
            
            # Overall test result
            success = status_ok and content_ok
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response_data:
                    print(f"📄 Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ Failed - Expected status {expected_status}, got {response.status_code}")
                if response_data:
                    print(f"📄 Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            return success, response_data
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
    
    def test_status(self):
        """Test the status endpoint"""
        def check_status_response(data):
            required_fields = ['status', 'timestamp', 'models_loaded', 'embedding_model', 'llm_model']
            return all(field in data for field in required_fields)
        
        return self.run_test(
            "API Status",
            "GET",
            "status",
            200,
            check_response=check_status_response
        )
    
    def test_chat(self, message):
        """Test the chat endpoint"""
        def check_chat_response(data):
            required_fields = ['response', 'session_id', 'timestamp']
            return all(field in data for field in required_fields)
        
        return self.run_test(
            f"Chat API with message: '{message}'",
            "POST",
            "chat",
            200,
            data={"message": message, "session_id": self.session_id},
            check_response=check_chat_response
        )
    
    def test_upload_document(self):
        """Test the document upload endpoint"""
        def check_upload_response(data):
            required_fields = ['message', 'timestamp']
            return all(field in data for field in required_fields)
        
        return self.run_test(
            "Document Upload API",
            "POST",
            "upload_document",
            200,
            data={},
            check_response=check_upload_response
        )
    
    def test_knowledge_base(self):
        """Test the knowledge base endpoint"""
        def check_kb_response(data):
            required_fields = ['vector_store_size', 'total_documents', 'embedding_model', 'timestamp']
            return all(field in data for field in required_fields)
        
        return self.run_test(
            "Knowledge Base API",
            "GET",
            "knowledge_base",
            200,
            check_response=check_kb_response
        )
    
    def test_error_handling(self):
        """Test error handling with invalid request"""
        return self.run_test(
            "Error Handling - Invalid Request",
            "POST",
            "chat",
            500,  # Expecting error
            data={"invalid_field": "test"}
        )
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting API Tests for ИИ Чат-бот\n")
        
        # Test status endpoint
        self.test_status()
        
        # Test chat with different messages
        self.test_chat("привет")
        self.test_chat("как дела")
        self.test_chat("что умеешь")
        self.test_chat("спасибо")
        self.test_chat("пока")
        
        # Test with a long message
        long_message = "Это очень длинное сообщение для тестирования обработки длинных запросов. " * 5
        self.test_chat(long_message)
        
        # Test document upload
        self.test_upload_document()
        
        # Test knowledge base
        self.test_knowledge_base()
        
        # Test error handling
        self.test_error_handling()
        
        # Print summary
        print(f"\n📊 Tests Summary: {self.tests_passed}/{self.tests_run} passed")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ChatbotAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())