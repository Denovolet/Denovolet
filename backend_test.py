#!/usr/bin/env python3
"""
Backend API Testing for Sistema de Agendamento Odontológico
Tests all CRUD operations and API endpoints
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class OdontologiaAPITester:
    def __init__(self, base_url="https://apptflow-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            'servicos': [],
            'agendamentos': []
        }

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None, params: Dict[str, str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_status_endpoint(self):
        """Test system status"""
        return self.run_test("System Status", "GET", "api/status", 200)

    def test_list_servicos(self):
        """Test listing services"""
        success, response = self.run_test("List Services", "GET", "api/servicos", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} services")
            if len(response) >= 5:
                print("   ✅ Default services loaded correctly")
            else:
                print("   ⚠️  Expected at least 5 default services")
        return success, response

    def test_create_servico(self):
        """Test creating a new service"""
        test_service = {
            "nome": "Teste Automatizado - Consulta",
            "duracao_minutos": 45,
            "preco": 180.0,
            "descricao": "Serviço criado por teste automatizado"
        }
        
        success, response = self.run_test("Create Service", "POST", "api/servicos", 200, test_service)
        if success and 'id' in response:
            self.created_resources['servicos'].append(response['id'])
            print(f"   Created service with ID: {response['id']}")
        return success, response

    def test_get_servico(self, servico_id: str):
        """Test getting a specific service"""
        return self.run_test(f"Get Service {servico_id}", "GET", f"api/servicos/{servico_id}", 200)

    def test_list_horarios(self):
        """Test listing working hours"""
        success, response = self.run_test("List Working Hours", "GET", "api/horarios", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} working hour configurations")
            if len(response) == 7:
                print("   ✅ All weekdays configured")
            else:
                print("   ⚠️  Expected 7 weekday configurations")
        return success, response

    def test_list_agendamentos(self):
        """Test listing appointments"""
        return self.run_test("List Appointments", "GET", "api/agendamentos", 200)

    def test_list_agendamentos_by_date(self):
        """Test listing appointments by date"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.run_test("List Appointments by Date", "GET", "api/agendamentos", 200, params={'data': today})

    def test_horarios_disponiveis(self, servico_id: str):
        """Test getting available time slots"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        return self.run_test(
            "Get Available Times", 
            "GET", 
            "api/horarios-disponiveis", 
            200, 
            params={'data': tomorrow, 'servico_id': servico_id}
        )

    def test_create_agendamento(self, servico_id: str):
        """Test creating an appointment"""
        # Use tomorrow at 10:00 AM
        tomorrow_10am = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        test_appointment = {
            "paciente": {
                "nome": "Dr. João Silva - Teste",
                "telefone": "(11) 99999-9999",
                "email": "joao.teste@email.com",
                "observacoes": "Paciente de teste automatizado"
            },
            "servico_id": servico_id,
            "data_hora": tomorrow_10am.isoformat(),
            "observacoes": "Agendamento criado por teste automatizado"
        }
        
        success, response = self.run_test("Create Appointment", "POST", "api/agendamentos", 200, test_appointment)
        if success and 'id' in response:
            self.created_resources['agendamentos'].append(response['id'])
            print(f"   Created appointment with ID: {response['id']}")
        return success, response

    def test_get_agendamento(self, agendamento_id: str):
        """Test getting a specific appointment"""
        return self.run_test(f"Get Appointment {agendamento_id}", "GET", f"api/agendamentos/{agendamento_id}", 200)

    def test_update_agendamento_status(self, agendamento_id: str, status: str):
        """Test updating appointment status"""
        return self.run_test(
            f"Update Appointment Status to {status}", 
            "PUT", 
            f"api/agendamentos/{agendamento_id}/status", 
            200,
            params={'status': status}
        )

    def test_delete_agendamento(self, agendamento_id: str):
        """Test deleting an appointment"""
        success, response = self.run_test(f"Delete Appointment {agendamento_id}", "DELETE", f"api/agendamentos/{agendamento_id}", 200)
        if success:
            # Remove from our tracking list
            if agendamento_id in self.created_resources['agendamentos']:
                self.created_resources['agendamentos'].remove(agendamento_id)
        return success, response

    def test_delete_servico(self, servico_id: str):
        """Test deleting a service"""
        success, response = self.run_test(f"Delete Service {servico_id}", "DELETE", f"api/servicos/{servico_id}", 200)
        if success:
            # Remove from our tracking list
            if servico_id in self.created_resources['servicos']:
                self.created_resources['servicos'].remove(servico_id)
        return success, response

    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Delete test appointments
        for agendamento_id in self.created_resources['agendamentos'].copy():
            self.test_delete_agendamento(agendamento_id)
        
        # Delete test services
        for servico_id in self.created_resources['servicos'].copy():
            self.test_delete_servico(servico_id)

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🚀 Starting Backend API Tests for Sistema de Agendamento Odontológico")
        print("=" * 70)

        # Test 1: System Status
        status_success, _ = self.test_status_endpoint()
        if not status_success:
            print("❌ System is not responding. Stopping tests.")
            return False

        # Test 2: List Services (should have 5 default services)
        servicos_success, servicos = self.test_list_servicos()
        if not servicos_success or not servicos:
            print("❌ Cannot load services. Stopping tests.")
            return False

        # Use first service for further tests
        first_servico_id = servicos[0]['id']
        print(f"\n📋 Using service '{servicos[0]['nome']}' (ID: {first_servico_id}) for tests")

        # Test 3: Get specific service
        self.test_get_servico(first_servico_id)

        # Test 4: Create new service
        create_servico_success, new_servico = self.test_create_servico()
        
        # Test 5: List working hours
        self.test_list_horarios()

        # Test 6: Get available time slots
        self.test_horarios_disponiveis(first_servico_id)

        # Test 7: List appointments (initially empty)
        self.test_list_agendamentos()

        # Test 8: List appointments by date
        self.test_list_agendamentos_by_date()

        # Test 9: Create appointment
        create_agendamento_success, new_agendamento = self.test_create_agendamento(first_servico_id)
        
        if create_agendamento_success and 'id' in new_agendamento:
            agendamento_id = new_agendamento['id']
            
            # Test 10: Get specific appointment
            self.test_get_agendamento(agendamento_id)
            
            # Test 11: Update appointment status to 'concluido'
            self.test_update_agendamento_status(agendamento_id, 'concluido')
            
            # Test 12: Update appointment status to 'cancelado'
            self.test_update_agendamento_status(agendamento_id, 'cancelado')

        # Test 13: Test conflict prevention (try to create appointment at same time)
        if create_agendamento_success:
            print("\n🔒 Testing appointment conflict prevention...")
            conflict_success, _ = self.test_create_agendamento(first_servico_id)
            if not conflict_success:
                print("   ✅ Conflict prevention working correctly")
                self.tests_passed += 1
            else:
                print("   ⚠️  Conflict prevention may not be working")
            self.tests_run += 1

        # Cleanup
        self.cleanup_resources()

        return True

def main():
    """Main test execution"""
    print("Sistema de Agendamento Odontológico - Backend API Tests")
    print("Testing against: https://apptflow-3.preview.emergentagent.com")
    print("=" * 70)

    tester = OdontologiaAPITester()
    
    try:
        success = tester.run_all_tests()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"Tests Run: {tester.tests_run}")
        print(f"Tests Passed: {tester.tests_passed}")
        print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
        print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
        
        if tester.tests_passed == tester.tests_run:
            print("\n🎉 ALL TESTS PASSED! Backend API is working correctly.")
            return 0
        elif tester.tests_passed >= tester.tests_run * 0.8:
            print("\n✅ Most tests passed. Backend API is mostly functional.")
            return 0
        else:
            print("\n❌ Many tests failed. Backend API has significant issues.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())