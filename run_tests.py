#!/usr/bin/env python3
"""
Script de Testes Automatizados para Cloud Data Orchestrator
Executa todos os testes do projeto de forma organizada
"""

import os
import sys
import subprocess
import time
from pathlib import Path

class TestRunner:
    """Executor de testes para o projeto"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        
    def run_command(self, command, cwd=None, check=False):
        """Executa um comando no terminal"""
        if cwd is None:
            cwd = self.project_root
            
        print(f"🧪 Executando: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True
            )
            
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao executar comando: {e}")
            return e
    
    def test_python_imports(self):
        """Testa se todos os módulos Python podem ser importados"""
        print("\n🔍 Testando imports Python...")
        
        modules_to_test = [
            "data_pipeline.data_collector",
            "lambda.data_handler",
            "dashboard.app",
            "dashboard.app_test"
        ]
        
        success_count = 0
        total_count = len(modules_to_test)
        
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {module}")
                success_count += 1
            except ImportError as e:
                print(f"❌ {module}: {e}")
        
        self.test_results['python_imports'] = {
            'success': success_count,
            'total': total_count,
            'passed': success_count == total_count
        }
        
        print(f"📊 Imports: {success_count}/{total_count} ✅")
        return success_count == total_count
    
    def test_unit_tests(self):
        """Executa testes unitários"""
        print("\n🧪 Executando testes unitários...")
        
        result = self.run_command("python -m pytest tests/ -v", check=False)
        
        if result.returncode == 0:
            print("✅ Todos os testes unitários passaram")
            self.test_results['unit_tests'] = {'passed': True, 'output': result.stdout}
            return True
        else:
            print("❌ Alguns testes unitários falharam")
            self.test_results['unit_tests'] = {'passed': False, 'output': result.stderr}
            return False
    
    def test_data_pipeline(self):
        """Testa o data pipeline"""
        print("\n🔬 Testando data pipeline...")
        
        result = self.run_command("python data_pipeline/data_collector_test.py", check=False)
        
        if result.returncode == 0:
            print("✅ Data pipeline funcionando corretamente")
            self.test_results['data_pipeline'] = {'passed': True, 'output': result.stdout}
            return True
        else:
            print("❌ Data pipeline com problemas")
            self.test_results['data_pipeline'] = {'passed': False, 'output': result.stderr}
            return False
    
    def test_lambda_function(self):
        """Testa a função Lambda"""
        print("\n⚡ Testando função Lambda...")
        
        result = self.run_command("python lambda/test_lambda_mock.py", check=False)
        
        if result.returncode == 0:
            print("✅ Função Lambda funcionando corretamente")
            self.test_results['lambda_function'] = {'passed': True, 'output': result.stdout}
            return True
        else:
            print("❌ Função Lambda com problemas")
            self.test_results['lambda_function'] = {'passed': False, 'output': result.stderr}
            return False
    
    def test_code_quality(self):
        """Testa qualidade do código"""
        print("\n🔍 Testando qualidade do código...")
        
        # Black
        black_result = self.run_command("black --check .", check=False)
        black_passed = black_result.returncode == 0
        
        # Flake8
        flake8_result = self.run_command("flake8 . --max-line-length=88 --ignore=E203,W503", check=False)
        flake8_passed = flake8_result.returncode == 0
        
        if black_passed and flake8_passed:
            print("✅ Qualidade do código: OK")
            self.test_results['code_quality'] = {'passed': True}
            return True
        else:
            print("❌ Problemas de qualidade do código detectados")
            self.test_results['code_quality'] = {
                'passed': False,
                'black': black_passed,
                'flake8': flake8_passed
            }
            return False
    
    def test_dependencies(self):
        """Testa se todas as dependências estão instaladas"""
        print("\n📦 Testando dependências...")
        
        required_packages = [
            'boto3', 'requests', 'streamlit', 'plotly', 
            'pandas', 'pytest', 'black', 'flake8'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package}")
                missing_packages.append(package)
        
        if not missing_packages:
            print("✅ Todas as dependências estão instaladas")
            self.test_results['dependencies'] = {'passed': True}
            return True
        else:
            print(f"❌ Dependências faltando: {', '.join(missing_packages)}")
            self.test_results['dependencies'] = {'passed': False, 'missing': missing_packages}
            return False
    
    def generate_report(self):
        """Gera relatório dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE TESTES")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('passed', False))
        
        print(f"Total de Testes: {total_tests}")
        print(f"Testes Passaram: {passed_tests}")
        print(f"Testes Falharam: {total_tests - passed_tests}")
        print(f"Taxa de Sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 Detalhes dos Testes:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        print("=" * 60)
        
        if passed_tests == total_tests:
            print("🎉 TODOS OS TESTES PASSARAM!")
            return True
        else:
            print("⚠️  ALGUNS TESTES FALHARAM!")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando execução de todos os testes...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Executar todos os testes
        tests = [
            ("Dependências", self.test_dependencies),
            ("Imports Python", self.test_python_imports),
            ("Qualidade do Código", self.test_code_quality),
            ("Testes Unitários", self.test_unit_tests),
            ("Data Pipeline", self.test_data_pipeline),
            ("Função Lambda", self.test_lambda_function)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Erro no teste {test_name}: {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = {'passed': False, 'error': str(e)}
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️  Tempo total de execução: {execution_time:.2f} segundos")
        
        # Gerar relatório
        all_passed = self.generate_report()
        
        return all_passed

def main():
    """Função principal"""
    test_runner = TestRunner()
    
    try:
        success = test_runner.run_all_tests()
        
        if success:
            print("✅ Todos os testes passaram com sucesso!")
            sys.exit(0)
        else:
            print("❌ Alguns testes falharam!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
