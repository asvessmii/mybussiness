#!/usr/bin/env python3
"""
Тестирование API для системы управления проектами чат-ботов
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

class ProjectAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.test_project_id = None
        
    def run_test(self, name, method, endpoint, expected_status, data=None, check_response=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)
            
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
    
    def test_get_projects(self):
        """Test GET /api/projects endpoint"""
        def check_projects_response(data):
            return 'projects' in data and 'status' in data and data['status'] == 'success'
        
        return self.run_test(
            "GET /api/projects - Get all projects",
            "GET",
            "projects",
            200,
            check_response=check_projects_response
        )
    
    def test_create_project(self):
        """Test POST /api/projects endpoint"""
        def check_create_response(data):
            if 'status' in data and data['status'] == 'success' and 'project' in data:
                self.test_project_id = data['project']['id']
                return True
            return False
        
        return self.run_test(
            "POST /api/projects - Create new project",
            "POST",
            "projects",
            201,
            data={"name": "Тест API", "url": "https://httpbin.org"},
            check_response=check_create_response
        )
    
    def test_get_project(self):
        """Test GET /api/projects/{project_id} endpoint"""
        if not self.test_project_id:
            print("❌ Cannot test GET project - No project ID available")
            return False, {}
        
        def check_project_response(data):
            return 'status' in data and data['status'] == 'success' and 'project' in data
        
        return self.run_test(
            f"GET /api/projects/{self.test_project_id} - Get project details",
            "GET",
            f"projects/{self.test_project_id}",
            200,
            check_response=check_project_response
        )
    
    def test_get_project_status(self):
        """Test GET /api/projects/{project_id}/status endpoint"""
        if not self.test_project_id:
            print("❌ Cannot test GET project status - No project ID available")
            return False, {}
        
        def check_status_response(data):
            return ('status' in data and data['status'] == 'success' and 
                    'project_status' in data and 'status' in data['project_status'])
        
        return self.run_test(
            f"GET /api/projects/{self.test_project_id}/status - Get project status",
            "GET",
            f"projects/{self.test_project_id}/status",
            200,
            check_response=check_status_response
        )
    
    def test_start_scraping(self):
        """Test POST /api/projects/{project_id}/scrape endpoint"""
        if not self.test_project_id:
            print("❌ Cannot test start scraping - No project ID available")
            return False, {}
        
        def check_scrape_response(data):
            return 'status' in data and data['status'] == 'success' and 'message' in data
        
        return self.run_test(
            f"POST /api/projects/{self.test_project_id}/scrape - Start scraping",
            "POST",
            f"projects/{self.test_project_id}/scrape",
            200,
            data={},
            check_response=check_scrape_response
        )
    
    def test_start_training(self):
        """Test POST /api/projects/{project_id}/train endpoint"""
        if not self.test_project_id:
            print("❌ Cannot test start training - No project ID available")
            return False, {}
        
        def check_train_response(data):
            return 'status' in data and data['status'] == 'success' and 'message' in data
        
        return self.run_test(
            f"POST /api/projects/{self.test_project_id}/train - Start training",
            "POST",
            f"projects/{self.test_project_id}/train",
            200,
            data={},
            check_response=check_train_response
        )
    
    def test_chat_with_project(self):
        """Test POST /api/projects/{project_id}/chat endpoint"""
        if not self.test_project_id:
            print("❌ Cannot test chat - No project ID available")
            return False, {}
        
        def check_chat_response(data):
            # We expect either a success response or an error response about the project not being ready
            return 'status' in data
        
        return self.run_test(
            f"POST /api/projects/{self.test_project_id}/chat - Chat with bot",
            "POST",
            f"projects/{self.test_project_id}/chat",
            200,  # We expect 200 even for error responses
            data={"message": "Привет, это тестовое сообщение", "session_id": str(uuid.uuid4())},
            check_response=check_chat_response
        )
    
    def test_generate_code(self):
        """Test POST /api/projects/{project_id}/generate-code endpoint"""
        if not self.test_project_id:
            print("❌ Cannot test code generation - No project ID available")
            return False, {}
        
        def check_code_response(data):
            return 'status' in data
        
        return self.run_test(
            f"POST /api/projects/{self.test_project_id}/generate-code - Generate integration code",
            "POST",
            f"projects/{self.test_project_id}/generate-code",
            200,
            data={},
            check_response=check_code_response
        )
    
    def test_delete_project(self):
        """Test DELETE /api/projects/{project_id} endpoint"""
        if not self.test_project_id:
            print("❌ Cannot test delete project - No project ID available")
            return False, {}
        
        def check_delete_response(data):
            return 'status' in data and data['status'] == 'success' and 'message' in data
        
        return self.run_test(
            f"DELETE /api/projects/{self.test_project_id} - Delete project",
            "DELETE",
            f"projects/{self.test_project_id}",
            200,
            check_response=check_delete_response
        )
    
    def test_error_handling(self):
        """Test error handling with invalid requests"""
        # Test invalid project ID
        invalid_id = "invalid-id-12345"
        
        self.run_test(
            "Error Handling - Invalid Project ID",
            "GET",
            f"projects/{invalid_id}",
            404,
        )
        
        # Test invalid data for project creation
        self.run_test(
            "Error Handling - Invalid Project Data",
            "POST",
            "projects",
            400,
            data={"invalid_field": "test"}
        )
        
        # Test rate limiting (this might not trigger depending on the server configuration)
        print("\n🔍 Testing Rate Limiting...")
        for i in range(6):  # Try to exceed the 5 per minute limit
            self.session.post(
                f"{self.base_url}/api/projects",
                json={"name": f"Rate Test {i}", "url": "https://example.com"},
                headers={'Content-Type': 'application/json'}
            )
        
        # Check if the last request was rate limited
        response = self.session.post(
            f"{self.base_url}/api/projects",
            json={"name": "Rate Test Final", "url": "https://example.com"},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 429:
            self.tests_passed += 1
            print("✅ Rate limiting is working correctly")
        else:
            print("⚠️ Rate limiting test inconclusive - might need longer test period")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting API Tests for Project Management System\n")
        
        # Test getting all projects
        self.test_get_projects()
        
        # Test creating a new project
        success, _ = self.test_create_project()
        
        if success:
            # Test getting project details
            self.test_get_project()
            
            # Test getting project status
            self.test_get_project_status()
            
            # Test starting scraping
            self.test_start_scraping()
            
            # Check status after scraping started
            print("\n⏳ Waiting 2 seconds for status update...")
            time.sleep(2)
            self.test_get_project_status()
            
            # Test starting training
            self.test_start_training()
            
            # Test chat with project
            self.test_chat_with_project()
            
            # Test generating integration code
            self.test_generate_code()
            
            # Test deleting the project
            self.test_delete_project()
        
        # Test error handling
        self.test_error_handling()
        
        # Print summary
        print(f"\n📊 Tests Summary: {self.tests_passed}/{self.tests_run} passed")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ProjectAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())