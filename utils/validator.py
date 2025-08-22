#!/usr/bin/env python3
"""
Sistema de Validação de Dados para Cloud Data Orchestrator
Valida dados coletados antes de salvar no banco
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ValidationRule:
    """Regra de validação"""
    field: str
    rule_type: str
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None
    error_message: Optional[str] = None

@dataclass
class ValidationResult:
    """Resultado da validação"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_data: Dict[str, Any]

class DataValidator:
    """Validador de dados"""
    
    def __init__(self):
        self.rules = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Configura regras padrão de validação"""
        # Regras para dados de clima
        self.rules["weather"] = [
            ValidationRule("city", "string", required=True, error_message="Cidade é obrigatória"),
            ValidationRule("temperature", "number", required=True, min_value=-50, max_value=60, 
                         error_message="Temperatura deve estar entre -50°C e 60°C"),
            ValidationRule("humidity", "number", required=True, min_value=0, max_value=100,
                         error_message="Umidade deve estar entre 0% e 100%"),
            ValidationRule("description", "string", required=True, error_message="Descrição é obrigatória"),
            ValidationRule("timestamp", "datetime", required=True, error_message="Timestamp é obrigatório"),
            ValidationRule("source", "string", required=True, error_message="Fonte é obrigatória")
        ]
        
        # Regras para dados de câmbio
        self.rules["currency"] = [
            ValidationRule("base_currency", "string", required=True, error_message="Moeda base é obrigatória"),
            ValidationRule("target_currency", "string", required=True, error_message="Moeda alvo é obrigatória"),
            ValidationRule("rate", "number", required=True, min_value=0.0001, max_value=10000,
                         error_message="Taxa deve ser positiva e menor que 10000"),
            ValidationRule("timestamp", "datetime", required=True, error_message="Timestamp é obrigatório"),
            ValidationRule("source", "string", required=True, error_message="Fonte é obrigatória")
        ]
        
        # Regras para dados do GitHub
        self.rules["github"] = [
            ValidationRule("name", "string", required=True, error_message="Nome é obrigatório"),
            ValidationRule("full_name", "string", required=True, error_message="Nome completo é obrigatório"),
            ValidationRule("stars", "number", required=True, min_value=0, error_message="Stars deve ser >= 0"),
            ValidationRule("language", "string", required=False, error_message="Linguagem é opcional"),
            ValidationRule("description", "string", required=False, error_message="Descrição é opcional"),
            ValidationRule("timestamp", "datetime", required=True, error_message="Timestamp é obrigatório"),
            ValidationRule("source", "string", required=True, error_message="Fonte é obrigatória")
        ]
    
    def add_rule(self, data_type: str, rule: ValidationRule) -> None:
        """Adiciona uma regra de validação"""
        if data_type not in self.rules:
            self.rules[data_type] = []
        self.rules[data_type].append(rule)
    
    def validate_data(self, data: Dict[str, Any], data_type: str) -> ValidationResult:
        """Valida dados de acordo com as regras"""
        if data_type not in self.rules:
            return ValidationResult(
                is_valid=False,
                errors=[f"Tipo de dados '{data_type}' não suportado"],
                warnings=[],
                validated_data={}
            )
        
        errors = []
        warnings = []
        validated_data = {}
        
        for rule in self.rules[data_type]:
            field_value = data.get(rule.field)
            
            # Verificar se campo é obrigatório
            if rule.required and field_value is None:
                errors.append(rule.error_message or f"Campo '{rule.field}' é obrigatório")
                continue
            
            # Se campo não é obrigatório e está vazio, pular
            if not rule.required and field_value is None:
                continue
            
            # Aplicar validações específicas
            field_errors, field_warnings = self._validate_field(field_value, rule)
            errors.extend(field_errors)
            warnings.extend(field_warnings)
            
            # Adicionar ao dados validados
            validated_data[rule.field] = field_value
        
        # Adicionar campos extras que não estão nas regras
        for key, value in data.items():
            if key not in validated_data:
                validated_data[key] = value
                warnings.append(f"Campo '{key}' não está nas regras de validação")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_data=validated_data
        )
    
    def _validate_field(self, value: Any, rule: ValidationRule) -> Tuple[List[str], List[str]]:
        """Valida um campo específico"""
        errors = []
        warnings = []
        
        # Validação de tipo
        if rule.rule_type == "string":
            if not isinstance(value, str):
                errors.append(f"Campo '{rule.field}' deve ser uma string")
                return errors, warnings
            
            if rule.pattern and not re.match(rule.pattern, value):
                errors.append(f"Campo '{rule.field}' não corresponde ao padrão esperado")
        
        elif rule.rule_type == "number":
            try:
                num_value = float(value)
                if rule.min_value is not None and num_value < rule.min_value:
                    errors.append(f"Campo '{rule.field}' deve ser >= {rule.min_value}")
                if rule.max_value is not None and num_value > rule.max_value:
                    errors.append(f"Campo '{rule.field}' deve ser <= {rule.max_value}")
            except (ValueError, TypeError):
                errors.append(f"Campo '{rule.field}' deve ser um número")
        
        elif rule.rule_type == "datetime":
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f"Campo '{rule.field}' deve ser um timestamp ISO válido")
            elif not isinstance(value, datetime):
                errors.append(f"Campo '{rule.field}' deve ser um datetime válido")
        
        # Validação customizada
        if rule.custom_validator and callable(rule.custom_validator):
            try:
                if not rule.custom_validator(value):
                    errors.append(f"Campo '{rule.field}' falhou na validação customizada")
            except Exception as e:
                errors.append(f"Erro na validação customizada do campo '{rule.field}': {str(e)}")
        
        return errors, warnings
    
    def validate_batch(self, data_list: List[Dict[str, Any]], data_type: str) -> List[ValidationResult]:
        """Valida uma lista de dados"""
        results = []
        for data in data_list:
            result = self.validate_data(data, data_type)
            results.append(result)
        return results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Retorna resumo da validação em lote"""
        total_items = len(results)
        valid_items = sum(1 for r in results if r.is_valid)
        invalid_items = total_items - valid_items
        
        all_errors = []
        all_warnings = []
        
        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return {
            "total_items": total_items,
            "valid_items": valid_items,
            "invalid_items": invalid_items,
            "success_rate": (valid_items / total_items * 100) if total_items > 0 else 0,
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "error_types": self._count_error_types(all_errors),
            "warning_types": self._count_error_types(all_warnings)
        }
    
    def _count_error_types(self, messages: List[str]) -> Dict[str, int]:
        """Conta tipos de erros/avisos"""
        error_counts = {}
        for message in messages:
            # Extrair tipo de erro da mensagem
            if "é obrigatório" in message:
                error_type = "missing_required_field"
            elif "deve ser" in message:
                error_type = "invalid_format"
            elif "não corresponde" in message:
                error_type = "pattern_mismatch"
            elif "falhou na validação" in message:
                error_type = "custom_validation_failed"
            else:
                error_type = "other"
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return error_counts

class DataQualityChecker:
    """Verificador de qualidade dos dados"""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def check_data_quality(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Verifica qualidade dos dados"""
        validation_result = self.validator.validate_data(data, data_type)
        
        quality_score = self._calculate_quality_score(validation_result)
        
        return {
            "quality_score": quality_score,
            "validation_result": validation_result,
            "recommendations": self._generate_recommendations(validation_result),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_quality_score(self, result: ValidationResult) -> float:
        """Calcula score de qualidade (0-100)"""
        if not result.errors and not result.warnings:
            return 100.0
        
        # Penalizar erros mais que avisos
        error_penalty = len(result.errors) * 20
        warning_penalty = len(result.warnings) * 5
        
        score = max(0, 100 - error_penalty - warning_penalty)
        return round(score, 1)
    
    def _generate_recommendations(self, result: ValidationResult) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        if result.errors:
            recommendations.append("Corrigir erros de validação antes de processar os dados")
        
        if result.warnings:
            recommendations.append("Revisar avisos para melhorar qualidade dos dados")
        
        if len(result.errors) > 5:
            recommendations.append("Considerar revisar o processo de coleta de dados")
        
        if len(result.warnings) > 10:
            recommendations.append("Implementar validações mais rigorosas na fonte")
        
        return recommendations

def main():
    """Função principal para teste"""
    print("🧪 Testando sistema de validação...")
    
    # Criar validador
    validator = DataValidator()
    quality_checker = DataQualityChecker()
    
    # Dados de teste para clima
    weather_data = {
        "city": "São Paulo",
        "temperature": 25.5,
        "humidity": 75,
        "description": "céu limpo",
        "timestamp": datetime.now().isoformat(),
        "source": "openweather_api"
    }
    
    # Validar dados de clima
    print("\n🌤️  Validando dados de clima:")
    validation_result = validator.validate_data(weather_data, "weather")
    
    print(f"Válido: {validation_result.is_valid}")
    if validation_result.errors:
        print(f"❌ Erros: {validation_result.errors}")
    if validation_result.warnings:
        print(f"⚠️  Avisos: {validation_result.warnings}")
    
    # Verificar qualidade
    quality_result = quality_checker.check_data_quality(weather_data, "weather")
    print(f"📊 Score de qualidade: {quality_result['quality_score']}/100")
    
    # Dados inválidos para teste
    invalid_weather = {
        "city": "",  # Cidade vazia
        "temperature": 150,  # Temperatura impossível
        "humidity": -5,  # Umidade negativa
        "timestamp": "invalid_timestamp"
    }
    
    print("\n❌ Testando dados inválidos:")
    invalid_result = validator.validate_data(invalid_weather, "weather")
    
    print(f"Válido: {invalid_result.is_valid}")
    if invalid_result.errors:
        print(f"❌ Erros: {invalid_result.errors}")
    
    # Validação em lote
    print("\n📦 Testando validação em lote:")
    batch_data = [weather_data, invalid_weather]
    batch_results = validator.validate_batch(batch_data, "weather")
    
    summary = validator.get_validation_summary(batch_results)
    print(f"Resumo: {summary['valid_items']}/{summary['total_items']} válidos")
    print(f"Taxa de sucesso: {summary['success_rate']:.1f}%")
    
    print("\n✅ Testes de validação concluídos!")

if __name__ == "__main__":
    main()
