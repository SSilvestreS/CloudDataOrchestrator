# ☁️ Deploy Automatizado na Nuvem - CloudDataOrchestrator v2.0

Guia completo para deploy automatizado na AWS usando CI/CD, Terraform e Docker.

## 🚀 **Visão Geral**

O CloudDataOrchestrator v2.0 suporta deploy automatizado na nuvem com:

- **🐳 Containerização**: Docker + ECS Fargate
- **🏗️ Infraestrutura**: Terraform (IaC)
- **🔄 CI/CD**: GitHub Actions
- **⚖️ Load Balancing**: Application Load Balancer
- **📊 Monitoramento**: CloudWatch + Alarms
- **🔐 Segurança**: IAM Roles + Security Groups

## 📋 **Pré-requisitos**

### **Ferramentas Necessárias**
```bash
# Instalar ferramentas
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
```

### **Configuração AWS**
```bash
# Configurar credenciais
aws configure
# ou
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### **Variáveis de Ambiente**
```bash
# Copiar e configurar
cp env.example .env

# Variáveis obrigatórias para deploy
export API_TOKEN="your-secure-api-token"
export GITHUB_TOKEN="your-github-token"  # Para push de imagens
export TF_STATE_BUCKET="clouddataorchestrator-terraform-state"
```

## 🎯 **Ambientes Disponíveis**

### **Staging**
- **Propósito**: Testes e validação
- **Instâncias**: 1 API, 1 Dashboard
- **Recursos**: Mínimos (512 CPU, 1GB RAM)
- **URL**: `http://staging-alb-dns-name.amazonaws.com`

### **Production**
- **Propósito**: Produção
- **Instâncias**: 3 API, 2 Dashboard
- **Recursos**: Otimizados (1024 CPU, 2GB RAM)
- **URL**: `http://production-alb-dns-name.amazonaws.com`

## 🚀 **Deploy Manual**

### **1. Deploy Local para Staging**
```bash
# Deploy completo
python deploy_cloud.py deploy --environment staging

# Verificar saúde
curl http://$(terraform output -raw alb_dns_name)/health
```

### **2. Deploy para Production**
```bash
# Deploy para produção
python deploy_cloud.py deploy --environment production

# Verificar com autenticação
curl -H "Authorization: Bearer your-api-token" \
     http://$(terraform output -raw alb_dns_name)/status
```

### **3. Rollback**
```bash
# Rollback automático para versão anterior
python deploy_cloud.py rollback --environment production
```

### **4. Destruir Infraestrutura**
```bash
# CUIDADO: Remove toda a infraestrutura
python deploy_cloud.py destroy --environment staging
```

## 🔄 **Deploy Automatizado (CI/CD)**

### **GitHub Actions**

O deploy é automatizado via GitHub Actions no arquivo `.github/workflows/deploy.yml`:

#### **Triggers**
- **Push para master**: Deploy para staging
- **Tags v***: Deploy para production
- **Manual**: Via workflow_dispatch

#### **Stages**
1. **🧪 Tests**: Testes unitários + linting
2. **🐳 Build**: Build e push de imagens Docker
3. **🚀 Deploy Staging**: Deploy automático para staging
4. **🎯 Deploy Production**: Deploy para produção (apenas tags)
5. **🔄 Rollback**: Rollback automático em caso de falha

### **Configurar Secrets no GitHub**

```bash
# No GitHub Repository Settings > Secrets:
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
TF_STATE_BUCKET=clouddataorchestrator-terraform-state
API_TOKEN_STAGING=staging-api-token
API_TOKEN_PRODUCTION=production-api-token
```

### **Deploy via Tag**
```bash
# Criar e push de tag para deploy em produção
git tag v2.0.0
git push origin v2.0.0
```

## 🏗️ **Infraestrutura AWS**

### **Componentes Criados**

#### **Networking**
- VPC com subnets públicas e privadas
- Internet Gateway + NAT Gateway
- Security Groups para ALB, ECS e RDS

#### **Compute**
- ECS Cluster com Fargate
- Application Load Balancer
- Target Groups para API e Dashboard

#### **Storage**
- DynamoDB para dados transacionais
- S3 para armazenamento de arquivos
- EFS para volumes persistentes (opcional)

#### **Monitoring**
- CloudWatch Logs
- CloudWatch Alarms
- X-Ray Tracing (opcional)

#### **Security**
- IAM Roles e Policies
- Systems Manager Parameter Store
- Secrets Manager para credenciais

### **Custos Estimados**

#### **Staging (mensal)**
- ECS Fargate: ~$30
- ALB: ~$20
- DynamoDB: ~$5
- S3: ~$5
- **Total**: ~$60/mês

#### **Production (mensal)**
- ECS Fargate: ~$150
- ALB: ~$20
- DynamoDB: ~$20
- S3: ~$10
- CloudWatch: ~$10
- **Total**: ~$210/mês

## 📊 **Monitoramento**

### **Health Checks**
```bash
# Health check básico
curl http://your-alb-dns/health

# Status completo
curl -H "Authorization: Bearer your-token" \
     http://your-alb-dns/status

# Métricas
curl -H "Authorization: Bearer your-token" \
     http://your-alb-dns/metrics
```

### **CloudWatch Dashboards**
- CPU e Memory utilization
- Request count e latency
- Error rates
- Custom metrics da aplicação

### **Alarms**
- CPU > 80%
- Memory > 85%
- Error rate > 5%
- Response time > 2s

## 🔧 **Troubleshooting**

### **Problemas Comuns**

#### **Deploy Falha**
```bash
# Verificar logs do Terraform
cd infrastructure && terraform plan

# Verificar logs do ECS
aws logs tail /ecs/clouddataorchestrator-staging --follow

# Verificar status do serviço
aws ecs describe-services --cluster clouddataorchestrator-cluster-staging
```

#### **Health Check Falha**
```bash
# Verificar targets do ALB
aws elbv2 describe-target-health --target-group-arn your-target-group-arn

# Verificar security groups
aws ec2 describe-security-groups --group-names clouddataorchestrator-*
```

#### **Permissões AWS**
```bash
# Verificar credenciais
aws sts get-caller-identity

# Verificar permissões IAM
aws iam simulate-principal-policy --policy-source-arn your-role-arn
```

### **Rollback Manual**
```bash
# Via Terraform
cd infrastructure
terraform plan -var="image_tag=previous-tag" -out=rollback.plan
terraform apply rollback.plan

# Via ECS Console
# 1. Ir para ECS > Services
# 2. Update Service > Revision anterior
# 3. Deploy
```

## 🔐 **Segurança**

### **Best Practices**
- ✅ Usar IAM Roles (não access keys)
- ✅ Criptografia em trânsito (HTTPS)
- ✅ Criptografia em repouso (S3, DynamoDB)
- ✅ Network isolation (VPC, Security Groups)
- ✅ Secrets no Parameter Store/Secrets Manager
- ✅ Least privilege principle

### **Compliance**
- GDPR: Dados criptografados e auditados
- SOC 2: Logs centralizados e monitoramento
- ISO 27001: Controles de acesso e backup

## 📈 **Escalabilidade**

### **Auto Scaling**
```hcl
# Em infrastructure/main_v2.tf
resource "aws_appautoscaling_target" "api" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}
```

### **Performance Tuning**
- Connection pooling
- Redis para cache distribuído
- CDN para assets estáticos
- Database read replicas

## 🚨 **Disaster Recovery**

### **Backup Strategy**
- DynamoDB: Point-in-time recovery
- S3: Cross-region replication
- ECS: Multi-AZ deployment
- Terraform state: S3 versioning

### **Recovery Procedures**
1. **RTO**: < 30 minutos
2. **RPO**: < 5 minutos
3. **Automated failover**: ALB + Multi-AZ
4. **Manual recovery**: Terraform + Docker images

## 📞 **Suporte**

### **Logs**
```bash
# Logs da aplicação
aws logs tail /ecs/clouddataorchestrator-production --follow

# Logs do ALB
aws logs tail /aws/elasticloadbalancing/app/clouddataorchestrator-alb-production
```

### **Métricas**
- CloudWatch Dashboard
- API `/metrics` endpoint
- Prometheus exporters (opcional)

### **Alertas**
- Email notifications
- Slack integration
- PagerDuty (produção)

---

## 🎉 **Deploy Concluído!**

Após o deploy bem-sucedido, você terá:

- ✅ **API REST** rodando em `http://your-alb-dns/`
- ✅ **Dashboard** em `http://your-alb-dns/dashboard/`
- ✅ **Monitoramento** completo no CloudWatch
- ✅ **Auto-scaling** configurado
- ✅ **Backup** automatizado
- ✅ **CI/CD** pipeline ativo

**🚀 Seu CloudDataOrchestrator v2.0 está rodando na nuvem!**
